import re
import secrets
import string
from datetime import UTC, datetime, timedelta

from psycopg import AsyncConnection, errors

from app.gateway import decide, schedule
from app.seats import occupied_seats

CARD_RE = re.compile(r"^\d{16}$")
_ALPHABET = string.ascii_uppercase + string.digits


class InvalidRequest(Exception):
    pass


class EventNotAvailable(Exception):
    pass


class SoldOut(Exception):
    pass


async def purchase(
    conn: AsyncConnection, event_id: str, card_number: str, *, user_id: str | None = None, buyer_email: str | None = None
) -> dict:
    if not CARD_RE.match(card_number or ""):
        raise InvalidRequest("Número do cartão deve ter 16 dígitos")
    async with conn.transaction():
        # R07: the event row lock serializes every purchase of this event
        cur = await conn.execute("SELECT * FROM events WHERE id=%s FOR UPDATE", (event_id,))
        event = await cur.fetchone()
        if event is None or event["status"] != "published":
            raise EventNotAvailable(event_id)
        if await occupied_seats(conn, event_id) >= event["capacity"]:
            raise SoldOut(event_id)
        approved, delay = decide(card_number)
        due_at = datetime.now(UTC) + timedelta(seconds=delay)
        ticket_id = f"tkt_{secrets.token_hex(5)}"
        for attempt in range(5):
            code = "".join(secrets.choice(_ALPHABET) for _ in range(8))
            try:
                async with conn.transaction():  # savepoint
                    await conn.execute(
                        "INSERT INTO tickets (id, event_id, user_id, buyer_email, code, status, price_cents,"
                        " gateway_approved, gateway_due_at) VALUES (%s,%s,%s,%s,%s,'pending',%s,%s,%s)",
                        (ticket_id, event_id, user_id, buyer_email, code, event["price_cents"], approved, due_at),
                    )
                break
            except errors.UniqueViolation:
                if attempt == 4:
                    raise
    schedule(ticket_id, approved, due_at)
    return {"id": ticket_id, "code": code, "status": "pending", "event_id": event_id}
