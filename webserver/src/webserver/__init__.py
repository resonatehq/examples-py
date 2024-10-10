import time
from typing import Generator
from fastapi import FastAPI
from pydantic import BaseModel
from resonate.context import Context
from resonate.promise import Promise
from resonate.typing import Yieldable
from resonate.scheduler import Scheduler
from resonate.storage import LocalPromiseStore

app = FastAPI()

HOST = "localhost"
PORT = 8000


resonate = Scheduler(durable_promise_storage=LocalPromiseStore())


class InputData(BaseModel):
    number: int


def factorial(ctx: Context, n: int) -> Generator[Yieldable, int, int]:
    time.sleep(0.5)
    if n == 0 or n == 1:
        return 1

    return n * (
        yield ctx.lfc(
            factorial,
            n=n - 1,
        ).with_options(
            promise_id=f"factorial-for-{n-1}",
            durable=True,
        )
    )


resonate.register(factorial)


@app.get("/async/get-number/{number}")
async def get_process_number_async(number: int):
    p: Promise[int] = resonate.run(f"factorial-for-{number}", factorial, n=number)
    if not p.done():
        return {"state": "Working on it", "msg": "Come back in 5 min"}

    value = p.result()
    return {"original": number, "result": value}


# Run the application
def main() -> None:
    import uvicorn

    uvicorn.run(app)
