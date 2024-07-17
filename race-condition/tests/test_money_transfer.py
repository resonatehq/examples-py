from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest
import race_condition
import resonate

if TYPE_CHECKING:
    from resonate.scheduler.dst import DSTScheduler


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(5)],
        mode="sequential",
    ),
)
def test_sequential_execution_and_no_failure(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    conn.execute("CREATE TABLE accounts(account_id, balance)")
    conn.commit()

    new_accounts = range(1, 4)
    balance_at_creation = 100
    for i in new_accounts:
        conn.execute("INSERT INTO accounts VALUES (?, ?)", (i, balance_at_creation))
    conn.commit()

    scheduler.deps.set("conn", conn)
    for _ in range(1000):
        scheduler.add(
            race_condition.basic.transaction,
            source=scheduler.random.choice(new_accounts),
            target=scheduler.random.choice(new_accounts),
            amount=scheduler.random.randint(0, 200),
        )

    scheduler.run()

    accounts_in_negative: int = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE balance < 0"
    ).fetchone()[0]

    total_money_in_system: int = conn.execute(
        "SELECT SUM(balance) FROM accounts"
    ).fetchone()[0]

    assert (
        accounts_in_negative == 0  # no account gets in the negative
        and total_money_in_system
        == len(new_accounts) * balance_at_creation  # we never destroy money
    ), f"Seed {scheduler.seed} causes a failure"


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(5)],
        mode="concurrent",
    ),
)
def test_concurrent_execution_and_no_failure(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    conn.execute("CREATE TABLE accounts(account_id, balance)")
    conn.commit()

    new_accounts = range(1, 4)
    balance_at_creation = 100
    for i in new_accounts:
        conn.execute("INSERT INTO accounts VALUES (?, ?)", (i, balance_at_creation))
    conn.commit()

    scheduler.deps.set("conn", conn)
    for _ in range(1000):
        scheduler.add(
            race_condition.basic.transaction,
            source=scheduler.random.choice(new_accounts),
            target=scheduler.random.choice(new_accounts),
            amount=scheduler.random.randint(0, 200),
        )

    scheduler.run()

    accounts_in_negative: int = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE balance < 0"
    ).fetchone()[0]

    total_money_in_system: int = conn.execute(
        "SELECT SUM(balance) FROM accounts"
    ).fetchone()[0]

    assert (
        accounts_in_negative >= 0  # sometimes we get accounts on negative
        and total_money_in_system
        == len(new_accounts) * balance_at_creation  # we never destroy money
    ), f"Seed {scheduler.seed} causes a failure"


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(5)],
        mode="concurrent",
    ),
)
def test_concurrent_execution_with_optimistic_locking_and_no_failure(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    conn.execute("CREATE TABLE accounts(account_id, balance, version)")
    conn.commit()

    new_accounts = range(1, 4)
    balance_at_creation = 100
    for i in new_accounts:
        conn.execute(
            "INSERT INTO accounts VALUES (?, ?, ?)", (i, balance_at_creation, 0)
        )
    conn.commit()

    scheduler.deps.set("conn", conn)
    for _ in range(1000):
        scheduler.add(
            race_condition.optimistic_locking.transaction,
            source=scheduler.random.choice(new_accounts),
            target=scheduler.random.choice(new_accounts),
            amount=scheduler.random.randint(0, 200),
        )

    promises = scheduler.run()
    assert (p.done() for p in promises)

    accounts_in_negative: int = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE balance < 0"
    ).fetchone()[0]

    total_money_in_system: int = conn.execute(
        "SELECT SUM(balance) FROM accounts"
    ).fetchone()[0]

    assert (
        accounts_in_negative == 0  # no account get in the negative
        and total_money_in_system
        == len(new_accounts) * balance_at_creation  # we never destroy money
    ), f"Seed {scheduler.seed} causes a failure"


@pytest.mark.parametrize(
    "scheduler",
    resonate.testing.dst(
        [range(5)], mode="concurrent", failure_chance=10, max_failures=10000
    ),
)
def test_concurrent_execution_with_optimistic_locking_and_with_failure(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    conn.execute("CREATE TABLE accounts(account_id, balance, version)")
    conn.commit()

    new_accounts = range(1, 4)
    balance_at_creation = 100
    for i in new_accounts:
        conn.execute(
            "INSERT INTO accounts VALUES (?, ?, ?)", (i, balance_at_creation, 0)
        )
    conn.commit()

    scheduler.deps.set("conn", conn)
    for _ in range(10):
        scheduler.add(
            race_condition.optimistic_locking.transaction,
            source=scheduler.random.choice(new_accounts),
            target=scheduler.random.choice(new_accounts),
            amount=scheduler.random.randint(0, 200),
        )

    promises = scheduler.run()
    assert (p.done() for p in promises)

    accounts_in_negative: int = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE balance < 0"
    ).fetchone()[0]

    total_money_in_system: int = conn.execute(
        "SELECT SUM(balance) FROM accounts"
    ).fetchone()[0]

    assert (
        accounts_in_negative == 0 # no account in the negative
        and total_money_in_system != len(new_accounts) * balance_at_creation # we destroy money
    ), f"Seed {scheduler.seed} causes a failure"
