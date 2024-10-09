from fastapi import FastAPI
import uvicorn
from resonate.scheduler import Scheduler
from resonate.context import Context
from resonate.storage import LocalPromiseStore

app = FastAPI()
resonate = Scheduler(LocalPromiseStore())


def baz(ctx: Context):
    return 1


def bar(ctx: Context):
    v = yield ctx.lfc(baz)
    return v + 1


def foo(ctx: Context):
    v = yield ctx.lfc(bar)
    return v + 1


resonate.register(foo)


@app.get("/")
def read_root():
    v = resonate.run("foo", foo).result()
    return {"value": v}


def main() -> None:
    uvicorn.run(app)
