import resonate
from duckduckgo_search import DDGS
from fastapi import FastAPI
from pydantic import BaseModel

import prompt_checking

app = FastAPI()


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    response: str


@app.post("/search")
async def search(request: SearchRequest) -> SearchResponse:
    s = resonate.testing.dst(seeds=[1])[0]
    s.deps.set("model", "llama3.1")
    s.deps.set("duckduckgo_client", DDGS())
    s.add(prompt_checking.use_case, query=request.query)
    result = s.run()[0].result()
    return SearchResponse(response=result)
