import asyncio
import re

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


KEY = {"X-Api-Key": "catraca-parceiro-2026"}
OK, SLOW = "4000000000000001", "4000000000000003"


async def _published(org, **over):
    eid = (await org.post("/org/events/new", data=form(**over))).headers["location"].rsplit("/", 1)[1]
    await org.post(f"/org/events/{eid}/publish")
    return eid


async def _metrics(org, eid):
    html = (await org.get(f"/org/events/{eid}")).text
    return dict(re.findall(r'data-metric="(\w+)">([^<]*)<', html))


async def _api_buy(client, eid, card):
    r = await client.post(f"/api/partner/events/{eid}/purchases", headers=KEY, json={"buyerEmail": "a@b.io", "cardNumber": card})
    assert r.status_code == 202


@pytest.mark.anyio
async def test_web_and_api_purchases_count(org_a, participant, client):
    # Arrange
    eid = await _published(org_a, capacity="6")

    # Act
    await participant.post(f"/events/{eid}/buy", data={"card_number": OK})
    await _api_buy(client, eid, OK)
    await _api_buy(client, eid, SLOW)
    await asyncio.sleep(0.3)

    # Assert
    m = await _metrics(org_a, eid)
    assert (m["confirmed"], m["pending"], m["available"]) == ("2", "1", "3")


@pytest.mark.anyio
async def test_price_change_revenue(org_a, participant):
    # Arrange
    eid = await _published(org_a, capacity="4")
    await participant.post(f"/events/{eid}/buy", data={"card_number": OK})

    # Act
    await org_a.post(f"/org/events/{eid}/edit", data=form(capacity="4", price="150,00"))
    await participant.post(f"/events/{eid}/buy", data={"card_number": OK})
    await asyncio.sleep(0.3)

    # Assert
    assert (await _metrics(org_a, eid))["revenue"] == "R$ 250,00"


@pytest.mark.anyio
async def test_capacity_increase_reflects_available(org_a):
    # Arrange
    eid = await _published(org_a, capacity="2")
    before = int((await _metrics(org_a, eid))["available"])

    # Act
    await org_a.post(f"/org/events/{eid}/edit", data=form(capacity="3"))

    # Assert
    assert (before, int((await _metrics(org_a, eid))["available"])) == (2, 3)
