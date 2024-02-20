import time
import sys
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver

from scraperenv import URL, DriverLocation, output_file, nb_scroll, hide_browser

def setup():
    print("setup...")
    driver.get(URL)
    time.sleep(2)
    driver.find_element_by_xpath("//button[contains(., 'Tout refuser')]").click()
    time.sleep(5)
    button_list = driver.find_elements_by_class_name("M77dve")
    button_list[1].click()
    time.sleep(3)

def scrolling():
    scrollable_div = driver.find_elements_by_css_selector(".lXJj5c.Hk4XGb")[1]
    scrollable_div.click()
    time.sleep(1)
    scrolling = driver.execute_script('document.getElementsByClassName("dS8AEf")[0].scrollTop = document.getElementsByClassName("dS8AEf")[0].scrollHeight', scrollable_div)
    time.sleep(1)

def get_data():
    more_elemets = driver.find_elements_by_class_name('w8nwRe kyuRq')
    for list_more_element in more_elemets:
        list_more_element.click()
    
    elements = driver.find_elements_by_class_name(
        'jftiEf')
    parsed_data = []
    for data in elements:
        comment_div = data.find_element_by_class_name("MyEned")
        try:
            comment_div.find_element_by_xpath("//button[contains(., 'Plus')]").click()
        except:
            pass
        comment = comment_div.find_element_by_class_name("wiI7pd").text
        comment = comment.replace("\r", " ").replace("\n", "").replace("\"", "")

        score = data.find_element_by_class_name("kvMYJc").get_attribute("aria-label")
        
        parsed_data.append(f'{{"comment": "{comment}", "score": {score[0]}}}\n')

    return parsed_data

if __name__ == "__main__":

    options = webdriver.ChromeOptions()
    if hide_browser:
        options.add_argument("--headless")  # show browser or not
    options.add_argument("--lang=en-US")
    options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    driver = webdriver.Chrome(DriverLocation, options=options)

    setup()

    total_data = []
    for i in tqdm(range(nb_scroll)):
        scrolling()
        data = get_data()
        total_data += data
    driver.close()

    with open(output_file, "w") as f:
        for line in total_data:
            f.write(line)

    print('Done!')
