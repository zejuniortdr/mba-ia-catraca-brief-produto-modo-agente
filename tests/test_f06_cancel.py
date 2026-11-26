import asyncio

import pytest

from tests.helpers_f02 import create, form
from tests.helpers_f03 import make_ticket

KEY = {"X-Api-Key": "catraca-parceiro-2026"}
OK = "4000000000000001"
SLOW_OK = "4000000000000003"


async def published(org, **over):
    eid = await create(org, **over)
    assert (await org.post(f"/org/events/{eid}/publish")).status_code == 303
    return eid


async def event_status(db, eid):
    return (await (await db.execute("SELECT status FROM events WHERE id=%s", (eid,))).fetchone())["status"]


async def ticket_status(db, tid):
    return (await (await db.execute("SELECT status FROM tickets WHERE id=%s", (tid,))).fetchone())["status"]


@pytest.mark.anyio
async def test_cancel_published(org_a, db):
    # Arrange
    eid = await published(org_a)

    # Act
    r = await org_a.post(f"/org/events/{eid}/cancel")

    # Assert
    assert r.status_code == 303 and r.headers["location"] == f"/org/events/{eid}"
    assert await event_status(db, eid) == "cancelled"


@pytest.mark.anyio
async def test_cancel_draft_409(org_a, db):
    # Arrange
    eid = await create(org_a)

    # Act
    r = await org_a.post(f"/org/events/{eid}/cancel")

    # Assert
    assert r.status_code == 409 and "Só evento publicado pode ser cancelado" in r.text
    assert await event_status(db, eid) == "draft"


@pytest.mark.anyio
async def test_cancel_twice_409(org_a):
    # Arrange
    eid = await published(org_a)
    await org_a.post(f"/org/events/{eid}/cancel")

    # Act
    r = await org_a.post(f"/org/events/{eid}/cancel")

    # Assert
    assert r.status_code == 409 and "Só evento publicado pode ser cancelado" in r.text


@pytest.mark.anyio
async def test_cancel_transitions(org_a, db):
    # Arrange
    eid = await published(org_a, capacity="10")
    conf = await make_ticket(db, eid, "confirmed")
    pend = await make_ticket(db, eid, "pending")
    decl = await make_ticket(db, eid, "declined")

    # Act
    await org_a.post(f"/org/events/{eid}/cancel")

    # Assert
    assert [await ticket_status(db, t) for t in (conf, pend, decl)] == ["refunded", "cancelled", "declined"]


@pytest.mark.anyio
async def test_other_org_cancel_404(org_a, org_b, db):
    # Arrange
    eid = await published(org_a, name="Segredo Total")

    # Act
    r = await org_b.post(f"/org/events/{eid}/cancel")

    # Assert
    assert r.status_code == 404 and "Segredo Total" not in r.text
    assert await event_status(db, eid) == "published"


@pytest.mark.anyio
async def test_late_gateway_does_not_change_cancelled(org_a, client, db):
    # Arrange
    eid = await published(org_a)
    r = await client.post(f"/api/partner/events/{eid}/purchases", headers=KEY, json={"buyerEmail": "a@b.co", "cardNumber": SLOW_OK})
    tid = r.json()["ticketId"]

    # Act
    await org_a.post(f"/org/events/{eid}/cancel")
    await asyncio.sleep(0.7)

    # Assert
    assert await ticket_status(db, tid) == "cancelled"


@pytest.mark.anyio
async def test_late_gateway_approved_before_cancel_becomes_refunded(org_a, client, db):
    # Arrange
    eid = await published(org_a)
    r = await client.post(f"/api/partner/events/{eid}/purchases", headers=KEY, json={"buyerEmail": "a@b.co", "cardNumber": OK})
    tid = r.json()["ticketId"]
    await asyncio.sleep(0.2)
    assert await ticket_status(db, tid) == "confirmed"

    # Act
    await org_a.post(f"/org/events/{eid}/cancel")

    # Assert
    assert await ticket_status(db, tid) == "refunded"


@pytest.mark.anyio
async def test_edit_cancelled_409(org_a, db):
    # Arrange
    eid = await published(org_a)
    await org_a.post(f"/org/events/{eid}/cancel")

    # Act
    r = await org_a.post(f"/org/events/{eid}/edit", data=form(name="Outro", capacity="5"))

    # Assert
    row = await (await db.execute("SELECT name, capacity FROM events WHERE id=%s", (eid,))).fetchone()
    assert r.status_code == 409 and "Evento cancelado não pode ser editado" in r.text
    assert (row["name"], row["capacity"]) == ("Jazz no Porão", 2)


@pytest.mark.anyio
async def test_publish_cancelled_409(org_a, db):
    # Arrange
    eid = await published(org_a)
    await org_a.post(f"/org/events/{eid}/cancel")

    # Act
    r = await org_a.post(f"/org/events/{eid}/publish")

    # Assert
    assert r.status_code == 409
    assert await event_status(db, eid) == "cancelled"


@pytest.mark.anyio
async def test_manage_page_cancelled_no_forms(org_a):
    # Arrange
    eid = await published(org_a)
    before = (await org_a.get(f"/org/events/{eid}")).text
    await org_a.post(f"/org/events/{eid}/cancel")

    # Act
    html = (await org_a.get(f"/org/events/{eid}")).text

    # Assert
    assert 'id="cancel-form"' in before
    assert 'id="event-status">cancelado' in html and 'id="event-cancelled"' in html
    assert not any(f'id="{f}"' in html for f in ("edit-form", "publish-form", "cancel-form"))


@pytest.mark.anyio
async def test_cancelled_out_of_showcase_and_api(org_a, client, participant, db):
    # Arrange
    eid = await published(org_a)
    await org_a.post(f"/org/events/{eid}/cancel")

    # Act
    showcase = (await client.get("/")).text
    api_list = (await client.get("/api/partner/events", headers=KEY)).json()
    page = await participant.get(f"/events/{eid}")
    buy = await participant.post(f"/events/{eid}/buy", data={"card_number": OK})
    api_buy = await client.post(f"/api/partner/events/{eid}/purchases", headers=KEY, json={"buyerEmail": "a@b.co", "cardNumber": OK})

    # Assert
    assert eid not in showcase and api_list == []
    assert (page.status_code, buy.status_code, api_buy.status_code) == (404, 404, 404)
    assert api_buy.json() == {"error": "event_not_available"}
    assert (await (await db.execute("SELECT count(*) AS n FROM tickets")).fetchone())["n"] == 0


@pytest.mark.anyio
async def test_my_tickets_shows_refunded_and_cancelled(org_a, participant):
    # Arrange
    eid = await published(org_a)
    await participant.post(f"/events/{eid}/buy", data={"card_number": OK})
    await asyncio.sleep(0.2)
    await participant.post(f"/events/{eid}/buy", data={"card_number": SLOW_OK})

    # Act
    await org_a.post(f"/org/events/{eid}/cancel")
    html = (await participant.get("/me/tickets")).text

    # Assert
    assert 'class="status">estornado' in html and 'class="status">cancelado' in html


@pytest.mark.anyio
async def test_api_tickets_after_cancel(org_a, client):
    # Arrange
    eid = await published(org_a)
    t1 = (await client.post(f"/api/partner/events/{eid}/purchases", headers=KEY, json={"buyerEmail": "a@b.co", "cardNumber": OK})).json()["ticketId"]
    t2 = (await client.post(f"/api/partner/events/{eid}/purchases", headers=KEY, json={"buyerEmail": "a@b.co", "cardNumber": SLOW_OK})).json()["ticketId"]
    await asyncio.sleep(0.2)

    # Act
    await org_a.post(f"/org/events/{eid}/cancel")
    s1 = (await client.get(f"/api/partner/tickets/{t1}", headers=KEY)).json()["status"]
    s2 = (await client.get(f"/api/partner/tickets/{t2}", headers=KEY)).json()["status"]

    # Assert
    assert (s1, s2) == ("refunded", "cancelled")


@pytest.mark.anyio
async def test_cancel_during_burst_never_leaves_pending(org_a, client, db):
    # Arrange
    eid = await published(org_a, capacity="30")
    body = {"buyerEmail": "a@b.co", "cardNumber": OK}

    # Act
    await asyncio.gather(
        org_a.post(f"/org/events/{eid}/cancel"),
        *[client.post(f"/api/partner/events/{eid}/purchases", headers=KEY, json=body) for _ in range(20)],
    )
    await asyncio.sleep(0.7)

    # Assert
    cur = await db.execute("SELECT count(*) AS n FROM tickets WHERE event_id=%s AND status IN ('pending','confirmed')", (eid,))
    assert (await cur.fetchone())["n"] == 0
