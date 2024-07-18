class NotEnoughFundsError(Exception):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"Account {account_id} does not have enough money")


class VersionConflict(Exception):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"Version conflict {account_id}")


def rollback(ctx, ikey):
    conn = ctx.deps.get("conn")
    # Get all the transfer entries related to the current context (ctx.id)
    transfers = conn.execute(
        "SELECT account_id, amount FROM transfer WHERE transfer_id = ?", (ikey,)
    ).fetchall()
    for account_id, amount in transfers:
        # Revert the changes in balance
        conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE account_id = ?",
            (amount, account_id),
        )
    # Delete the transfer entries for the current context
    conn.execute("DELETE FROM transfer WHERE transfer_id = ?", (ikey,))
    conn.commit()


def get_balance(ctx, account):
    conn = ctx.deps.get("conn")
    resp = conn.execute(
        "SELECT balance, version FROM accounts WHERE account_id = ?", (account,)
    ).fetchone()
    conn.commit()
    return resp[0], resp[1]


def set_balance(ctx, id, account, amount, version=None):
    conn = ctx.deps.get("conn")
    conn.execute(
        "INSERT INTO transfer (transfer_id, account_id, amount) VALUES (?, ?, ?)",
        (id, account, amount),
    )
    if version is None:
        resp = conn.execute(
            "UPDATE accounts SET balance = balance + ?, version = version + 1 WHERE account_id = ?",
            (amount, account),
        )
        conn.commit()
        ctx.assert_statement(resp.rowcount == 1, msg="More that one row was affected")
    else:
        resp = conn.execute(
            "UPDATE accounts SET balance = balance + ?, version = version + 1 WHERE account_id = ? AND version = ?",
            (amount, account, version),
        )
        if resp.rowcount == 0:
            conn.rollback()
            raise VersionConflict(account_id=account)
        else:
            conn.commit()


def transfer(ctx, id, source, target, amount):
    yield ctx.call(rollback, id)

    balance, version = yield ctx.call(get_balance, account=source)

    if balance - amount < 0:
        raise NotEnoughFundsError(account_id=source)

    yield ctx.call(set_balance, id, source, -1 * amount, version)

    yield ctx.call(set_balance, id, target, +1 * amount)

    return (source, target, amount)
