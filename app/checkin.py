from typing import Annotated

from fastapi import APIRouter, Depends, Request
from psycopg import AsyncConnection

from app import auth, db
from app.events import get_owned_event, manage_context, not_found, render_manage

router = APIRouter()

INVALID = "Ingresso inválido para este evento"
CANCELLED = "Evento cancelado"
NOT_CONFIRMED = "Ingresso não confirmado"
USED = "Ingresso já utilizado"
ALLOWED = "Entrada liberada"


async def check_in(conn: AsyncConnection, event: dict, code: str) -> str:
    async with conn.transaction():
        # row lock on the ticket: two simultaneous check-ins of one code cannot both pass
        cur = await conn.execute(
            "SELECT * FROM tickets WHERE code=%s AND event_id=%s FOR UPDATE", (code.strip().upper(), event["id"])
        )
        ticket = await cur.fetchone()
        if ticket is None:
            return INVALID
        if event["status"] == "cancelled":
            return CANCELLED
        if ticket["status"] != "confirmed":
            return NOT_CONFIRMED
        if ticket["checked_in"]:
            return USED
        await conn.execute("UPDATE tickets SET checked_in=true WHERE id=%s", (ticket["id"],))
        return ALLOWED


Organizer = Annotated[dict, Depends(auth.require_organizer)]
Conn = Annotated[AsyncConnection, Depends(db.get_conn)]


@router.post("/org/events/{event_id}/checkin")
async def checkin(event_id: str, request: Request, user: Organizer, conn: Conn):
    event = await get_owned_event(conn, event_id, user["id"])
    if event is None:
        return not_found(request, user)
    form = await request.form()
    ctx = await manage_context(request, conn, event, user)
    ctx["checkin_result"] = await check_in(conn, event, str(form.get("code", "")))
    return render_manage(ctx)
