
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
from tenacity import retry, wait_exponential
from jinja2 import Environment
from copy import deepcopy

def format_prompt(prompt: str, data_model: BaseModel) -> str:
    formatter = Environment()
    prompt = deepcopy(prompt)
    for turn in prompt:
        if turn.get("content") is None:
            raise ValueError("Your prompt content in None")

        turn["content"] = formatter.from_string(turn["content"]).render(**dict(data_model))

    return prompt


def format_prompts(prompt: str, kwargs_list: Dict[str, str]) -> List[str]:
    return list(map(lambda kwargs: format_prompt(prompt, kwargs), kwargs_list))


@retry(wait=wait_exponential(multiplier=1, min=1, max=5))
async def model_completion(client, prompt: str, response_model: BaseModel, temperature: float=0, model:str="gpt-3.5-turbo"):
    response = await client.chat.completions.create(
        messages = prompt,
        model=model,
        response_model=response_model,
        temperature=temperature,
    )
    return response


async def parallel_model_completion(client, prompts: List[str], response_model: BaseModel, temperature: float=0, model: str="gpt-3.5-turbo"):
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for prompt in prompts:
            tasks.append(tg.create_task(model_completion(client, prompt, response_model, temperature, model)))

    return list(map(lambda x: x.result(), tasks))
