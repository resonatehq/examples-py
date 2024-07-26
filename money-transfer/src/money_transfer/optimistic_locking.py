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
    balance, version = conn.execute(
        "SELECT balance, version FROM accounts WHERE account_id = ?",
        (account_id,),
    ).fetchone()
    conn.commit()
    return balance, version


def update_balance_ensure_version(
    ctx: Context,
    account_id: int,
    amount: int,
    version: int,
) -> None:
    conn: Connection = ctx.deps.get("conn")
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
        raise errors.VersionConflictError
    ctx.assert_statement(cur.rowcount == 1, msg="More that one row was affected")


def update_balance(ctx: Context, account_id: int, amount: int) -> None:
    conn: Connection = ctx.deps.get("conn")

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
    ctx: Context,
    source: int,
    target: int,
    amount: int,
) -> Generator[Yieldable, Any, tuple[int, int, int]]:
    source_balance_and_version: tuple[int, int] = yield ctx.call(
        current_balance,
        account_id=source,
    )
    source_balance, version = source_balance_and_version

    if source_balance - amount < 0:
        raise errors.NotEnoughFundsError(account_id=source)

    yield ctx.call(
        update_balance_ensure_version,
        account_id=source,
        amount=amount * -1,
        version=version,
    )

    yield ctx.call(update_balance, account_id=target, amount=amount)
    return source, target, amount
