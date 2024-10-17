from dataclasses import dataclass
from resonate.context import Context
from resonate.scheduler import Scheduler
from resonate.storage import LocalPromiseStore
from resonate.retry_policy import never
from resonate.commands import Command
from sqlite3 import Connection
import sqlite3
import click
import time

# Create an SQLite database if it doesn't exist
# Create a connection with that database
conn = sqlite3.connect("benchmark.db", check_same_thread=False)

# Create a Resonate Scheduler with an in memore promise store
resonate = Scheduler(LocalPromiseStore(), processor_threads=1)

### SEQUENTIAL INSERTS
# Define a function that inserts a single row into the database
def _create_user(_: Context, value: int):
    conn.execute("INSERT INTO users (value) VALUES (?)", (value,))
    conn.commit()
    print(f"Value {value} has been inserted to database")

# Define a top level function that uses sequential inserts
def create_user_sequentially(ctx: Context, v: int):
    p = yield ctx.lfi(_create_user, v).with_options(retry_policy=never())
    yield p

### BATCH INSERTS
# Define a data structure for the Resonate SDK to track and create batches of
@dataclass
class InsertValue(Command):
    conn: Connection
    value: int

# Define a function that inserts a batch of rows into the database
# The main difference is that commit() is only called after all the Insert statements are executed
def _batch_handler(_: Context, cmds: list[InsertValue]):
    first_value = cmds[0].value
    last_value = None
    for cmd in cmds:
        conn.execute("INSERT INTO users (value) VALUES (?)", (cmd.value,))
        last_value = cmd.value
    conn.commit()
    print(f"Values from {first_value} to {last_value} have been inserted to database.")

# Definte the top level function that uses batching
def create_user_batching(ctx: Context, v: int):
    p = yield ctx.lfi(InsertValue(conn, v))
    yield p

# Register the top level functions with the Resonate Scheduler
resonate.register(create_user_sequentially, retry_policy=never())
resonate.register(create_user_batching, retry_policy=never())

# Register the batch handler and data structure with the Resonate Scheduler
resonate.register_command_handler(InsertValue, _batch_handler, retry_policy=never())

# Define a CLI to create an interaction point
@click.command()
@click.option("--batch/--no-batch", default=False)
@click.option("--values", type=click.IntRange(0, 100_000))
def cli(batch: bool, values: int):
    # To benchmark, we start from a clean slate each time
    # Drop the users table if it already exists
    conn.execute("DROP TABLE IF EXISTS users")
    # Create a new users table
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, value INTEGER)"
    )
    conn.commit()
    # Create an array to store all the promises
    promises = []
    # Capture the starting time of the operation
    start_time = time.time_ns()
    # If batching, run the batch inserts
    if batch:
        for v in range(values):
            p = resonate.run(f"insert-batch-value-{v}", create_user_batching, v)
            promises.append(p)
    # If not batching, run the sequential inserts
    else:
        for v in range(values):
            p = resonate.run(f"insert-no-batch-value-{v}", create_user_sequentially, v)
            promises.append(p)

    # Yield all promises to ensure they are all complete
    for p in promises:
        p.result()

    # Capture the ending time of the operation
    end_time = time.time_ns()
    print(
        f"Inserting {values:,} values took {(end_time-start_time)/1e9:2f} seconds with batching={batch}"
    )

def main() -> None:
    cli()
