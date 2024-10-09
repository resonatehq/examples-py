from typing import Generator
import click
from resonate.context import Context
from resonate.scheduler import Scheduler
from resonate.storage import LocalPromiseStore
from resonate.typing import Yieldable
from resonate import retry_policy

resonate = Scheduler(LocalPromiseStore())


def fib(ctx: Context, n: int) -> Generator[Yieldable, int, int]:
    if n <= 1:
        return n

    return (yield ctx.lfc(fib, n - 1).with_options(promise_id=f"fib-{n-1}")) + (
        yield ctx.lfc(fib, n - 2).with_options(promise_id=f"fib-{n-2}")
    )


resonate.register(fib, retry_policy=retry_policy.never())


@click.command()
@click.option("--number", prompt="Number", type=click.IntRange(0))
def cli(number: int):
    value = resonate.run(f"fib-{number}", fib, number).result()
    click.echo(f"F({number}) = {value}")


def main() -> None:
    cli()
