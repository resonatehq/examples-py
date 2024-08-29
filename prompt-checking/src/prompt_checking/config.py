from functools import cache

from duckduckgo_search import DDGS
from resonate.scheduler import Scheduler


@cache
def configured_scheduler() -> Scheduler:
    s = Scheduler()
    s._deps.set("model", "llama3.1")
    s._deps.set("duckduckgo_client", DDGS())
    return s
