import pytest

from app.panel import panel_metrics
from tests.helpers_f03 import make_event, make_ticket


async def _event(db, eid):
    return await (await db.execute("SELECT * FROM events WHERE id=%s", (eid,))).fetchone()


@pytest.mark.anyio
async def test_metrics_counts(db):
    # Arrange
    eid = await make_event(db, capacity=10)
    a = await make_ticket(db, eid, "confirmed")
    await make_ticket(db, eid, "confirmed")
    await db.execute("UPDATE tickets SET checked_in=true WHERE id=%s", (a,))
    for s in ("pending", "declined", "cancelled", "refunded"):
        await make_ticket(db, eid, s)

    # Act
    m = await panel_metrics(db, await _event(db, eid))

    # Assert
    assert (m["confirmed"], m["pending"], m["checkins"], m["refunded"]) == (2, 1, 1, 1)
    assert m["available"] == 7


@pytest.mark.anyio
async def test_revenue_uses_ticket_price(db):
    # Arrange
    eid = await make_event(db, capacity=10, price=99900)
    for s, p in [("confirmed", 10000), ("confirmed", 10000), ("confirmed", 15000), ("refunded", 10000), ("declined", 10000)]:
        t = await make_ticket(db, eid, s)
        await db.execute("UPDATE tickets SET price_cents=%s WHERE id=%s", (p, t))

    # Act
    m = await panel_metrics(db, await _event(db, eid))

    # Assert
    assert m["revenue_cents"] == 35000


@pytest.mark.anyio
async def test_available_cancelled_zero(db):
    # Arrange
    eid = await make_event(db, capacity=5, status="cancelled")

    # Act
    m = await panel_metrics(db, await _event(db, eid))

    # Assert
    assert m["available"] == 0
