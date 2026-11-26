import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from psycopg import AsyncConnection

from app import auth, db
from app.seats import occupied_seats
from app.web import render

router = APIRouter()
TZ = timezone(timedelta(hours=-3))
_PRICE = re.compile(r"\d+([.,]\d{1,2})?")


def parse_event_form(form, now: datetime) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    name = (form.get("name") or "").strip()
    venue = (form.get("venue") or "").strip()
    if not name:
        errors.append("Nome é obrigatório")
    if not venue:
        errors.append("Local é obrigatório")
    starts_at = None
    try:
        starts_at = datetime.strptime((form.get("starts_at") or "").strip(), "%Y-%m-%dT%H:%M").replace(tzinfo=TZ)
        if starts_at <= now:
            errors.append("Data de início precisa estar no futuro")
    except ValueError:
        errors.append("Data de início inválida")
    capacity = None
    raw = (form.get("capacity") or "").strip()
    if raw.isdigit() and int(raw) >= 1:
        capacity = int(raw)
    else:
        errors.append("Lotação deve ser um inteiro maior ou igual a 1")
    price_cents = None
    raw = (form.get("price") or "").strip()
    if _PRICE.fullmatch(raw):
        price_cents = round(float(raw.replace(",", ".")) * 100)
    if not price_cents:
        errors.append("Preço deve ser maior que zero")
    if errors:
        return None, errors
    return {"name": name, "venue": venue, "starts_at": starts_at, "capacity": capacity, "price_cents": price_cents}, []


async def get_event(conn: AsyncConnection, event_id: str) -> dict | None:
    cur = await conn.execute("SELECT * FROM events WHERE id = %s", (event_id,))
    return await cur.fetchone()


async def get_owned_event(conn: AsyncConnection, event_id: str, organizer_id: str) -> dict | None:
    cur = await conn.execute("SELECT * FROM events WHERE id = %s AND organizer_id = %s", (event_id, organizer_id))
    return await cur.fetchone()


async def list_on_sale(conn: AsyncConnection) -> list[dict]:
    cur = await conn.execute("SELECT * FROM events WHERE status = 'published' ORDER BY starts_at")
    return await cur.fetchall()


async def list_by_organizer(conn: AsyncConnection, organizer_id: str) -> list[dict]:
    cur = await conn.execute("SELECT * FROM events WHERE organizer_id = %s ORDER BY starts_at", (organizer_id,))
    return await cur.fetchall()


async def manage_context(request: Request, conn: AsyncConnection, event: dict, user: dict) -> dict:
    return {"request": request, "user": user, "event": event, "errors": []}


def render_manage(ctx: dict, status_code: int = 200):
    return render(ctx["request"], "org/manage.html", ctx["user"], status_code, **{k: v for k, v in ctx.items() if k not in ("request", "user")})


def not_found(request: Request, user: dict):
    return render(request, "404.html", user, 404)


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


Organizer = Annotated[dict, Depends(auth.require_organizer)]
Conn = Annotated[AsyncConnection, Depends(db.get_conn)]


@router.get("/org/events")
async def org_list(request: Request, user: Organizer, conn: Conn):
    return render(request, "org/list.html", user, events=await list_by_organizer(conn, user["id"]))


@router.get("/org/events/new")
async def new_form(request: Request, user: Organizer):
    return render(request, "org/new.html", user, errors=[], form={})


@router.post("/org/events/new")
async def create(request: Request, user: Organizer, conn: Conn):
    form = await request.form()
    data, errors = parse_event_form(form, datetime.now(TZ))
    if errors:
        return render(request, "org/new.html", user, 422, errors=errors, form=form)
    event_id = f"evt_{secrets.token_hex(5)}"
    await conn.execute(
        "INSERT INTO events (id, organizer_id, name, starts_at, venue, capacity, price_cents)"
        " VALUES (%(id)s, %(org)s, %(name)s, %(starts_at)s, %(venue)s, %(capacity)s, %(price_cents)s)",
        {**data, "id": event_id, "org": user["id"]},
    )
    return _redirect(f"/org/events/{event_id}")


@router.get("/org/events/{event_id}")
async def manage(event_id: str, request: Request, user: Organizer, conn: Conn):
    event = await get_owned_event(conn, event_id, user["id"])
    if event is None:
        return not_found(request, user)
    return render_manage(await manage_context(request, conn, event, user))


@router.post("/org/events/{event_id}/edit")
async def edit(event_id: str, request: Request, user: Organizer, conn: Conn):
    cur = await conn.execute(
        "SELECT * FROM events WHERE id = %s AND organizer_id = %s FOR UPDATE", (event_id, user["id"])
    )
    event = await cur.fetchone()
    if event is None:
        return not_found(request, user)
    form = await request.form()
    data, errors = parse_event_form(form, datetime.now(TZ))
    if data and data["capacity"] < (occupied := await occupied_seats(conn, event_id)):
        errors.append(f"Lotação não pode ser menor que as vagas ocupadas ({occupied})")
    if errors:
        ctx = await manage_context(request, conn, event, user)
        ctx.update(errors=errors, form=form)
        return render_manage(ctx, 422)
    await conn.execute(
        "UPDATE events SET name=%(name)s, venue=%(venue)s, starts_at=%(starts_at)s, capacity=%(capacity)s,"
        " price_cents=%(price_cents)s WHERE id=%(id)s",
        {**data, "id": event_id},
    )
    return _redirect(f"/org/events/{event_id}")


@router.post("/org/events/{event_id}/publish")
async def publish(event_id: str, request: Request, user: Organizer, conn: Conn):
    event = await get_owned_event(conn, event_id, user["id"])
    if event is None:
        return not_found(request, user)
    cur = await conn.execute(
        "UPDATE events SET status='published' WHERE id=%s AND organizer_id=%s AND status='draft'",
        (event_id, user["id"]),
    )
    if cur.rowcount == 0:
        ctx = await manage_context(request, conn, event, user)
        ctx["errors"] = ["Evento não pode ser publicado"]
        return render_manage(ctx, 409)
    return _redirect(f"/org/events/{event_id}")
