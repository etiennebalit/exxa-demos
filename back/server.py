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
from tenacity import retry, wait_exponential
import pickle

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from demo_ressources import Extractor, Matcher, Summarizer, ResumeRequest

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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


@retry(wait=wait_exponential(multiplier=1, min=1, max=5))
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


# @app.post("/test")
# async def jaaj(request: ResumeRequest):
#     with open("test_data", "rb") as f:
#         return pickle.load(f)

@app.post("/extract_resume/")
async def extract_resume(request: ResumeRequest):
    gpt3 = "gpt-3.5-turbo"
    gpt4 = "gpt-4-turbo-preview"

    nb_of_rows = 5
    data_file = "data/output_kfc.jsonl"
    frame = pd.read_json(path_or_buf=data_file, lines=True)

    start_time = time.time()

    prompt = format_prompt(Extractor.EXTRACTOR_PROMPT, {"data": request.demande})
    topics = await model_completion(prompt, Extractor.EXTRACTOR_OUTPUT, model=gpt3)

    # Format the review list
    review_topics_list = []
    for index, row in frame.iloc[:nb_of_rows].iterrows() :
        review_topics_list.append({
            "review": row.comment,
            "topics_list": topics.topics
        })


    prompts  = format_prompts(Matcher.MATCHING_PROMPT, review_topics_list)
    matching_results = await parallel_model_completion(prompts, Matcher.MATCHING_OUTPUT, model=gpt3)


    # group the comment by topic then by sentiment
    sentiment_dict = {sentiment.name: [] for sentiment in Matcher.SentimentEnum}
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

    prompts = format_prompts(Summarizer.SUMMARY_PROMPT, grouped_review_list)
    summary_results = await parallel_model_completion(prompts, Summarizer.SUMMARY_OUTPUT, temperature=0.7, model=gpt3)
    
    stop_time = time.time()

    output = dict()
    output["results"] = dict()
    for entry in summary_results:
        output["results"][entry.topic] = {"positive": entry.positive_summary, "neutral": entry.neutral_summary, "negative": entry.negative_summary}
    output["total_time"] = stop_time - start_time
    # 
    # with open("test_data", "wb") as f:
    #     pickle.dump(output, f)


    return JSONResponse(content=jsonable_encoder(output))
