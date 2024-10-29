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
        balance_with_version: tuple[int, int] = conn.execute(
            """
                SELECT balance - IFNULL(
                    (
                    SELECT SUM(amount)
                    FROM transfers
                    WHERE account_id = ?
                    AND amount > 0
                    ), 0)
                , version
                FROM accounts
                WHERE account_id = ?
                """,
            (
                account_id,
                account_id,
            ),
        ).fetchone()
        balance, version = balance_with_version
    return balance, version


def rollback(ctx: Context, transfer_id: int) -> None:
    conn: Connection = ctx.deps.get("conn")
    with conn:
        transfers: list[tuple[int, int]] = conn.execute(
            "SELECT amount, account_id FROM transfers WHERE transfer_id = ?",
            (transfer_id,),
        ).fetchall()

        if len(transfers) > 0:
            cur = conn.executemany(
                """
                    UPDATE accounts
                    SET
                        balance = balance - ?,
                        version = version + 1
                    WHERE account_id = ?
                    """,
                transfers,
            )
            ctx.assert_statement(cur.rowcount > 0, "More that one row must be affected")
            conn.execute("DELETE FROM transfers WHERE transfer_id = ?", (transfer_id,))


def update_balance_ensuring_version(
    ctx: Context, transfer_id: int, account_id: int, amount: int, version: int
) -> None:
    conn: Connection = ctx.deps.get("conn")
    with conn:
        conn.execute(
            "INSERT INTO transfers (transfer_id, account_id, amount) VALUES (?, ?, ?)",
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
        if cur.rowcount == 0:
            raise errors.VersionConflictError
    ctx.assert_statement(cur.rowcount == 1, msg="More that one row was affected")


def update_balance(
    ctx: Context,
    transfer_id: int,
    account_id: int,
    amount: int,
) -> None:
    conn: Connection = ctx.deps.get("conn")
    with conn:
        conn.execute(
            "INSERT INTO transfers (transfer_id, account_id, amount) VALUES (?, ?, ?)",
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

    ctx.assert_statement(cur.rowcount == 1, msg="More that one row was affected")


def transaction(
    ctx: Context,
    transfer_id: int,
    source: int,
    target: int,
    amount: int,
) -> Generator[Yieldable, Any, tuple[int, int, int]]:
    if source == target:
        raise errors.SameAccountTransferError

    yield ctx.call(rollback, transfer_id=transfer_id)

    source_balance_and_version: tuple[int, int] = yield ctx.call(
        current_balance,
        account_id=source,
    )
    source_balance, version = source_balance_and_version

    if source_balance - amount < 0:
        raise errors.NotEnoughFundsError(account_id=source)

    yield ctx.call(
        update_balance_ensuring_version,
        transfer_id=transfer_id,
        account_id=source,
        amount=amount * -1,
        version=version,
    )
    yield ctx.call(
        update_balance,
        transfer_id=transfer_id,
        account_id=target,
        amount=amount,
    )

    return source, target, amount
