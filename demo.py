import pandas as pd
import asyncio
import os
from openai import AsyncOpenAI
from jinja2 import Environment
import json
import time

from demo_prompts import EXTRACT_PROMPT, MATCHING_PROMPT, SUMMARY_PROMPT 


client = AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])

async def model_completion(request_kwargs, prompt_template, model="gpt-3.5-turbo", debug=False):
    formatter = Environment()
    prompt = formatter.from_string(prompt_template).render(**request_kwargs)
    
    if debug:
        print(prompt)

    response = await client.chat.completions.create(
        messages = [{"role": "user", "content": prompt}],
        model=model,
        response_format={"type": "json_object"},
        temperature=0,
    )
    return response.choices[0].message.content

async def main():

    gpt3 = "gpt-3.5-turbo"
    gpt4 = "gpt-4-turbo-preview"

    show_time = False

    nb_of_rows = 50
    data_file = "output_kfc.jsonl"
    frame = pd.read_json(path_or_buf=data_file, lines=True)

    demande = input("Que voulez vous connaître dans cet établissement ?\n>>> ")
    print()
    
    start_time = time.time()

    topic_json = await model_completion({"data": demande}, EXTRACT_PROMPT, gpt4)
    topic_dict = json.loads(topic_json)
    
    print("Lancement de la recherche sémantique sur les sujets:")
    for index, topic in enumerate(topic_dict.get("entities")):
        print(f"\t{index+1}. {topic}")

    kwargs_list = []
    for index, row in frame.iloc[:nb_of_rows].iterrows() :
        kwargs_list.append({
            "review": row.comment,
            "topic_list": topic_dict.get("entities")
        })

    extraction_tasks = []
    async with asyncio.TaskGroup() as tg:
        for topic_matching_kwargs in kwargs_list:
            extraction_tasks.append(tg.create_task(model_completion(topic_matching_kwargs, MATCHING_PROMPT, gpt3)))

    extraction_results = list(map(lambda x: json.loads(x.result()), extraction_tasks))


    grouping_dict = {}
    for topic in topic_dict.get("entities"):
        grouping_dict[topic] = []

    for result in extraction_results:
        for topic in topic_dict.get("entities"):
            if result.get(topic) is not None:
                grouping_dict.get(topic).append(result.get(topic))

    summary_tasks = []
    async with asyncio.TaskGroup() as tg:
        for topic, comments in grouping_dict.items():
            summary_kwargs = {
                "topic": topic,
                "list_of_comments": comments
            }
            summary_tasks.append(tg.create_task(model_completion(summary_kwargs, SUMMARY_PROMPT, gpt3)))

    summary_results = list(map(lambda x: json.loads(x.result()), summary_tasks))

    print("\n\nResultats:")
    for index, summarized_topic_dict in enumerate(summary_results):
        topic = next(iter(summarized_topic_dict))
        summary = summarized_topic_dict[topic]
        print(f"{index + 1}. {topic}:\n{summary}\n\n")

    stop_time = time.time()
    
    if show_time:
        print(f"Total llm pipeline processing time: {stop_time - start_time:.1f}s") 

asyncio.run(main())

