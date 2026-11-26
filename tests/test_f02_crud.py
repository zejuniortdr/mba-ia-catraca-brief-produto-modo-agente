import pytest

from tests.helpers_f02 import PAST, create, form

pytestmark = pytest.mark.anyio


async def test_create_event_draft(org_a, db):
    r = await org_a.post("/org/events/new", data=form())

    assert r.status_code == 303 and r.headers["location"].startswith("/org/events/evt_")
    row = await (await db.execute("SELECT status FROM events")).fetchone()
    assert row["status"] == "draft"


async def test_create_past_date_422(org_a):
    r = await org_a.post("/org/events/new", data=form(starts_at=PAST))

    assert r.status_code == 422 and "Data de início precisa estar no futuro" in r.text


async def test_org_list_only_own(org_a, org_b):
    eid = await create(org_a)

    r = await org_b.get("/org/events")

    assert r.status_code == 200 and f'data-event-id="{eid}"' not in r.text


async def test_org_list_own_has_event(org_a):
    eid = await create(org_a)

    r = await org_a.get("/org/events")

    assert f'data-event-id="{eid}"' in r.text


async def test_participant_seed_forbidden_org_events(participant):
    assert (await participant.get("/org/events")).status_code == 403


async def test_org_a_seed_access_org_events(org_a):
    assert (await org_a.get("/org/events")).status_code == 200


async def test_manage_page_markers(org_a):
    eid = await create(org_a)

    r = await org_a.get(f"/org/events/{eid}")

    assert r.status_code == 200
    for m in ('id="event-name">Jazz no Porão', 'id="event-status">rascunho', 'id="edit-form"',
              'id="publish-form"', "R$ 100,00"):
        assert m in r.text


async def test_other_org_manage_404_no_data(org_a, org_b):
    eid = await create(org_a)

    r = await org_b.get(f"/org/events/{eid}")

    assert r.status_code == 404 and "Jazz no Porão" not in r.text and "Bar do Zé" not in r.text


async def test_other_org_post_edit_404(org_a, org_b, db):
    eid = await create(org_a)

    r = await org_b.post(f"/org/events/{eid}/edit", data=form(name="Hack"))

    assert r.status_code == 404
    assert (await (await db.execute("SELECT name FROM events")).fetchone())["name"] == "Jazz no Porão"


async def test_other_org_post_publish_404(org_a, org_b, db):
    eid = await create(org_a)

    r = await org_b.post(f"/org/events/{eid}/publish")

    assert r.status_code == 404
    assert (await (await db.execute("SELECT status FROM events")).fetchone())["status"] == "draft"


async def test_anonymous_redirects_to_login(client):
    r = await client.get("/org/events/evt_x")

    assert r.status_code == 303 and r.headers["location"] == "/login"
