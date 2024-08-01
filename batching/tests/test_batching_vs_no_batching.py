from sqlite3 import Connection

import batching
import pytest
import resonate
from resonate.dst.scheduler import DSTScheduler

DB_TRANSACTIONS = 10_000
SEED = 232


@pytest.mark.parametrize("scheduler", resonate.testing.dst(seeds=[SEED]))
def test_no_batching(scheduler: DSTScheduler, setup_and_teardown: Connection) -> None:
    conn = setup_and_teardown

    conn.execute(
        "CREATE TABLE IF NOT EXISTS benchmark (id INTEGER PRIMARY KEY, value INTEGER)"
    )
    conn.commit()

    scheduler.deps.set("conn", conn)
    for i in range(DB_TRANSACTIONS):
        scheduler.add(batching.insert_value_by_value, value=i)

    promises = scheduler.run()
    assert all(p.success() for p in promises)


@pytest.mark.parametrize("scheduler", resonate.testing.dst(seeds=[SEED]))
def test_batching(scheduler: DSTScheduler, setup_and_teardown: Connection) -> None:
    conn = setup_and_teardown

    conn.execute(
        "CREATE TABLE IF NOT EXISTS benchmark (id INTEGER PRIMARY KEY, value INTEGER)"
    )
    conn.commit()

    scheduler.deps.set("conn", conn)
    scheduler.register_command(
        batching.Insert,
        batching.insert_handler,
        max_batch=DB_TRANSACTIONS,
    )
    for i in range(DB_TRANSACTIONS):
        scheduler.add(batching.insert_values_using_batch, value=i)

    promises = scheduler.run()
    assert all(p.success() for p in promises)
