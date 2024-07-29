import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture()
def setup_and_teardown() -> Generator[sqlite3.Connection, None, None]:
    path_db = Path().cwd() / "test.db"
    path_db.unlink(missing_ok=True)
    conn = sqlite3.connect(path_db)
    ans = conn.execute("SELECT 1").fetchone()
    assert ans == (1,)
    conn.execute("DROP TABLE IF EXISTS accounts")
    conn.execute("DROP TABLE IF EXISTS transfers")
    yield conn
    path_db.unlink(missing_ok=False)
