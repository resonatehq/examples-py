import sqlite3

import pytest


@pytest.fixture()
def setup_and_teardown() -> sqlite3.Connection:
    conn = sqlite3.connect("test.db")
    ans = conn.execute("SELECT 1").fetchone()
    assert ans == (1,)
    conn.execute("DROP TABLE IF EXISTS accounts")
    conn.execute("DROP TABLE IF EXISTS transfers")
    conn.execute("DROP TABLE IF EXISTS balance_updates")
    return conn
