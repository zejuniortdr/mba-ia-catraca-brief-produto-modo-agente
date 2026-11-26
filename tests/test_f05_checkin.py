import asyncio

import pytest

from app import checkin as ck
from app import db as appdb
from app.events import get_event
from tests.helpers_f02 import create
from tests.helpers_f03 import make_event, make_ticket

KEY = {"X-Api-Key": "catraca-parceiro-2026"}


async def run(eid, code):
    async with appdb.pool.connection() as conn:
        return await ck.check_in(conn, await get_event(conn, eid), code)


async def checked(db, tid):
    return (await (await db.execute("SELECT checked_in FROM tickets WHERE id=%s", (tid,))).fetchone())["checked_in"]


@pytest.mark.anyio
async def test_unknown_code_invalid(db, running_app):
    # Arrange
    eid = await make_event(db)

    # Act
    msg = await run(eid, "ZZZZZZZZ")

    # Assert
    assert msg == "Ingresso inválido para este evento"


@pytest.mark.anyio
async def test_cancelled_event_message(db, running_app):
    # Arrange
    eid = await make_event(db)
    await make_ticket(db, eid, "confirmed", code="AAAA1111")
    await db.execute("UPDATE events SET status='cancelled' WHERE id=%s", (eid,))

    # Act
    msg = await run(eid, "AAAA1111")

    # Assert
    assert msg == "Evento cancelado"


@pytest.mark.anyio
@pytest.mark.parametrize("status", ["pending", "declined", "cancelled", "refunded"])
async def test_not_confirmed(db, running_app, status):
    # Arrange
    eid = await make_event(db)
    tid = await make_ticket(db, eid, status, code="AAAA1111")

    # Act
    msg = await run(eid, "AAAA1111")

    # Assert
    assert (msg, await checked(db, tid)) == ("Ingresso não confirmado", False)


@pytest.mark.anyio
async def test_already_used(db, running_app):
    # Arrange
    eid = await make_event(db)
    await make_ticket(db, eid, "confirmed", code="AAAA1111")
    await run(eid, "AAAA1111")

    # Act
    msg = await run(eid, "AAAA1111")

    # Assert
    assert msg == "Ingresso já utilizado"


@pytest.mark.anyio
async def test_entry_allowed_marks_checked_in(db, running_app):
    # Arrange
    eid = await make_event(db)
    tid = await make_ticket(db, eid, "confirmed", code="AAAA1111")

    # Act
    msg = await run(eid, "AAAA1111")

    # Assert
    assert (msg, await checked(db, tid)) == ("Entrada liberada", True)


@pytest.mark.anyio
async def test_other_event_code_invalid_even_if_cancelled(db, running_app):
    # Arrange
    e1 = await make_event(db)
    e2 = await make_event(db)
    await make_ticket(db, e2, "confirmed", code="BBBB2222")
    await db.execute("UPDATE events SET status='cancelled' WHERE id=%s", (e1,))

    # Act
    msg = await run(e1, "BBBB2222")

    # Assert
    assert msg == "Ingresso inválido para este evento"


@pytest.mark.anyio
async def test_code_normalized(db, running_app):
    # Arrange
    eid = await make_event(db)
    await make_ticket(db, eid, "confirmed", code="AAAA1111")

    # Act
    msg = await run(eid, "  aaaa1111 ")

    # Assert
    assert msg == "Entrada liberada"


async def published(org, **over):
    eid = await create(org, **over)
    assert (await org.post(f"/org/events/{eid}/publish")).status_code == 303
    return eid


async def code_of(db, tid):
    return (await (await db.execute("SELECT code FROM tickets WHERE id=%s", (tid,))).fetchone())["code"]


async def wait_confirmed(client, tid):
    for _ in range(100):
        if (await client.get(f"/api/partner/tickets/{tid}", headers=KEY)).json()["status"] == "confirmed":
            return
        await asyncio.sleep(0.02)
    raise AssertionError("not confirmed")


@pytest.mark.anyio
async def test_checkin_page_has_form(org_a):
    # Arrange
    eid = await create(org_a)

    # Act
    r = await org_a.get(f"/org/events/{eid}")

    # Assert
    assert 'id="checkin-form"' in r.text


@pytest.mark.anyio
async def test_checkin_post_shows_message(org_a, db):
    # Arrange
    eid = await create(org_a)
    await make_ticket(db, eid, "confirmed", code="AAAA1111")

    # Act
    r = await org_a.post(f"/org/events/{eid}/checkin", data={"code": "AAAA1111"})

    # Assert
    assert r.status_code == 200
    assert 'id="checkin-result">Entrada liberada' in r.text


@pytest.mark.anyio
async def test_other_org_checkin_404(org_a, org_b, db):
    # Arrange
    eid = await create(org_a)
    tid = await make_ticket(db, eid, "confirmed", code="AAAA1111")

    # Act
    r = await org_b.post(f"/org/events/{eid}/checkin", data={"code": "AAAA1111"})

    # Assert
    assert r.status_code == 404
    assert "Jazz no Porão" not in r.text
    assert not await checked(db, tid)


@pytest.mark.anyio
async def test_web_ticket_flow(org_a, participant, db):
    # Arrange
    eid = await published(org_a, capacity="5")
    other = await published(org_a, capacity="5")
    await participant.post(f"/events/{eid}/buy", data={"card_number": "4000000000000001"})
    await participant.post(f"/events/{eid}/buy", data={"card_number": "4000000000000003"})
    await participant.post(f"/events/{other}/buy", data={"card_number": "4000000000000001"})
    rows = await (await db.execute("SELECT code, event_id, gateway_approved, gateway_due_at FROM tickets ORDER BY created_at")).fetchall()
    ok, slow, foreign = rows[0]["code"], rows[1]["code"], rows[2]["code"]
    await asyncio.sleep(0.2)

    # Act
    r_ok = await org_a.post(f"/org/events/{eid}/checkin", data={"code": ok})
    r_slow = await org_a.post(f"/org/events/{eid}/checkin", data={"code": slow})
    r_foreign = await org_a.post(f"/org/events/{eid}/checkin", data={"code": foreign})

    # Assert
    assert 'id="checkin-result">Entrada liberada' in r_ok.text
    assert 'id="checkin-result">Ingresso não confirmado' in r_slow.text
    assert 'id="checkin-result">Ingresso inválido para este evento' in r_foreign.text


@pytest.mark.anyio
async def test_api_ticket_checkin_reflects_in_api(org_a, client, db):
    # Arrange
    eid = await published(org_a)
    r = await client.post(
        f"/api/partner/events/{eid}/purchases", headers=KEY, json={"buyerEmail": "a@b.co", "cardNumber": "4000000000000001"}
    )
    tid = r.json()["ticketId"]
    await wait_confirmed(client, tid)

    # Act
    page = await org_a.post(f"/org/events/{eid}/checkin", data={"code": await code_of(db, tid)})

    # Assert
    assert "Entrada liberada" in page.text
    assert (await client.get(f"/api/partner/tickets/{tid}", headers=KEY)).json()["checkedIn"] is True
