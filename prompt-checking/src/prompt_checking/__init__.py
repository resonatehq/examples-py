import json
from collections.abc import Generator, Mapping  # noqa: F401
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

import ollama
from resonate.context import Context
from resonate.typing import Yieldable
from typing_extensions import assert_never

from . import testing

if TYPE_CHECKING:
    from duckduckgo_search import DDGS

__all__ = ["testing"]
Model: TypeAlias = Literal["llama3.1"]
RouteOutput: TypeAlias = Literal["web_search", "generate"]


def query_duckduckgo(
    ctx: Context,
    query: str,
    max_results: int,
) -> list[dict[str, str]]:
    ctx.assert_statement(max_results > 0, "Max results must be postive.")
    c: DDGS = ctx.deps.get("duckduckgo_client")
    return c.text(keywords=query, max_results=max_results)


def format_results(results: list[dict[str, str]]) -> str:
    return "\n".join(r["body"] for r in results)


def reply_query_based_on_info(
    ctx: Context,
    info: str | None,
    query: str,
) -> str:
    model: Model = ctx.deps.get("model")
    assert ctx.seed is not None
    if info is None:
        info = ""
    resp = ollama.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """You are an AI assistant for Research Question Tasks, that synthesizes web search results.
    Strictly use the following pieces of web search context to answer the question. If you don't know the answer, just say that you don't know.
    keep the answer concise, but provide all of the details you can in the form of a research report.
    Only make direct references to material if provided in the context.""",  # noqa: E501
            },
            {
                "role": "user",
                "content": f"""Question: {query}
    Web Search Context {info}
    Answer:""",
            },
        ],
        options=ollama.Options(seed=ctx.seed),
    )
    return resp["message"]["content"]


def check_if_websearch_is_required(ctx: Context, query: str) -> bool:
    model: Model = ctx.deps.get("model")
    assert ctx.seed is not None
    resp = ollama.chat(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """You are an expert at routing a user question to either the generation stage or web search.
    Use the web search for questions that require more context for a better answer, or recent events.
    Otherwise, you can skip and go straight to the generation phase to respond.
    You do not need to be stringent with the keywords in the question related to these topics.
    Give a binary choice 'web_search' or 'generate' based on the question.
    Return the JSON with a single key 'choice' with no premable or explanation. """,  # noqa: E501
            },
            {"role": "user", "content": f"Question to route: {query} "},
        ],
        options=ollama.Options(seed=ctx.seed),
    )
    choice: RouteOutput = json.loads(resp["message"]["content"])["choice"]
    need_websearch: bool
    if choice == "generate":
        need_websearch = False
    elif choice == "web_search":
        need_websearch = True
    else:
        assert_never(choice)

    return need_websearch


def use_case(ctx: Context, query: str) -> Generator[Yieldable, Any, str | None]:
    websearch_info: str | None = None
    if (yield ctx.call(check_if_websearch_is_required, query=query)):
        results: list[dict[str, str]] = yield ctx.call(
            query_duckduckgo, query=query, max_results=25
        )
        websearch_info = format_results(results)

    return (
        yield ctx.call(
            reply_query_based_on_info,
            query=query,
            info=websearch_info,
        )
    )
