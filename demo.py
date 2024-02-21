import asyncio
import os
from openai import AsyncOpenAI
from jinja2 import Environment

from demo_prompts import EXTRACT_PROMPT 


client = AsyncOpenAI(api_key=os.environ['OPENAI_API_KEY'])

async def interests_extraction(request_kwargs):
    formatter = Environment()
    prompt = formatter.from_string(EXTRACT_PROMPT).render(**request_kwargs)

    response = await client.chat.completions.create(
        messages = [
            { "role": "user", "content": prompt}
        ],
        model="gpt-3.5-turbo",
        # model="gpt-4-turbo-preview",
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content

async def main():
    demande = input("Que voulez vous connaître dans cet établissement ?\n>>> ")

    request_kwargs = {
        "data": demande,
    }

    output = await interests_extraction(request_kwargs)
    print(output)




asyncio.run(main())

