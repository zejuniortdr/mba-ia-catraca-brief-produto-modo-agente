import os
from pathlib import Path

import psycopg
import pytest

_admin_url = os.environ["DATABASE_URL"]
TEST_URL = os.environ["TEST_DATABASE_URL"]

with psycopg.connect(_admin_url, autocommit=True) as _c:
    if not _c.execute("SELECT 1 FROM pg_database WHERE datname='catraca_test'").fetchone():
        _c.execute("CREATE DATABASE catraca_test")

os.environ["DATABASE_URL"] = TEST_URL  # must happen before app.db is imported

import httpx
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db():
    """AsyncConnection (autocommit) to the clean test database; use for SQL state setup."""
    async with await AsyncConnection.connect(TEST_URL, autocommit=True, row_factory=dict_row) as conn:
        await conn.execute((Path(__file__).parent.parent / "app" / "schema.sql").read_text())
        await conn.execute("TRUNCATE users, events, tickets CASCADE")
        yield conn


@pytest.fixture
async def running_app(db):
    async with app.router.lifespan_context(app):
        yield app


def _client():
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def client(running_app):
    async with _client() as c:
        yield c


async def _logged(email):
    async with _client() as c:
        r = await c.post("/login", data={"email": email, "password": "catraca123"})
        assert r.status_code == 303
        yield c


@pytest.fixture
async def org_a(running_app):
    async for c in _logged("org.a@catraca.local"):
        yield c


@pytest.fixture
async def org_b(running_app):
    async for c in _logged("org.b@catraca.local"):
        yield c


@pytest.fixture
async def participant(running_app):
    async for c in _logged("participante@catraca.local"):
        yield c

