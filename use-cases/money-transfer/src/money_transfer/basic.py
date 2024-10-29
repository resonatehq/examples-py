from __future__ import annotations

from typing import TYPE_CHECKING, Any

from money_transfer import errors

if TYPE_CHECKING:
    from collections.abc import Generator
    from sqlite3 import Connection

    from resonate.context import Context
    from resonate.typing import Yieldable


def current_balance(ctx: Context, account_id: int) -> int:
    conn: Connection = ctx.deps.get("conn")
    balance: int = conn.execute(
        "SELECT balance FROM accounts WHERE account_id = ?",
        (account_id,),
    ).fetchone()[0]
    conn.commit()
    return balance


def update_balance(
    ctx: Context,
    account_id: int,
    amount: int,
) -> None:
    conn: Connection = ctx.deps.get("conn")
    cur = conn.execute(
        """
        UPDATE accounts
        SET balance = balance + ?
        WHERE account_id = ?
        """,
        (amount, account_id),
    )

    ctx.assert_statement(cur.rowcount == 1, msg="More that one row was affected")
    conn.commit()


def transaction(
    ctx: Context,
    source: int,
    target: int,
    amount: int,
) -> Generator[Yieldable, Any, tuple[int, int, int]]:
    if source == target:
        raise errors.SameAccountTransferError

    source_balance: int = yield ctx.call(current_balance, account_id=source)

    if source_balance - amount < 0:
        raise errors.NotEnoughFundsError(account_id=source)

    yield ctx.call(
        update_balance,
        account_id=source,
        amount=amount * -1,
    )

    yield ctx.call(
        update_balance,
        account_id=target,
        amount=amount,
    )
    return source, target, amount
