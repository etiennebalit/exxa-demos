import pandas as pd
import asyncio
import os
from openai import AsyncOpenAI
import time
import sys
import instructor
import pickle


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from demo_ressources import Extractor, Matcher, Summarizer, InputOutput
from demo_functions import format_prompt, format_prompts, model_completion, parallel_model_completion

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

client = instructor.patch(AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY']))


@app.post("/extract_resume/")
async def extract_resume(request: InputOutput.ResumeRequest) :
    gpt3 = "gpt-3.5-turbo"
    gpt4 = "gpt-4-turbo-preview"

    nb_of_rows = 10
    data_file = "data/kfc.jsonl"
    frame = pd.read_json(path_or_buf=data_file, lines=True)

    prompt = format_prompt(Extractor.EXTRACTOR_PROMPT, Extractor.EXTRACTOR_INPUT(data=request.demande))
    topics = await model_completion(client, prompt, Extractor.EXTRACTOR_OUTPUT, model=gpt3)

    # Format the review list
    review_topics_list: List[Matcher.MATCHING_INPUT] = []
    for index, row in frame.iloc[:nb_of_rows].iterrows() :
        review_topics_list.append(Matcher.MATCHING_INPUT(
            review=row.comment,
            topics_list=topics.topics
        ))

    prompts = format_prompts(Matcher.MATCHING_PROMPT, review_topics_list)
    matching_results = await parallel_model_completion(client, prompts, Matcher.MATCHING_OUTPUT, model=gpt3)


    sentiment_topic_list: List[Summarizer.SUMMARY_INPUT] = []
    for sentiment in Matcher.SentimentEnum:
        for topic in topics.topics:
            bullet_list = []
            for results in matching_results:
                for result in results.results:
                    if result.topic == topic :
                        bullet_list.append(result.review_extract)
            sentiment_topic_list.append(Summarizer.SUMMARY_INPUT(
                    topic=topic,
                    sentiment=sentiment,
                    bullet_points=bullet_list
                )
            )

    prompts = format_prompts(Summarizer.SUMMARY_PROMPT, sentiment_topic_list)
    summary_results = await parallel_model_completion(client, prompts, Summarizer.SUMMARY_OUTPUT, temperature=0.7, model=gpt3)
                
    
    output: InputOutput.Output = dict()
    output["results"] = []
    for topic in topics.topics:
        formated_topic = InputOutput.OutputTopic(topic=topic)
        for result in summary_results:
            if topic == result.topic:
                sentiment_field = getattr(formated_topic, result.sentiment)
                sentiment_field += result.bullet_points

        output["results"].append(formated_topic)

    print(output)

    return JSONResponse(content=jsonable_encoder(output))
