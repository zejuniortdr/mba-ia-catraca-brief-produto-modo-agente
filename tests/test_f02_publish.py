import pytest

from app import events
from tests.helpers_f02 import create

pytestmark = pytest.mark.anyio


async def test_draft_not_on_sale(org_a, db):
    await create(org_a)

    assert await events.list_on_sale(db) == []


async def test_publish_then_on_sale(org_a, db):
    eid = await create(org_a)

    r = await org_a.post(f"/org/events/{eid}/publish")

    assert r.status_code == 303
    assert [e["id"] for e in await events.list_on_sale(db)] == [eid]
    page = await org_a.get(f"/org/events/{eid}")
    assert 'id="event-status">publicado' in page.text and "publish-form" not in page.text


async def test_publish_twice_409(org_a):
    eid = await create(org_a)
    await org_a.post(f"/org/events/{eid}/publish")

    r = await org_a.post(f"/org/events/{eid}/publish")

    assert r.status_code == 409 and "Evento não pode ser publicado" in r.text
