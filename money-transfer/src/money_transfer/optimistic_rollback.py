from __future__ import annotations

from sqlite3 import Connection
from typing import TYPE_CHECKING, Any

from resonate.typing import Yieldable

if TYPE_CHECKING:
    from collections.abc import Generator

    from resonate.context import Context


class NotEnoughFundsError(Exception):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"Account {account_id} does not have enough money")


def current_balance(ctx: Context, account_id: int) -> tuple[int, int]:  # noqa: ARG001
    conn: Connection = ctx.deps.get("conn")
    balance, version = conn.execute(
        "SELECT balance, version FROM accounts WHERE account_id = ?", (account_id,)
    ).fetchone()
    conn.commit()
    return balance, version


def rollback(ctx: Context, transfer_id: int) -> None:
    conn: Connection = ctx.deps.get("conn")
    transfer: list[tuple[int, int]] = conn.execute(
        "SELECT account_id, amount FROM transfers WHERE transfer_id = ?", (transfer_id,)
    ).fetchall()
    for account_id, amount in transfer:
        conn.execute(
            """
            UPDATE accounts
            SET
                balance = balance - ?,
                version = version + 1
            WHERE account_id = ?
            """,
            (amount, account_id),
        )
    conn.execute("DELETE FROM transfers WHERE transfer_id = ?", (transfer_id,))
    conn.commit()


def update_balance_ensure_version(
    ctx: Context, transfer_id: int, account_id: int, amount: int, version: int
) -> None:
    conn: Connection = ctx.deps.get("conn")
    conn.execute(
        "INSERT INTO transfer (transfer_id, account_id, amount) VALUES (?, ?, ?)",
        (transfer_id, account_id, amount),
    )
    cur = conn.execute(
        """
            UPDATE accounts
            SET
                balance = balance + ?,
                version = version + 1
            WHERE account_id = ? and version = ?
            """,
        (amount, account_id, version),
    )
    conn.commit()
    if cur.rowcount == 0:
        raise RuntimeError("Someone else got here first! :(")
    ctx.assert_statement(cur.rowcount == 1, msg="More that one row was affected")


def update_balance(
    ctx: Context, transfer_id: int, account_id: int, amount: int
) -> None:
    conn: Connection = ctx.deps.get("conn")

    conn.execute(
        "INSERT INTO transfer (transfer_id, account_id, amount) VALUES (?, ?, ?)",
        (transfer_id, account_id, amount),
    )

    cur = conn.execute(
        """
        UPDATE accounts
        SET
            balance = balance + ?,
            version = version + 1
        WHERE account_id = ?
        """,
        (amount, account_id),
    )
    conn.commit()
    ctx.assert_statement(cur.rowcount == 1, msg="More that one row was affected")


def transaction(
    ctx: Context, transfer_id: int, source: int, target: int, amount: int
) -> Generator[Yieldable, Any, None]:
    yield ctx.call(rollback, transfer_id=transfer_id)

    source_balance_and_version: tuple[int, int] = yield ctx.call(
        current_balance, account_id=source
    )
    source_balance, version = source_balance_and_version

    if source_balance - amount < 0:
        raise NotEnoughFundsError(account_id=source)

    yield ctx.call(
        update_balance_ensure_version,
        transfer_id=transfer_id,
        account_id=source,
        amount=amount * -1,
        version=version,
    )

    yield ctx.call(
        update_balance, transfer_id=transfer_id, account_id=target, amount=amount
    )
