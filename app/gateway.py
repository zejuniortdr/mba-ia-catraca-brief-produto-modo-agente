import asyncio
import os
import random
from datetime import UTC, datetime

from app import db

# last 4 digits -> (approved, (min_s, max_s)); anything else is declined in 2-5 s
_RULES = {
    "0001": (True, (2, 5)),
    "0002": (False, (2, 5)),
    "0003": (True, (30, 40)),
    "0004": (False, (30, 40)),
}
_tasks: set[asyncio.Task] = set()


def decide(card_number: str) -> tuple[bool, float]:
    approved, (lo, hi) = _RULES.get(card_number[-4:], (False, (2, 5)))
    return approved, random.uniform(lo, hi) * float(os.environ.get("GATEWAY_DELAY_SCALE", "1.0"))


async def apply_result(ticket_id: str, approved: bool) -> None:
    """Only a pending ticket changes; a late answer never overwrites cancelled/refunded. Missing ticket is a no-op."""
    async with db.pool.connection() as conn:
        await conn.execute(
            "UPDATE tickets SET status=%s WHERE id=%s AND status='pending'",
            ("confirmed" if approved else "declined", ticket_id),
        )


async def _run(ticket_id: str, approved: bool, due_at: datetime) -> None:
    await asyncio.sleep(max(0.0, (due_at - datetime.now(UTC)).total_seconds()))
    await apply_result(ticket_id, approved)


def schedule(ticket_id: str, approved: bool, due_at: datetime) -> None:
    task = asyncio.get_running_loop().create_task(_run(ticket_id, approved, due_at))
    _tasks.add(task)  # keep a reference so it is not garbage collected
    task.add_done_callback(_tasks.discard)


async def reschedule_pending() -> None:
    async with db.pool.connection() as conn:
        cur = await conn.execute(
            "SELECT id, gateway_approved, gateway_due_at FROM tickets"
            " WHERE status='pending' AND gateway_due_at IS NOT NULL"
        )
        rows = await cur.fetchall()
    for r in rows:
        schedule(r["id"], bool(r["gateway_approved"]), r["gateway_due_at"])


async def cancel_pending_tasks() -> None:
    """Shutdown hook: stop in-flight gateway tasks (they would touch a closed pool / next test's DB)."""
    tasks = list(_tasks)
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
