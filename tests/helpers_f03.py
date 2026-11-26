import secrets
from datetime import UTC, datetime, timedelta


async def make_event(db, capacity=2, price=10000, status="published"):
    cur = await db.execute("SELECT id FROM users WHERE role='organizer' LIMIT 1")
    org = await cur.fetchone()
    if org is None:
        await db.execute(
            "INSERT INTO users (id, name, email, password_hash, role) VALUES ('usr_org','Org','o@x.io','x','organizer')"
        )
        org = {"id": "usr_org"}
    eid = f"evt_{secrets.token_hex(5)}"
    await db.execute(
        "INSERT INTO events (id, organizer_id, name, starts_at, venue, capacity, price_cents, status)"
        " VALUES (%s,%s,'Jazz', %s,'Bar',%s,%s,%s)",
        (eid, org["id"], datetime.now(UTC) + timedelta(days=30), capacity, price, status),
    )
    return eid


async def make_ticket(db, event_id, status="pending", **over):
    f = {"id": f"tkt_{secrets.token_hex(5)}", "code": secrets.token_hex(4).upper(), "gateway_approved": None, "gateway_due_at": None, **over}
    await db.execute(
        "INSERT INTO tickets (id, event_id, code, status, price_cents, gateway_approved, gateway_due_at)"
        " VALUES (%(id)s,%(e)s,%(code)s,%(s)s,10000,%(gateway_approved)s,%(gateway_due_at)s)",
        {**f, "e": event_id, "s": status},
    )
    return f["id"]
