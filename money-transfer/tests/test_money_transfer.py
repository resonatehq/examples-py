from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest
import money_transfer
import resonate

import money_transfer.optimistic_rollback

if TYPE_CHECKING:
    from resonate.scheduler.dst import DSTScheduler


ACCOUNTS = range(1, 4)
INITIAL_BALANCE = 100
MAX_TRANSACTION = 150
NUM_SEEDS = 5
NUM_TRANSACTIONS = 100


def check_invariants(conn: sqlite3.Connection, seed: int) -> None:
    accounts_in_negative: int = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE balance < 0"
    ).fetchone()[0]

    total_money_in_system: int = conn.execute(
        "SELECT SUM(balance) FROM accounts"
    ).fetchone()[0]

    assert (
        accounts_in_negative == 0
    ), f"Seed {seed} causes a accounts to get in the negatives"

    assert (
        total_money_in_system == len(ACCOUNTS) * INITIAL_BALANCE
    ), f"Seed {seed} created or destroyed money in the system"


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(NUM_SEEDS)],
        mode="sequential",
    ),
)
def test_sequential_execution_and_no_failure(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    conn.execute("CREATE TABLE accounts(account_id, balance)")
    conn.commit()

    for i in ACCOUNTS:
        conn.execute("INSERT INTO accounts VALUES (?, ?)", (i, INITIAL_BALANCE))
    conn.commit()

    scheduler.deps.set("conn", conn)
    for _ in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.basic.transaction,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )

    promises = scheduler.run()
    assert (p.done() for p in promises)

    check_invariants(conn=conn, seed=scheduler.seed)


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(NUM_SEEDS)],
        mode="concurrent",
    ),
)
def test_concurrent_execution_and_no_failure(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    conn.execute("CREATE TABLE accounts(account_id, balance)")
    conn.commit()

    for i in ACCOUNTS:
        conn.execute("INSERT INTO accounts VALUES (?, ?)", (i, INITIAL_BALANCE))
    conn.commit()

    scheduler.deps.set("conn", conn)
    for _ in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.basic.transaction,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )

    promises = scheduler.run()
    assert (p.done() for p in promises)

    check_invariants(conn=conn, seed=scheduler.seed)


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(NUM_SEEDS)],
        mode="concurrent",
    ),
)
def test_concurrent_execution_with_optimistic_locking_and_no_failure(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    conn.execute("CREATE TABLE accounts(account_id, balance, version)")
    conn.commit()

    for i in ACCOUNTS:
        conn.execute("INSERT INTO accounts VALUES (?, ?, ?)", (i, INITIAL_BALANCE, 0))
    conn.commit()

    scheduler.deps.set("conn", conn)
    for _ in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.optimistic_locking.transaction,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )

    promises = scheduler.run()
    assert (p.done() for p in promises)

    check_invariants(conn=conn, seed=scheduler.seed)


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(NUM_SEEDS)],
        mode="concurrent",
        failure_chance=0.2,
        max_failures=1_000,
    ),
)
def test_concurrent_execution_with_optimistic_locking_and_with_failure(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    conn.execute("CREATE TABLE accounts(account_id, balance, version)")
    conn.commit()

    for i in ACCOUNTS:
        conn.execute("INSERT INTO accounts VALUES (?, ?, ?)", (i, INITIAL_BALANCE, 0))
    conn.commit()

    scheduler.deps.set("conn", conn)
    for _ in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.optimistic_locking.transaction,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )

    promises = scheduler.run()
    assert (p.done() for p in promises)

    check_invariants(conn=conn, seed=scheduler.seed)


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(NUM_SEEDS)],
        mode="concurrent",
        failure_chance=0.2,
        max_failures=1_000,
    ),
)
def test_concurrent_execution_with_optimistic_locking_and_optimistic_rollback(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    conn.execute("CREATE TABLE transfers(transfer_id, account_id, amount)")
    conn.execute("CREATE TABLE accounts(account_id, balance, version)")
    conn.commit()

    for i in ACCOUNTS:
        conn.execute("INSERT INTO accounts VALUES (?, ?, ?)", (i, INITIAL_BALANCE, 0))
    conn.commit()

    scheduler.deps.set("conn", conn)
    for i in range(NUM_TRANSACTIONS):
        scheduler.add(
            money_transfer.optimistic_rollback.transaction,
            transfer_id=i,
            source=scheduler.random.choice(ACCOUNTS),
            target=scheduler.random.choice(ACCOUNTS),
            amount=scheduler.random.randint(0, MAX_TRANSACTION),
        )

    promises = scheduler.run()
    assert (p.done() for p in promises)

    check_invariants(conn=conn, seed=scheduler.seed)
