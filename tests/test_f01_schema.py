import psycopg
import pytest


async def _user(db):
    await db.execute("INSERT INTO users VALUES ('u1','N','n@x','h','organizer')")


async def _event(db, capacity=5):
    await db.execute(
        "INSERT INTO events (id, organizer_id, name, starts_at, venue, capacity, price_cents)"
        " VALUES ('e1','u1','E', now(), 'V', %s, 100)",
        (capacity,),
    )


@pytest.mark.anyio
async def test_schema_has_tables(db):
    # Act
    cur = await db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    names = {r["table_name"] for r in await cur.fetchall()}

    # Assert
    assert {"users", "events", "tickets"} <= names


@pytest.mark.anyio
async def test_event_capacity_check(db):
    # Arrange
    await _user(db)

    # Act / Assert
    with pytest.raises(psycopg.errors.CheckViolation):
        await _event(db, capacity=0)


async def _ticket(db, code="ABCDEFGH", status="pending"):
    await db.execute(
        "INSERT INTO tickets (id, event_id, code, status, price_cents) VALUES (%s,'e1',%s,%s,100)",
        (f"t-{code}-{status}", code, status),
    )


@pytest.mark.anyio
async def test_ticket_status_check(db):
    # Arrange
    await _user(db)
    await _event(db)

    # Act / Assert
    with pytest.raises(psycopg.errors.CheckViolation):
        await _ticket(db, status="foo")


@pytest.mark.anyio
async def test_ticket_code_unique(db):
    # Arrange
    await _user(db)
    await _event(db)
    await _ticket(db, status="pending")

    # Act / Assert
    with pytest.raises(psycopg.errors.UniqueViolation):
        await _ticket(db, status="confirmed")
