import pytest

from app import events
from app.seats import available_seats, occupied_seats
from tests.helpers_f02 import create

pytestmark = pytest.mark.anyio


async def add_tickets(db, eid, statuses):
    for i, s in enumerate(statuses):
        await db.execute(
            "INSERT INTO tickets(id,event_id,code,status,price_cents) VALUES (%s,%s,%s,%s,10000)",
            (f"tkt_{i}", eid, f"CODE000{i}", s),
        )


async def test_occupied_counts_pending_confirmed(org_a, db):
    eid = await create(org_a)
    await add_tickets(db, eid, ["pending", "confirmed", "declined", "cancelled", "refunded"])

    assert await occupied_seats(db, eid) == 2


async def test_available_cancelled_zero(org_a, db):
    eid = await create(org_a)
    await db.execute("UPDATE events SET status='cancelled'")

    assert await available_seats(db, await events.get_event(db, eid)) == 0


async def test_available_subtracts_occupied(org_a, db):
    eid = await create(org_a, capacity="3")
    await add_tickets(db, eid, ["pending"])

    assert await available_seats(db, await events.get_event(db, eid)) == 2
