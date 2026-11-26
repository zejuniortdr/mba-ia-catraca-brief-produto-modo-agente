import re

import pytest

from tests.helpers_f02 import create
from tests.helpers_f03 import make_ticket

SLOW_OK = "4000000000000003"


async def published(org, **over):
    eid = await create(org, **over)
    assert (await org.post(f"/org/events/{eid}/publish")).status_code == 303
    return eid


async def signup(client, email="novo@x.io"):
    r = await client.post("/signup", data={"name": "Novo", "email": email, "password": "senha123"})
    assert r.status_code == 303


@pytest.mark.anyio
async def test_showcase_only_published(client, org_a, db):
    # Arrange
    draft = await create(org_a)
    pub = await published(org_a)
    cancelled = await published(org_a)
    await db.execute("UPDATE events SET status='cancelled' WHERE id=%s", (cancelled,))

    # Act
    html = (await client.get("/")).text

    # Assert
    assert f'data-event-id="{pub}"' in html
    assert draft not in html and cancelled not in html
    assert "R$ 100,00" in html


@pytest.mark.anyio
async def test_event_page_buy_form(client, org_a):
    # Arrange
    eid = await published(org_a)

    # Act
    r = await client.get(f"/events/{eid}")

    # Assert
    assert r.status_code == 200 and 'id="buy-form"' in r.text


@pytest.mark.anyio
async def test_event_page_draft_404(client, org_a):
    # Arrange
    eid = await create(org_a)

    # Act / Assert
    assert (await client.get(f"/events/{eid}")).status_code == 404


@pytest.mark.anyio
async def test_event_page_sold_out_message(client, org_a, db):
    # Arrange
    eid = await published(org_a, capacity="1")
    await make_ticket(db, eid, "pending")

    # Act
    html = (await client.get(f"/events/{eid}")).text

    # Assert
    assert 'id="sold-out">Ingressos esgotados' in html and "buy-form" not in html


@pytest.mark.anyio
async def test_visitor_buy_redirects_login(client, org_a, db):
    # Arrange
    eid = await published(org_a)

    # Act
    r = await client.post(f"/events/{eid}/buy", data={"card_number": SLOW_OK})

    # Assert
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert (await (await db.execute("SELECT count(*) AS n FROM tickets")).fetchone())["n"] == 0


@pytest.mark.anyio
async def test_signup_then_buy_shows_pending_in_my_tickets(client, org_a):
    # Arrange
    eid = await published(org_a)
    await signup(client)

    # Act
    r = await client.post(f"/events/{eid}/buy", data={"card_number": SLOW_OK})
    html = (await client.get("/me/tickets")).text

    # Assert
    assert r.status_code == 303 and r.headers["location"] == "/me/tickets"
    assert 'class="event">Jazz no Porão' in html
    assert 'class="status">pendente' in html
    assert re.search(r'class="code">[A-Z0-9]{8}<', html)


@pytest.mark.anyio
async def test_my_tickets_confirmed_after_gateway(client, org_a):
    # Arrange
    eid = await published(org_a)
    await signup(client)

    # Act
    await client.post(f"/events/{eid}/buy", data={"card_number": "4000000000000001"})
    import asyncio

    await asyncio.sleep(0.2)

    # Assert
    assert 'class="status">confirmado' in (await client.get("/me/tickets")).text


@pytest.mark.anyio
async def test_buy_invalid_card_422(client, org_a, db):
    # Arrange
    eid = await published(org_a)
    await signup(client)

    # Act
    r = await client.post(f"/events/{eid}/buy", data={"card_number": "123"})

    # Assert
    assert r.status_code == 422 and "Número do cartão deve ter 16 dígitos" in r.text
    assert (await (await db.execute("SELECT count(*) AS n FROM tickets")).fetchone())["n"] == 0


@pytest.mark.anyio
async def test_buy_sold_out_409_message(client, org_a, db):
    # Arrange
    eid = await published(org_a, capacity="1")
    await make_ticket(db, eid, "confirmed")
    await signup(client)

    # Act
    r = await client.post(f"/events/{eid}/buy", data={"card_number": SLOW_OK})

    # Assert
    assert r.status_code == 409 and "Ingressos esgotados" in r.text


@pytest.mark.anyio
async def test_buy_unpublished_404(client, org_a):
    # Arrange
    eid = await create(org_a)
    await signup(client)

    # Act / Assert
    assert (await client.post(f"/events/{eid}/buy", data={"card_number": SLOW_OK})).status_code == 404


@pytest.mark.anyio
async def test_my_tickets_only_own(client, participant, org_a):
    # Arrange
    eid = await published(org_a)
    await signup(client)
    await client.post(f"/events/{eid}/buy", data={"card_number": SLOW_OK})

    # Act
    html = (await participant.get("/me/tickets")).text

    # Assert
    assert "data-ticket-id" not in html


@pytest.mark.anyio
async def test_price_change_applies_to_new_purchases_only(client, org_a, db):
    # Arrange
    from tests.helpers_f02 import form

    eid = await published(org_a, capacity="4")
    await signup(client)
    await client.post(f"/events/{eid}/buy", data={"card_number": SLOW_OK})

    # Act
    r = await org_a.post(f"/org/events/{eid}/edit", data=form(capacity="4", price="150,00"))
    await client.post(f"/events/{eid}/buy", data={"card_number": SLOW_OK})

    # Assert
    assert r.status_code == 303
    cur = await db.execute("SELECT price_cents FROM tickets WHERE event_id=%s ORDER BY created_at", (eid,))
    assert [x["price_cents"] for x in await cur.fetchall()] == [10000, 15000]


@pytest.mark.anyio
async def test_capacity_below_web_purchases_rejected(client, org_a):
    # Arrange
    from tests.helpers_f02 import form

    eid = await published(org_a)
    await signup(client)
    for _ in range(2):
        await client.post(f"/events/{eid}/buy", data={"card_number": SLOW_OK})

    # Act
    r = await org_a.post(f"/org/events/{eid}/edit", data=form(capacity="1"))

    # Assert
    assert r.status_code == 422 and "Lotação não pode ser menor que as vagas ocupadas" in r.text
