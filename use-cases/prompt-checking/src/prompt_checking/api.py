from typing import TYPE_CHECKING

from fastapi import FastAPI
from pydantic import BaseModel

import prompt_checking
from prompt_checking.config import configured_scheduler

if TYPE_CHECKING:
    from resonate.promise import Promise

app = FastAPI()


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    response: str


@app.post("/search")
async def search(request: SearchRequest) -> SearchResponse:
    s = configured_scheduler()
    p: Promise[str] = s.run("search", prompt_checking.use_case, query=request.query)
    return SearchResponse(response=p.result())
