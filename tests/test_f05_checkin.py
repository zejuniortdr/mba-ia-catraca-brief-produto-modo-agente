import pytest

from app import checkin as ck
from app import db as appdb
from app.events import get_event
from tests.helpers_f03 import make_event, make_ticket


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
