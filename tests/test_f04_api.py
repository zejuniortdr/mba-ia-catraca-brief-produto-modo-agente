import asyncio
import re
from collections import Counter

import pytest

from tests.helpers_f03 import make_event, make_ticket

KEY = {"X-Api-Key": "catraca-parceiro-2026"}
OK = "4000000000000001"
DECLINED = "4000000000000004"
BODY = {"buyerEmail": "t2@example.com", "cardNumber": OK}
ROUTES = [("GET", "/api/partner/events"), ("POST", "/api/partner/events/evt_x/purchases"), ("GET", "/api/partner/tickets/x")]


async def post(client, eid, body=BODY, **kw):
    return await client.post(f"/api/partner/events/{eid}/purchases", headers=KEY, json=body, **kw)


@pytest.mark.anyio
@pytest.mark.parametrize("headers", [{}, {"X-Api-Key": "errada"}])
@pytest.mark.parametrize("method,path", ROUTES)
async def test_unauthorized(client, method, path, headers):
    # Act
    r = await client.request(method, path, headers=headers, json=BODY)

    # Assert
    assert (r.status_code, r.json()) == (401, {"error": "unauthorized"})


@pytest.mark.anyio
async def test_unauthorized_before_body_validation(client):
    # Act
    r = await client.post("/api/partner/events/evt_x/purchases", content="xyz")

    # Assert
    assert (r.status_code, r.json()) == (401, {"error": "unauthorized"})


@pytest.mark.anyio
async def test_list_only_published(client, db):
    # Arrange
    pub = await make_event(db, capacity=2, price=10000)
    await make_event(db, status="draft")
    await make_event(db, status="cancelled")

    # Act
    r = await client.get("/api/partner/events", headers=KEY)

    # Assert
    data = r.json()
    assert r.status_code == 200
    assert [e["id"] for e in data] == [pub]
    assert (data[0]["availableSeats"], data[0]["priceCents"]) == (2, 10000)


@pytest.mark.anyio
async def test_list_fields_exact(client, db):
    # Arrange
    await make_event(db)

    # Act
    e = (await client.get("/api/partner/events", headers=KEY)).json()[0]

    # Assert
    assert set(e) == {"id", "name", "startsAt", "priceCents", "availableSeats"}
    assert e["startsAt"].endswith("-03:00")


@pytest.mark.anyio
async def test_purchase_202_pending(client, db):
    # Arrange
    eid = await make_event(db)

    # Act
    r = await post(client, eid)

    # Assert
    j = r.json()
    assert r.status_code == 202
    assert set(j) == {"ticketId", "code", "status"}
    assert j["status"] == "pending" and re.fullmatch(r"[A-Z0-9]{8}", j["code"])


@pytest.mark.anyio
@pytest.mark.parametrize(
    "kw",
    [
        {"content": ""},
        {"content": "xyz"},
        {"json": {"cardNumber": OK}},
        {"json": {"buyerEmail": "ana@", "cardNumber": OK}},
        {"json": {"buyerEmail": "a@b.co", "cardNumber": "123"}},
        {"json": {"buyerEmail": "a@b.co", "cardNumber": 4000000000000001}},
        {"json": [1]},
    ],
)
async def test_invalid_body_422(client, db, kw):
    # Arrange
    eid = await make_event(db)

    # Act
    r = await client.post(f"/api/partner/events/{eid}/purchases", headers=KEY, **kw)

    # Assert
    assert (r.status_code, r.json()) == (422, {"error": "invalid_request"})


@pytest.mark.anyio
async def test_error_order_invalid_before_not_found(client, db):
    # Act
    r = await post(client, "evt_naoexiste", {"buyerEmail": "a@b.co", "cardNumber": "123"})

    # Assert
    assert r.status_code == 422


@pytest.mark.anyio
@pytest.mark.parametrize("status", [None, "draft", "cancelled"])
async def test_event_not_available_404(client, db, status):
    # Arrange
    eid = "evt_naoexiste" if status is None else await make_event(db, status=status)

    # Act
    r = await post(client, eid)

    # Assert
    assert (r.status_code, r.json()) == (404, {"error": "event_not_available"})


@pytest.mark.anyio
async def test_not_found_before_sold_out(client, db):
    # Arrange
    eid = await make_event(db, capacity=1, status="draft")
    await make_ticket(db, eid)

    # Act
    r = await post(client, eid)

    # Assert
    assert r.status_code == 404


@pytest.mark.anyio
async def test_sold_out_409(client, db):
    # Arrange
    eid = await make_event(db, capacity=1)
    await post(client, eid)

    # Act
    r = await post(client, eid)

    # Assert
    assert (r.status_code, r.json()) == (409, {"error": "sold_out"})
    assert (await client.get("/api/partner/events", headers=KEY)).json()[0]["availableSeats"] == 0


@pytest.mark.anyio
async def test_burst_30_capacity_5(client, db):
    for _ in range(5):
        # Arrange
        eid = await make_event(db, capacity=5)

        # Act
        rs = await asyncio.gather(
            *[post(client, eid, {"buyerEmail": f"c{i}@example.com", "cardNumber": OK}) for i in range(30)]
        )

        # Assert
        assert Counter(r.status_code for r in rs) == {202: 5, 409: 25}


@pytest.mark.anyio
async def test_ticket_lookup_fields(client, db):
    # Arrange
    eid = await make_event(db)
    t = (await post(client, eid)).json()

    # Act
    r = await client.get(f"/api/partner/tickets/{t['ticketId']}", headers=KEY)

    # Assert
    assert r.status_code == 200
    assert r.json() == {
        "ticketId": t["ticketId"],
        "code": t["code"],
        "eventId": eid,
        "status": "pending",
        "checkedIn": False,
    }


@pytest.mark.anyio
async def test_ticket_not_found_404(client):
    # Act
    r = await client.get("/api/partner/tickets/tkt_inexistente", headers=KEY)

    # Assert
    assert (r.status_code, r.json()) == (404, {"error": "ticket_not_found"})


@pytest.mark.anyio
async def test_web_ticket_visible_in_api(client, participant, db):
    # Arrange
    eid = await make_event(db)
    await participant.post(f"/events/{eid}/buy", data={"card_number": OK})
    row = await (await db.execute("SELECT id, code FROM tickets WHERE event_id=%s", (eid,))).fetchone()

    # Act
    r = await client.get(f"/api/partner/tickets/{row['id']}", headers=KEY)

    # Assert
    assert (r.status_code, r.json()["code"], r.json()["eventId"]) == (200, row["code"], eid)


@pytest.mark.anyio
async def test_api_sellout_shows_sold_out_on_showcase(client, participant, db):
    # Arrange
    eid = await make_event(db, capacity=1)
    await post(client, eid)

    # Act
    r = await participant.get(f"/events/{eid}")

    # Assert
    assert "Ingressos esgotados" in r.text


@pytest.mark.anyio
async def test_declined_frees_seat(client, db):
    # Arrange
    eid = await make_event(db, capacity=2)
    tid = (await post(client, eid, {"buyerEmail": "a@b.co", "cardNumber": DECLINED})).json()["ticketId"]

    # Act
    status = None
    for _ in range(100):
        status = (await client.get(f"/api/partner/tickets/{tid}", headers=KEY)).json()["status"]
        if status == "declined":
            break
        await asyncio.sleep(0.02)

    # Assert
    assert status == "declined"
    assert (await client.get("/api/partner/events", headers=KEY)).json()[0]["availableSeats"] == 2
