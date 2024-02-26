import inspect
from enum import Enum
from pydantic import BaseModel, RootModel, Field
from typing import List, Dict, Optional

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

class SentimentEnum(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral  = "neutral"

class ExtractionSentiment(BaseModel):
    topic: str = Field(..., description="The topic of interest")
    review_extract: str = Field(..., description="A subpart of the review relevan to the topic")
    sentiment: SentimentEnum = Field(..., description="Sentiment classification of the review_extract")

class MATCHING_OUTPUT(BaseModel):
    results: List[ExtractionSentiment]


MATCHING_PROMPT = [
    {
        "role": "system",
        "content": inspect.cleandoc(
            """
            # Expert Topic Matcher 
            Your output should be in French.
            You are an expert at online review analysis. You are given a review and a list of topics.
            For each of the topic, you will extract the relevant subparts of the review.
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

class SUMMARY_OUTPUT(BaseModel):
    topic: str
    positive_summary: str
    neutral_summary: str
    negative_summary: str

SUMMARY_PROMPT = [
    {
        "role": "system",
        "content": inspect.cleandoc(
            """
            # Expert summary writer
            Your output should be in French.
            You are given a topic and a list positive, negative and neutral extract from review focusing on this topic.
            Make a summary of the comment for each sentiment.
            while also condensing the information into a concise and easy-to-understand format.
            Please ensure that the summary includes relevant details and examples that support the main ideas,
            while avoiding any unnecessary information or repetition.
            The length of the summary should be appropriate for the length and complexity of the original text,
            providing a clear and accurate overview without omitting any important information.
            If one of the list of comment for one sentiment is empty, summerise it as "No information found"
            """
        )
    },
    {
        "role": "user",
        "content": inspect.cleandoc(
            """
            ## Topic
            {{ topic }}

            ## List of review extracts
            {{ list_of_comments }}

            ## Response format
            You must output a JSON.
            """
        )
    }
]
