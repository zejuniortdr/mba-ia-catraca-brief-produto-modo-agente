import pytest

from tests.helpers_f02 import PAST, create, form
from tests.test_f02_seats import add_tickets

pytestmark = pytest.mark.anyio


async def test_edit_capacity_below_occupied_422(org_a, db):
    eid = await create(org_a)
    await add_tickets(db, eid, ["pending", "confirmed"])

    r = await org_a.post(f"/org/events/{eid}/edit", data=form(capacity="1"))

    assert r.status_code == 422 and "Lotação não pode ser menor que as vagas ocupadas (2)" in r.text


async def test_edit_capacity_increase_ok(org_a, db):
    eid = await create(org_a)

    r = await org_a.post(f"/org/events/{eid}/edit", data=form(capacity="3"))

    assert r.status_code == 303
    assert (await (await db.execute("SELECT capacity FROM events")).fetchone())["capacity"] == 3


async def test_edit_past_date_422(org_a):
    eid = await create(org_a)

    r = await org_a.post(f"/org/events/{eid}/edit", data=form(starts_at=PAST))

    assert r.status_code == 422 and "Data de início precisa estar no futuro" in r.text


async def test_edit_price_ok(org_a):
    eid = await create(org_a)

    await org_a.post(f"/org/events/{eid}/edit", data=form(capacity="3", price="150,00"))

    page = await org_a.get(f"/org/events/{eid}")
    assert "R$ 150,00" in page.text and "Lotação: 3" in page.text
