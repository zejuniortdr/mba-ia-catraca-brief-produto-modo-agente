from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from psycopg import AsyncConnection

from app import auth, db
from app.events import get_event, list_on_sale, not_found
from app.purchases import EventNotAvailable, InvalidRequest, SoldOut, purchase
from app.seats import available_seats
from app.web import render

router = APIRouter()
User = Annotated[dict, Depends(auth.require_user)]
Conn = Annotated[AsyncConnection, Depends(db.get_conn)]


@router.get("/")
async def showcase(request: Request, conn: Conn):
    return render(request, "shop/home.html", await auth.current_user(request), events=await list_on_sale(conn))


async def _event_page(request, conn, event, status_code=200, error=None):
    sold_out = await available_seats(conn, event) == 0
    return render(
        request, "shop/event.html", await auth.current_user(request), status_code,
        event=event, sold_out=sold_out, error=error,
    )


@router.get("/events/{event_id}")
async def event_page(event_id: str, request: Request, conn: Conn):
    event = await get_event(conn, event_id)
    if event is None or event["status"] != "published":
        return not_found(request, await auth.current_user(request))
    return await _event_page(request, conn, event)


@router.post("/events/{event_id}/buy")
async def buy(event_id: str, request: Request, user: User, conn: Conn, card_number: Annotated[str, Form()] = ""):
    try:
        await purchase(conn, event_id, card_number.strip(), user_id=user["id"], buyer_email=user["email"])
    except EventNotAvailable:
        return not_found(request, user)
    except InvalidRequest as e:
        return await _event_page(request, conn, await get_event(conn, event_id), 422, error=str(e))
    except SoldOut:
        return await _event_page(request, conn, await get_event(conn, event_id), 409)
    return RedirectResponse("/me/tickets", status_code=303)


@router.get("/me/tickets")
async def my_tickets(request: Request, user: User, conn: Conn):
    cur = await conn.execute(
        "SELECT t.id, t.code, t.status, e.name AS event_name FROM tickets t JOIN events e ON e.id = t.event_id"
        " WHERE t.user_id = %s ORDER BY t.created_at DESC",
        (user["id"],),
    )
    return render(request, "shop/tickets.html", user, tickets=await cur.fetchall())
