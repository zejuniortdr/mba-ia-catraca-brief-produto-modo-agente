from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.events import Conn, Organizer, manage_context, not_found, render_manage

router = APIRouter()


@router.post("/org/events/{event_id}/cancel")
async def cancel(event_id: str, request: Request, user: Organizer, conn: Conn):
    cur = await conn.execute(
        "SELECT * FROM events WHERE id = %s AND organizer_id = %s FOR UPDATE", (event_id, user["id"])
    )
    event = await cur.fetchone()
    if event is None:
        return not_found(request, user)
    if event["status"] != "published":
        ctx = await manage_context(request, conn, event, user)
        ctx["errors"] = ["Só evento publicado pode ser cancelado"]
        return render_manage(ctx, 409)
    await conn.execute("UPDATE events SET status='cancelled' WHERE id=%s", (event_id,))
    await conn.execute(
        "UPDATE tickets SET status = CASE status WHEN 'confirmed' THEN 'refunded' ELSE 'cancelled' END"
        " WHERE event_id=%s AND status IN ('pending','confirmed')",
        (event_id,),
    )
    return RedirectResponse(f"/org/events/{event_id}", status_code=303)
