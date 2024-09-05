from functools import cache
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
    if n == 0 or n == 1:
        return 1
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
async def get_number_async(number: int):
    storage = _storage()
    record = storage.get(promise_id=f"factorial-for-{number}")
    if record.is_pending():
        return {"state": record.state}
    elif record.is_resolved():
        return {"state": record.state, "original": number, "result": record.value.data}
    else:
        assert record.is_rejected()
        return {"state": record.state, "error": record.value.data}


# Run the application
def main() -> None:
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
