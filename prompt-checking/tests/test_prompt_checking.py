import json
from typing import Literal

import ollama
import prompt_checking
import pytest
import resonate
from duckduckgo_search import DDGS
from resonate.dst.scheduler import DSTScheduler
from typing_extensions import assert_never


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        seeds=[1],
        mocks={
            prompt_checking.query_duckduckgo: prompt_checking.testing.mocks.query_duckduckgo,  # noqa: E501
        },
    ),
)
def test_deterministic_prompt_generation(scheduler: DSTScheduler) -> None:
    scheduler.deps.set("model", "llama3.1")
    scheduler.deps.set("duckduckgo_client", DDGS())
    scheduler.add(prompt_checking.use_case, query="home depot news")
    assert (
        scheduler.run()[0].result()
        == "Here's a summary of the latest news from The Home Depot:\n\n**Recent Announcements**\n\n* The Home Depot is spending $18.3 billion to buy SRS Distribution, a huge building-projects supplier.\n* The company will release its Q2 2024 earnings on Aug 13, 2024, with expected revenue of $43,375.69 million and earnings of $4.48 per share.\n\n**Previous Announcements**\n\n* The Home Depot reported sales and earnings decline for the first quarter of fiscal 2024.\n* The company announced a pending acquisition of SRS Distribution Inc. and a conference call to discuss its performance.\n* In March 2024, Home Depot will buy SRS Distribution, a materials provider for professionals, in a deal valued at approximately $18.25 billion including debt.\n\n**Recent Earnings Reports**\n\n* For Q1 2024, Home Depot's revenues fell 2% year-over-year (y-o-y) to $36.4 billion.\n* Comparable sales decreased 2.8% during the quarter.\n* In February 2023, Home Depot reported fourth quarter and fiscal 2022 results, with sales for the fourth quarter of fiscal 2022 were $35.8 billion.\n\n**Other News**\n\n* Henry County police are looking for a man who exposed himself to a woman in a Home Depot store.\n* A security guard separates a group of migrants after a tow truck driver attempted to tow a migrant's vehicle while they tried to get work in the Home Depot parking lot.\n* The Home Depot has been accused of discriminatory practices, including refusing to hire African American workers.\n\nThese are just some of the recent news and announcements from The Home Depot."  # noqa: E501
    )


def _assert_is_a_reasonable_response(
    input_prompt: str,
    response: str,
    model: prompt_checking.Model,
    *,
    negation: bool = False,
) -> None:
    resp = ollama.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """
                    You are evaluting a response generated with AI. Your goal is to decide whether or not a response is resonable given an input prompt.
                    If the response seems reasonable return 'reasonable' if not return 'not_reasonable'.
                    Return the JSON with a single key 'choice' with no premable or explanation""",  # noqa: E501
            },
            {
                "role": "user",
                "content": f"Input prompt: {input_prompt}\nResponse:{response}",
            },
        ],
    )
    choice: Literal["reasonable", "not_reasonable"] = json.loads(
        resp["message"]["content"]
    )["choice"]
    if choice == "not_reasonable":
        assert (
            negation
        ), f"{response} is not a reasonable response for input prompt {input_prompt}"
    elif choice == "reasonable":
        return
    else:
        assert_never(choice)


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        seeds=[range(2)],
        mocks={
            prompt_checking.query_duckduckgo: prompt_checking.testing.mocks.query_duckduckgo,  # noqa: E501
        },
    ),
)
def test_not_reasonable_responses(scheduler: DSTScheduler) -> None:
    scheduler.deps.set("model", "llama3.1")
    scheduler.deps.set("duckduckgo_client", DDGS())
    input_prompt = "teleperformance news"
    scheduler.add(prompt_checking.use_case, query=input_prompt)
    response: str = scheduler.run()[0].result()
    _assert_is_a_reasonable_response(
        input_prompt=input_prompt,
        response=response,
        model=scheduler.deps.get("model"),
        negation=True,
    )


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        seeds=[range(2)],
        mocks={
            prompt_checking.query_duckduckgo: prompt_checking.testing.mocks.query_duckduckgo,  # noqa: E501
        },
    ),
)
def test_reasonable_responses(scheduler: DSTScheduler) -> None:
    scheduler.deps.set("model", "llama3.1")
    scheduler.deps.set("duckduckgo_client", DDGS())
    input_prompt = "home depot news"
    scheduler.add(prompt_checking.use_case, query=input_prompt)
    response: str = scheduler.run()[0].result()
    _assert_is_a_reasonable_response(
        input_prompt=input_prompt,
        response=response,
        model=scheduler.deps.get("model"),
    )
