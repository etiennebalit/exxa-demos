from ragatouille import RAGPretrainedModel
from openai import OpenAI
import instructor
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
from tenacity import retry, wait_exponential
from jinja2 import Environment
from copy import deepcopy
import os
import chainlit as cl
from prompts.prompts import QA

def format_prompt(prompt: str, data_model: BaseModel) -> str:
    formatter = Environment()
    prompt = deepcopy(prompt)
    for turn in prompt:
        if turn.get("content") is None:
            raise ValueError("Your prompt content in None")

        turn["content"] = formatter.from_string(turn["content"]).render(**dict(data_model))

    return prompt

@retry(wait=wait_exponential(multiplier=1, min=1, max=5))
def model_completion(client, prompt: str, response_model: BaseModel, temperature: float=0, model:str="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        messages = prompt,
        model=model,
        response_model=response_model,
        temperature=temperature,
    )
    return response


path_to_index = ".ragatouille/colbert/indexes/Amazon/"
RAG = RAGPretrainedModel.from_index(path_to_index)

client = instructor.patch(OpenAI(api_key=os.environ['OPENAI_API_KEY']))

gpt3 = "gpt-3.5-turbo"
gpt4 = "gpt-4-turbo-preview"

@cl.step
async def rag_step(query):

    return retrived_samples

@cl.on_message
async def main(message: cl.Message):
    request = message.content
    results = RAG.search(query=request, k=3)
    retrived_samples = list(map(lambda result: result.get("content"), results))

    qa_input = QA.QAInput(request=request, retrived_samples=retrived_samples)
    prompt = format_prompt(QA.QA_PROMPT, qa_input)
    response = model_completion(client, prompt, QA.QAOutput, model=gpt4)
    
    await cl.Message(content=response.response).send()

if __name__ == "__main__":
    main()
