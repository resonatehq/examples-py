from __future__ import annotations

from typing import TYPE_CHECKING, Any

from money_transfer import errors

if TYPE_CHECKING:
    from collections.abc import Generator
    from sqlite3 import Connection

    from resonate.context import Context
    from resonate.typing import Yieldable


def current_balance(ctx: Context, account_id: int) -> tuple[int, int]:
    conn: Connection = ctx.deps.get("conn")
    with conn:
        balance, version = conn.execute(
            "SELECT balance, version FROM accounts WHERE account_id = ?",
            (account_id,),
        ).fetchone()
    return balance, version


def update_balance_ensure_version(
    ctx: Context,
    account_id: int,
    amount: int,
    version: int,
) -> None:
    conn: Connection = ctx.deps.get("conn")
    with conn:
        cur = conn.execute(
            "SELECT 1 FROM balance_updates WHERE transaction_id = ?",
            (ctx.ctx_id,),
        )
        result_exists = cur.fetchone()
        if result_exists is not None:
            return

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
        if cur.rowcount == 0:
            raise errors.VersionConflictError
        ctx.assert_statement(
            cur.rowcount == 1, msg="Only one row should have been affected."
        )

        conn.execute(
            "INSERT INTO balance_updates (transaction_id) VALUES (?)", (ctx.ctx_id,)
        )


def update_balance(ctx: Context, account_id: int, amount: int) -> None:
    conn: Connection = ctx.deps.get("conn")

    with conn:
        cur = conn.execute(
            "SELECT 1 FROM balance_updates WHERE transaction_id = ?",
            (ctx.ctx_id,),
        )
        result_exists = cur.fetchone()
        if result_exists is not None:
            return

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

        ctx.assert_statement(
            cur.rowcount == 1, msg="Only one row should have been affected."
        )
        conn.execute(
            "INSERT INTO balance_updates (transaction_id) VALUES (?)", (ctx.ctx_id,)
        )


def transaction(
    ctx: Context,
    source: int,
    target: int,
    amount: int,
) -> Generator[Yieldable, Any, tuple[int, int, int]]:
    if source == target:
        raise errors.SameAccountTransferError

    source_balance_and_version: tuple[int, int] = yield ctx.call(
        current_balance,
        account_id=source,
    )
    if source_balance_and_version[0] - amount < 0:
        raise errors.NotEnoughFundsError(account_id=source)

    yield ctx.call(
        update_balance_ensure_version,
        account_id=source,
        amount=amount * -1,
        version=source_balance_and_version[1],
    )
    yield ctx.call(update_balance, account_id=target, amount=amount)

    return source, target, amount
