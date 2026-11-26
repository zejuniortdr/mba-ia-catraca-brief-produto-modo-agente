from psycopg import AsyncConnection


async def occupied_seats(conn: AsyncConnection, event_id: str) -> int:
    cur = await conn.execute(
        "SELECT count(*) AS n FROM tickets WHERE event_id = %s AND status IN ('pending','confirmed')",
        (event_id,),
    )
    return (await cur.fetchone())["n"]


async def available_seats(conn: AsyncConnection, event: dict) -> int:
    if event["status"] == "cancelled":
        return 0
    return max(0, event["capacity"] - await occupied_seats(conn, event["id"]))
