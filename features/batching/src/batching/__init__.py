# @@@SNIPSTART examples-py-features-batching-init
from dataclasses import dataclass
from resonate.context import Context
from resonate.scheduler import Scheduler
from resonate.storage import LocalPromiseStore
from resonate.retry_policy import never
from resonate.commands import Command
import sqlite3

# Create an SQLite database if it doesn't exist
# Create a connection with that database
conn = sqlite3.connect("your_database.db", check_same_thread=False)

# Create a Resonate Scheduler with an in memory promise store
resonate = Scheduler(LocalPromiseStore(), processor_threads=1)

# Define a data structure for the Resonate SDK to track and create batches of
@dataclass
class InsertUser(Command):
    id: int

# Define a function that inserts a batch of rows into the database
# The main difference is that commit() is only called after all the Insert statements are executed
def _batch_handler(_: Context, users: list[InsertUser]):
    # error handling ommitted for this example
    for user in users:
        conn.execute("INSERT INTO users (value) VALUES (?)", (user.id,))
    conn.commit()
    print(f"{len(users)} users have been inserted to database.")

# Definte the top level function that uses batching
def create_user_batching(ctx: Context, u: int):
    p = yield ctx.lfi(InsertUser(u))
    yield p

# Register the top level functions with the Resonate Scheduler
resonate.register(create_user_batching, retry_policy=never())

# Register the batch handler and data structure with the Resonate Scheduler
resonate.register_command_handler(InsertUser, _batch_handler, retry_policy=never())

def main() -> None:
    # Drop the users table if it already exists
    conn.execute("DROP TABLE IF EXISTS users")
    # Create a new users table
    conn.execute(
        "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, value INTEGER)"
    )
    # Create an array to hold the promises
    promises = []

    for u in range(10000):
        p = resonate.run(f"insert-value-{u}", create_user_batching, u)
        promises.append(p)

    for p in promises:
        p.result()
# @@@SNIPEND