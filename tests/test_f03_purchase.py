import asyncio
import re

import pytest

from app import db as appdb
from app import gateway
from app.purchases import EventNotAvailable, InvalidRequest, SoldOut, purchase
from app.seats import available_seats, occupied_seats
from tests.helpers_f03 import make_event, make_ticket

OK, NO, SLOW_OK = "4000000000000001", "4000000000000002", "4000000000000003"


async def buy(event_id, card=OK):
    async with appdb.pool.connection() as conn:
        return await purchase(conn, event_id, card, buyer_email="x@y.io")


async def status_of(db, tid):
    return (await (await db.execute("SELECT status FROM tickets WHERE id=%s", (tid,))).fetchone())["status"]


async def wait_status(db, tid, want, timeout=1.0):
    for _ in range(int(timeout / 0.02)):
        if await status_of(db, tid) == want:
            return
        await asyncio.sleep(0.02)
    assert await status_of(db, tid) == want


@pytest.mark.anyio
async def test_purchase_pending_and_price_recorded(db, running_app):
    # Arrange
    eid = await make_event(db, price=12345)

    # Act
    t = await buy(eid, SLOW_OK)

    # Assert
    row = await (await db.execute("SELECT status, price_cents FROM tickets WHERE id=%s", (t["id"],))).fetchone()
    assert (t["status"], row["status"], row["price_cents"]) == ("pending", "pending", 12345)


@pytest.mark.anyio
@pytest.mark.parametrize("card", ["123", "400000000000000", "40000000000000ab", ""])
async def test_invalid_card_creates_nothing(db, running_app, card):
    # Arrange
    eid = await make_event(db)

    # Act
    with pytest.raises(InvalidRequest):
        await buy(eid, card)

    # Assert
    assert await occupied_seats(db, eid) == 0
    assert (await (await db.execute("SELECT count(*) AS n FROM tickets")).fetchone())["n"] == 0


@pytest.mark.anyio
async def test_draft_event_not_available(db, running_app):
    # Arrange
    eid = await make_event(db, status="draft")

    # Act / Assert
    with pytest.raises(EventNotAvailable):
        await buy(eid)
    with pytest.raises(EventNotAvailable):
        await buy("evt_nope")


@pytest.mark.anyio
async def test_sold_out_when_full(db, running_app):
    # Arrange
    eid = await make_event(db, capacity=1)
    await make_ticket(db, eid, "pending")

    # Act / Assert
    with pytest.raises(SoldOut):
        await buy(eid)


@pytest.mark.anyio
async def test_pending_occupies_seat(db, running_app):
    # Arrange
    eid = await make_event(db, capacity=2)
    event = {"id": eid, "status": "published", "capacity": 2}

    # Act
    await buy(eid, SLOW_OK)

    # Assert
    assert await available_seats(db, event) == 1


@pytest.mark.anyio
async def test_approved_confirms(db, running_app):
    # Arrange
    eid = await make_event(db)

    # Act
    t = await buy(eid, OK)

    # Assert
    await wait_status(db, t["id"], "confirmed")


@pytest.mark.anyio
async def test_declined_frees_seat(db, running_app):
    # Arrange
    eid = await make_event(db, capacity=1)

    # Act
    t = await buy(eid, NO)
    await wait_status(db, t["id"], "declined")

    # Assert
    assert await occupied_seats(db, eid) == 0


@pytest.mark.anyio
async def test_code_unique_format(db, running_app):
    # Arrange
    eid = await make_event(db, capacity=20)

    # Act
    codes = [(await buy(eid, SLOW_OK))["code"] for _ in range(20)]

    # Assert
    assert len(set(codes)) == 20
    assert all(re.fullmatch(r"[A-Z0-9]{8}", c) for c in codes)


@pytest.mark.anyio
async def test_concurrent_purchases_never_exceed_capacity(db, running_app):
    for _ in range(5):
        # Arrange
        eid = await make_event(db, capacity=5)

        # Act: 30 purchases, each on its own pool connection
        results = await asyncio.gather(*(buy(eid, SLOW_OK) for _ in range(30)), return_exceptions=True)

        # Assert
        assert sum(isinstance(r, dict) for r in results) == 5
        assert sum(isinstance(r, SoldOut) for r in results) == 25
        assert await occupied_seats(db, eid) == 5


@pytest.mark.anyio
async def test_reschedule_pending_resolves(db, running_app):
    # Arrange
    from datetime import UTC, datetime, timedelta

    eid = await make_event(db)
    tid = await make_ticket(
        db, eid, "pending", gateway_approved=True, gateway_due_at=datetime.now(UTC) - timedelta(seconds=5)
    )

    # Act
    await gateway.reschedule_pending()

    # Assert
    await wait_status(db, tid, "confirmed")
