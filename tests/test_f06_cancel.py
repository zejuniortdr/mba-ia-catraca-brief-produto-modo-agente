import pytest

from tests.helpers_f02 import create
from tests.helpers_f03 import make_ticket



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
