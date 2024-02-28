import inspect
from enum import Enum
from pydantic import BaseModel, RootModel, Field
from typing import List, Dict, Optional



class Extractor:

    class EXTRACTOR_OUTPUT(BaseModel):
        topics: List[str]

    EXTRACTOR_PROMPT = [
        {
            "role": "system",
            "content": inspect.cleandoc(
                """
                # Expert Entity Extractor
                Your output should be in French.
                You are an expert entity extractor focusing on business relevant concept.
                You use inference or deduction whenever necessary to
                supply missing or omitted data. Examine the provided data, text, or
                information and generate a list of any entities or objects relevant to business.
                Any other entities or concepts that are not relevant to a business should not be included.
                """
                )
        },
        {
            "role": "user",
            "content": inspect.cleandoc(
                """
                ## Data to extract
                {{ data }}
                
                ## Response format
                You must output a JSON.
                When providing integers, do not write out any decimals at all
                Use deduction where appropriate e.g. "3 dollars fifty cents" is a single
                value [3.5] not two values [3, 50] unless the user specifically asks for
                each part.
                """
            )
        }
    ]

class Matcher:

    class SentimentEnum(str, Enum):
        positif = "positif"
        negatif = "negatif"
        neutre  = "neutre"

    class ExtractionSentiment(BaseModel):
        topic: str = Field(..., description="The topic of interest")
        review_extract: str = Field(..., description="A subpart of the review relevan to the topic")
        sentiment: 'Matcher.SentimentEnum' = Field(..., description="Sentiment classification of the review_extract")

    class MATCHING_OUTPUT(BaseModel):
        results: List['Matcher.ExtractionSentiment']


    MATCHING_PROMPT = [
        {
            "role": "system",
            "content": inspect.cleandoc(
                """
                # Expert Bullet Points extractor 
                Your output should be in French.
                You are an expert at online review analysis. You are given a review and a list of topics.
                For each of the topic, you will extract the relevant subparts of the review as bullet points.
                If there is more than one subpart in the review that is relevant to the current topic, just write them down one after the other.
                If required, use very minimal editing to make the extracted subparts grammatically correct.
                """
            )
        },
        {
            "role": "user",
            "content": inspect.cleandoc(
                """
                ## Review to analyse
                {{ review }}
                
                ## List of topics to extract
                {{ topics_list }}

                ## Response format
                You must output a JSON.
                """
            )
        }
    ]


class Summarizer:

    class SUMMARY_OUTPUT(BaseModel):
        topic: str
        sentiment: str
        bullet_points: List[str]

    SUMMARY_PROMPT = [
        {
            "role": "system",
            "content": inspect.cleandoc(
                """
                # Expert summary writer
                Your output should be in French.
                You are given a topic, a sentiment and a list of bullet points. Those bullet points comes
                from differents review. Your goal is to output a list of bullet point.
                Some of the bullet points, even if phrased differently, will have the same meaning.
                Those bullet points shall be summarized as one single bullet point.
                If the list of bullet point is empty, write "No information found"
                """
            )
        },
        {
            "role": "user",
            "content": inspect.cleandoc(
                """
                ## Topic
                {{ topic }}

                ## Sentiment
                {{ sentiment }}

                ## List of review extracts
                {{ bullet_points }}

                ## Response format
                You must output a JSON.
                """
            )
        }
    ]

class InputOutput:

    class ResumeRequest(BaseModel):
        demande: str
    
    class OutputTopic(BaseModel):
        topic: str
        positif: List[str] = []
        neutre: List[str] = []
        negatif: List[str] = []

    class Output(BaseModel):
        result: List['InputOutput.OutputTopic']

