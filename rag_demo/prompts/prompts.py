
import inspect
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class QA:
    class QAInput(BaseModel):
        request: str
        retrived_samples: List[str]

    class QAOutput(BaseModel):
        are_samples_relevant: bool
        response: str


    QA_PROMPT = [
        {
            "role": "system",
            "content": inspect.cleandoc(
                """
                # Expert en Question réponse sur base de documents
                Tu as pour mission de répondre à la question demandé dans la limite du savoir contenu dans les documents qui te seront fournis.
                Si les documents ne permettent pas de répondre à la quesiton, excuse toi dans la réponse et mettre le paramettre "are_samples_relevant" à False.
                """
            )
        },
        {
            "role": "user",
            "content": inspect.cleandoc(
                """
                ## Documents fournis:
                {% for sample in retrived_samples %}
                {{ sample + "\n\n" }}
                {% endfor %}

                ## Question:
                {{ request }}
                """
            )
        }
    ]

