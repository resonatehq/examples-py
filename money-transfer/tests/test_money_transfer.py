from __future__ import annotations

from typing import TYPE_CHECKING, Any

import money_transfer
import pytest
import resonate
from money_transfer import errors

if TYPE_CHECKING:
    import sqlite3

    from resonate.dst.scheduler import DSTScheduler
    from resonate.promise import Promise


ACCOUNTS = range(1, 4)
INITIAL_BALANCE = 100
MAX_TRANSACTION = 150
NUM_SEEDS = 5
NUM_TRANSACTIONS = 100


def check_invariants(
    conn: sqlite3.Connection,
    seed: int,
    promises: list[Promise[Any]],
    *,
    with_transfers: bool,
) -> None:
    assert all(p.done() for p in promises)

    accounts_in_negative: int = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE balance < 0",
    ).fetchone()[0]
    assert (
        accounts_in_negative == 0
    ), f"Seed {seed} causes a accounts to get in the negatives"

    total_money_in_system: int = conn.execute(
        "SELECT SUM(balance) FROM accounts",
    ).fetchone()[0]

    assert (
        total_money_in_system == len(ACCOUNTS) * INITIAL_BALANCE
    ), f"Seed {seed} created or destroyed money in the system"

    mock_tables = {i: INITIAL_BALANCE for i in ACCOUNTS}
    for p in promises:
        if not p.success():
            try:
                p.result()
            except (
                errors.NotEnoughFundsError,
                errors.VersionConflictError,
                errors.SameAccountTransferError,
            ):
                continue

        source_target_amount: tuple[int, int, int] = p.result()
        source, target, amount = source_target_amount
        mock_tables[source] -= amount
        mock_tables[target] += amount

    accounts: list[tuple[int, int]] = conn.execute(
        "SELECT account_id, balance FROM accounts",
    ).fetchall()
    for account in accounts:
        assert (
            account[-1] == mock_tables[account[0]]
        ), f"Balance is SQL table is different compared to mock table for account {account[0]}"  # noqa: E501

    if with_transfers:
        assert conn.execute("SELECT SUM(amount) FROM transfers").fetchone()[0] == 0


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(NUM_SEEDS)],
        mode="sequential",
    ),
)
def test_sequential_execution_and_no_failure(
    scheduler: DSTScheduler,
    setup_and_teardown: sqlite3.Connection,
) -> None:
    conn = setup_and_teardown

    with conn:
        conn.execute("CREATE TABLE accounts(account_id, balance)")

    with conn:
        for i in ACCOUNTS:
            conn.execute("INSERT INTO accounts VALUES (?, ?)", (i, INITIAL_BALANCE))

    scheduler.deps.set("conn", conn)
    for _ in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.basic.transaction,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )

    check_invariants(
        conn,
        scheduler.seed,
        scheduler.run(),
        with_transfers=False,
    )


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(NUM_SEEDS)],
        mode="concurrent",
    ),
)
def test_concurrent_execution_and_no_failure(
    scheduler: DSTScheduler,
    setup_and_teardown: sqlite3.Connection,
) -> None:
    conn = setup_and_teardown

    with conn:
        conn.execute("CREATE TABLE accounts(account_id, balance)")

    with conn:
        for i in ACCOUNTS:
            conn.execute("INSERT INTO accounts VALUES (?, ?)", (i, INITIAL_BALANCE))

    scheduler.deps.set("conn", conn)
    for _ in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.basic.transaction,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )

    check_invariants(
        conn,
        scheduler.seed,
        scheduler.run(),
        with_transfers=False,
    )


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(NUM_SEEDS)],
        mode="concurrent",
    ),
)
def test_concurrent_execution_with_optimistic_locking_and_no_failure(
    scheduler: DSTScheduler,
    setup_and_teardown: sqlite3.Connection,
) -> None:
    conn = setup_and_teardown

    with conn:
        conn.execute("CREATE TABLE accounts(account_id, balance, version)")

    with conn:
        for i in ACCOUNTS:
            conn.execute(
                "INSERT INTO accounts VALUES (?, ?, ?)", (i, INITIAL_BALANCE, 0)
            )

    scheduler.deps.set("conn", conn)
    for _ in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.optimistic_locking.transaction,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )

    check_invariants(
        conn,
        scheduler.seed,
        scheduler.run(),
        with_transfers=False,
    )


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(NUM_SEEDS)],
        mode="concurrent",
        failure_chance=0.6,
        max_failures=1_000,
    ),
)
def test_concurrent_execution_with_optimistic_locking_and_with_failure(
    scheduler: DSTScheduler,
    setup_and_teardown: sqlite3.Connection,
) -> None:
    conn = setup_and_teardown

    with conn:
        conn.execute("CREATE TABLE accounts(account_id, balance, version)")

    with conn:
        for i in ACCOUNTS:
            conn.execute(
                "INSERT INTO accounts VALUES (?, ?, ?)", (i, INITIAL_BALANCE, 0)
            )

    scheduler.deps.set("conn", conn)
    for _ in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.optimistic_locking.transaction,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )

    check_invariants(
        conn,
        scheduler.seed,
        scheduler.run(),
        with_transfers=False,
    )


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        seeds=[range(NUM_SEEDS)],
        mode="concurrent",
        failure_chance=0.15,
        max_failures=1_000,
    ),
)
def test_concurrent_execution_with_optimistic_locking_and_optimistic_rollback(
    scheduler: DSTScheduler,
    setup_and_teardown: sqlite3.Connection,
) -> None:
    conn = setup_and_teardown

    with conn:
        conn.execute("CREATE TABLE transfers(transfer_id, account_id, amount)")
        conn.execute("CREATE TABLE accounts(account_id, balance, version)")

    with conn:
        for i in ACCOUNTS:
            conn.execute(
                "INSERT INTO accounts VALUES (?, ?, ?)", (i, INITIAL_BALANCE, 0)
            )

    scheduler.deps.set("conn", conn)
    for i in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.optimistic_locking_and_rollback.transaction,
            transfer_id=i,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )
    check_invariants(
        conn,
        scheduler.seed,
        scheduler.run(),
        with_transfers=True,
    )
