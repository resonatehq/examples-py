from functools import cache
import time
from typing import Generator
from fastapi import FastAPI
from pydantic import BaseModel
from resonate.context import Context
from resonate.options import Options
from resonate.typing import Yieldable
from resonate.scheduler import Scheduler
from resonate.storage import RemotePromiseStore

app = FastAPI()

HOST = "localhost"
PORT = 8000


@cache
def _storage() -> RemotePromiseStore:
    return RemotePromiseStore("http://localhost:8001")


@cache
def _scheduler() -> Scheduler:
    return Scheduler(durable_promise_storage=_storage())


def factorial(ctx: Context, n: int) -> Generator[Yieldable, int, int]:
    print(f"calculating factorial for {n}")
    if n == 0 or n == 1:
        return 1
    time.sleep(3)
    return n * (yield ctx.call(factorial, Options(durable=True), n=n - 1))


class InputData(BaseModel):
    number: int


@app.post("/sync/process-number")
async def process_number_sync(data: InputData):
    s = _scheduler()
    execution_promise = s.run(
        f"factorial-for-{data.number}", Options(durable=True), factorial, n=data.number
    )
    value = execution_promise.result()
    return {"original": data.number, "result": value}


@app.post("/async/process-number")
async def process_number_async(data: InputData):
    s = _scheduler()
    s.run(
        f"factorial-for-{data.number}", Options(durable=True), factorial, n=data.number
    )
    return {"url-for-response": f"http://{HOST}:{PORT}/async/get-number/{data.number}"}


@app.get("/async/get-number/{number}")
async def get_process_number_async(number: int):
    s = _scheduler()
    p = s.run(f"factorial-for-{number}", Options(durable=True), factorial, n=number)
    value = p.result()
    return {"original": number, "result": value}


# Run the application
def main() -> None:
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
