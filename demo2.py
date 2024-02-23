import pandas as pd
import asyncio
import os
from openai import AsyncOpenAI
from jinja2 import Environment
import json
import time
import sys
import instructor
from copy import deepcopy

from demo2_prompts import EXTRACTOR_PROMPT, EXTRACTOR_OUTPUT, MATCHING_PROMPT, MATCHING_OUTPUT, SUMMARY_PROMPT, SUMMARY_OUTPUT, SentimentEnum


client = instructor.patch(AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY']))

def format_prompt(prompt, kwargs):
    formatter = Environment()
    for turn in prompt:
        if turn.get("content") is None:
            raise ValueError("Your prompt content in None")

        turn["content"] = formatter.from_string(turn["content"]).render(**kwargs)

    return prompt


def format_prompts(prompt, kwargs_list):
    return list(map(lambda kwargs: format_prompt(deepcopy(prompt), kwargs), kwargs_list))


async def model_completion(prompt, response_model, temperature=0, model="gpt-3.5-turbo"):
    response = await client.chat.completions.create(
        messages = prompt,
        model=model,
        response_model=response_model,
        temperature=temperature,
    )
    return response


async def parallel_model_completion(prompts, response_model, temperature=0, model="gpt-3.5-turbo"):
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for prompt in prompts:
            tasks.append(tg.create_task(model_completion(prompt, response_model, temperature, model)))

    return list(map(lambda x: x.result(), tasks))

async def main():
    gpt3 = "gpt-3.5-turbo"
    gpt4 = "gpt-4-turbo-preview"

    nb_of_rows = 20
    data_file = "output_kfc.jsonl"
    frame = pd.read_json(path_or_buf=data_file, lines=True)

    topic_request_str = "la propreté, le comportement du personnel et la qualité de la nourriture"

    prompt = format_prompt(EXTRACTOR_PROMPT, {"data": topic_request_str})
    topics = await model_completion(prompt, EXTRACTOR_OUTPUT, model=gpt3)

    # Format the review list
    review_topics_list = []
    for index, row in frame.iloc[:nb_of_rows].iterrows() :
        review_topics_list.append({
            "review": row.comment,
            "topics_list": topics.topics
        })


    prompts  = format_prompts(MATCHING_PROMPT, review_topics_list)
    matching_results = await parallel_model_completion(prompts, MATCHING_OUTPUT, model=gpt3)

    sentiment_dict = {sentiment.name: [] for sentiment in SentimentEnum}
    extracted_topics_dict = {topic: deepcopy(sentiment_dict) for topic in topics.topics}
    for result in matching_results:
        for topic_sentiment in result.results:
            extracted_topics_dict[topic_sentiment.topic][topic_sentiment.sentiment].append(topic_sentiment.review_extract)

    grouped_review_list = []
    for k, v in extracted_topics_dict.items():       
        grouped_review_list.append({
            "topic": k,
            "list_of_comments": v
        })

    prompts = format_prompts(SUMMARY_PROMPT, grouped_review_list)
    summary_results = await parallel_model_completion(prompts, SUMMARY_OUTPUT, temperature=0.7, model=gpt3)
    
    for element in summary_results :
        print(element, end="\n\n")

asyncio.run(main())

