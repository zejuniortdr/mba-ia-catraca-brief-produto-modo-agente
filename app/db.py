import os
from collections.abc import AsyncIterator
from pathlib import Path

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://catraca:catraca@localhost:5432/catraca")

pool = AsyncConnectionPool(DATABASE_URL, min_size=1, max_size=20, open=False, kwargs={"row_factory": dict_row})


async def get_conn() -> AsyncIterator[AsyncConnection]:
    async with pool.connection() as conn:
        yield conn


async def apply_schema() -> None:
    sql = (Path(__file__).parent / "schema.sql").read_text()
    async with pool.connection() as conn:
        await conn.execute(sql)
