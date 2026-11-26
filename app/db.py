import os
from collections.abc import AsyncIterator
from pathlib import Path

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://catraca:catraca@localhost:5432/catraca")



def _new_pool() -> AsyncConnectionPool:
    return AsyncConnectionPool(
        DATABASE_URL, min_size=1, max_size=20, open=False, kwargs={"row_factory": dict_row}
    )


pool = _new_pool()


async def open_pool() -> None:
    """Open the pool; a closed pool cannot be reused, so build a fresh one (use `db.pool`, never import it)."""
    global pool
    if pool._closed:
        pool = _new_pool()
    await pool.open(wait=True)


async def get_conn() -> AsyncIterator[AsyncConnection]:
    async with pool.connection() as conn:
        yield conn


async def apply_schema() -> None:
    sql = (Path(__file__).parent / "schema.sql").read_text()
    async with pool.connection() as conn:
        await conn.execute(sql)
