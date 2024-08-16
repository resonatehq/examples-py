from duckduckgo_search import DDGS
from fastapi import FastAPI
from pydantic import BaseModel
from resonate.scheduler import Scheduler

import prompt_checking

app = FastAPI()


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    response: str


@app.post("/search")
async def search(request: SearchRequest) -> SearchResponse:
    s = Scheduler()
    s._deps.set("model", "llama3.1")
    s._deps.set("duckduckgo_client", DDGS())
    p = s.run("search", prompt_checking.use_case, query=request.query)
    return SearchResponse(response=p.result())
