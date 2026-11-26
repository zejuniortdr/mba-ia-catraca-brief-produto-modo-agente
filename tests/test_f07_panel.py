import pytest

from app.panel import panel_metrics
from tests.helpers_f02 import form
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


@pytest.mark.anyio
async def test_panel_rendered_on_manage_page(org_a, db):
    # Arrange
    r = await org_a.post("/org/events/new", data=form(capacity="5"))
    eid = r.headers["location"].rsplit("/", 1)[1]
    for price in (10000, 10000, 15000):
        t = await make_ticket(db, eid, "confirmed")
        await db.execute("UPDATE tickets SET price_cents=%s WHERE id=%s", (price, t))

    # Act
    r = await org_a.get(f"/org/events/{eid}")

    # Assert
    for label in ("Confirmados", "Pendentes", "Check-ins", "Vagas disponíveis", "Receita", "Estornados"):
        assert label in r.text
    assert 'data-metric="confirmed">3<' in r.text
    assert 'data-metric="revenue">R$ 350,00<' in r.text


@pytest.mark.anyio
async def test_other_org_cannot_see_panel(org_a, org_b, db):
    # Arrange
    r = await org_a.post("/org/events/new", data=form())
    eid = r.headers["location"].rsplit("/", 1)[1]

    # Act
    r = await org_b.get(f"/org/events/{eid}")

    # Assert
    assert r.status_code == 404
    assert 'id="panel"' not in r.text
