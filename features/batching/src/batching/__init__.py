from dataclasses import dataclass
from resonate.context import Context
from sqlite3 import Connection
from resonate.scheduler import Scheduler
from resonate.storage import LocalPromiseStore
import click
from resonate.retry_policy import never
from resonate.commands import Command

import time


conn = Connection("benchmark.db", check_same_thread=False)
resonate = Scheduler(LocalPromiseStore(), processor_threads=1)
# resonate = Scheduler(RemotePromiseStore("http://localhost:8001"), processor_threads=1)


def notify(ctx: Context, value):
    print(f"Value {value} has been inserted to database")


def _create_user(ctx: Context, value: int):
    conn.execute("INSERT INTO benchmark (value) VALUES (?)", (value,))
    conn.commit()


@dataclass
class InsertValue(Command):
    value: int


def _batch_handler(ctx: Context, cmds: list[InsertValue]):
    for cmd in cmds:
        conn.execute("INSERT INTO benchmark (value) VALUES (?)", (cmd.value,))
    conn.commit()


def create_user_batching(ctx: Context, v: int):
    p = yield ctx.lfi(InsertValue(v)).with_options(durable=False)
    yield p
    yield ctx.lfc(notify, v).with_options(durable=False)


def create_user_sequentially(ctx: Context, v: int):
    p = yield ctx.lfi(_create_user, v).with_options(retry_policy=never(), durable=False)
    yield p
    yield ctx.lfc(notify, v).with_options(durable=False)


# register top level function.
resonate.register(create_user_sequentially, retry_policy=never())
resonate.register(create_user_batching, retry_policy=never())

# register batch handler
resonate.register_command_handler(InsertValue, _batch_handler, retry_policy=never())


@click.command()
@click.option("--batch/--no-batch", default=False)
@click.option("--values", type=click.IntRange(0, 100_000))
def cli(batch: bool, values: int):
    # conn.execute("DROP TABLE IF EXISTS benchmark")
    conn.execute("DROP TABLE IF EXISTS benchmark")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS benchmark (id INTEGER PRIMARY KEY, value INTEGER)"
    )
    conn.commit()
    promises = []

    start_time = time.time_ns()
    if batch:
        for v in range(values):
            p = resonate.run(f"insert-value-{v}", create_user_batching, v)
            promises.append(p)
    else:
        for v in range(values):
            p = resonate.run(f"insert-value-{v}", create_user_sequentially, v)
            promises.append(p)

    for p in promises:
        p.result()

    end_time = time.time_ns()
    print(
        f"Inserting {values:,} values took {(end_time-start_time)/1e9:2f} seconds with batching={batch}"
    )


def main() -> None:
    cli()
