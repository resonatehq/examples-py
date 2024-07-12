from __future__ import annotations

import sqlite3
from functools import partial
from typing import TYPE_CHECKING

import pytest
import race_condition
import resonate

if TYPE_CHECKING:
    from collections.abc import Generator

    from resonate.scheduler.dst import DSTScheduler


@pytest.fixture()
def setup_and_teardown() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect("test.db")
    ans = conn.execute("SELECT 1").fetchone()
    assert ans == (1,)
    conn.execute("DROP TABLE IF EXISTS accounts")
    conn.execute("CREATE TABLE accounts(account_id, balance)")
    conn.commit()
    yield conn


@pytest.mark.parametrize("scheduler", resonate.testing.dst([range(5)]))
def test_race_condition(
    scheduler: DSTScheduler, setup_and_teardown: sqlite3.Connection
) -> None:
    conn = setup_and_teardown

    new_accounts = range(1, 4)
    balance_at_creation = 100
    for i in new_accounts:
        conn.execute("INSERT INTO accounts VALUES (?, ?)", (i, balance_at_creation))
    conn.commit()

    scheduler.deps.set("conn", conn)

    scheduler.run(
        [
            partial(
                race_condition.transaction,
                source=scheduler.random.choice(new_accounts),
                target=scheduler.random.choice(new_accounts),
                amount=scheduler.random.randint(0, 200),
            )
            for _ in range(1000)
        ]
    )

    accounts_in_negative: int = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE balance < 0"
    ).fetchone()[0]

    assert accounts_in_negative == 0, f"Seed {scheduler.seed} causes a failure"
