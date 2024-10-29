from collections.abc import Generator
from dataclasses import dataclass
from sqlite3 import Connection
from typing import Any

from resonate.context import Command, Context
from resonate.typing import Yieldable


@dataclass
class Insert(Command):
    conn: Connection
    value: int


def insert_handler(cmds: list[Insert]) -> None:
    conn = cmds[0].conn
    for cmd in cmds:
        conn.execute("INSERT INTO benchmark (value) VALUES (?)", (cmd.value,))
    conn.commit()


def insert_values_using_batch(
    ctx: Context, value: int
) -> Generator[Yieldable, Any, None]:
    yield ctx.call(Insert(conn=ctx.deps.get("conn"), value=value))
    return


def _insert(ctx: Context, value: int) -> None:
    conn: Connection = ctx.deps.get("conn")
    conn.execute("INSERT INTO benchmark (value) VALUES (?)", (value,))
    conn.commit()


def insert_value_by_value(ctx: Context, value: int) -> Generator[Yieldable, Any, None]:
    yield ctx.call(_insert, value)
