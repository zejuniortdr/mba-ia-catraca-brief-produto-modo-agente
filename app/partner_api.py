import hmac
import json
import os
import re
from datetime import timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from psycopg import AsyncConnection

from app import db
from app.events import list_on_sale
from app.purchases import EventNotAvailable, InvalidRequest, SoldOut, purchase
from app.seats import available_seats

BRT = timezone(timedelta(hours=-3))
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CARD_RE = re.compile(r"^\d{16}$")


class Unauthorized(Exception):
    pass


async def require_partner_key(request: Request) -> None:
    key = request.headers.get("x-api-key", "")
    expected = os.environ.get("PARTNER_API_KEY", "catraca-parceiro-2026")
    if not hmac.compare_digest(key.encode(), expected.encode()):
        raise Unauthorized


def _error(status: int, code: str) -> JSONResponse:
    return JSONResponse({"error": code}, status_code=status)


router = APIRouter(prefix="/api/partner", dependencies=[Depends(require_partner_key)])
Conn = Annotated[AsyncConnection, Depends(db.get_conn)]


@router.get("/events")
async def list_events(conn: Conn):
    return [
        {
            "id": e["id"],
            "name": e["name"],
            "startsAt": e["starts_at"].astimezone(BRT).isoformat(),
            "priceCents": e["price_cents"],
            "availableSeats": await available_seats(conn, e),
        }
        for e in await list_on_sale(conn)
    ]


@router.post("/events/{event_id}/purchases")
async def create_purchase(event_id: str, request: Request, conn: Conn):
    try:
        body = json.loads(await request.body())
    except ValueError:
        return _error(422, "invalid_request")
    email = body.get("buyerEmail") if isinstance(body, dict) else None
    card = body.get("cardNumber") if isinstance(body, dict) else None
    if not (isinstance(email, str) and EMAIL_RE.match(email) and isinstance(card, str) and CARD_RE.match(card)):
        return _error(422, "invalid_request")
    try:
        t = await purchase(conn, event_id, card, buyer_email=email)
    except EventNotAvailable:
        return _error(404, "event_not_available")
    except SoldOut:
        return _error(409, "sold_out")
    except InvalidRequest:
        return _error(422, "invalid_request")
    return JSONResponse({"ticketId": t["id"], "code": t["code"], "status": "pending"}, status_code=202)


@router.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, conn: Conn):
    cur = await conn.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
    t = await cur.fetchone()
    if t is None:
        return _error(404, "ticket_not_found")
    return {
        "ticketId": t["id"],
        "code": t["code"],
        "eventId": t["event_id"],
        "status": t["status"],
        "checkedIn": t["checked_in"],
    }
