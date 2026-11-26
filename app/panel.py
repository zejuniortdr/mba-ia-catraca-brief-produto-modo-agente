from psycopg import AsyncConnection

from app.seats import available_seats


async def panel_metrics(conn: AsyncConnection, event: dict) -> dict:
    cur = await conn.execute(
        """select
          count(*) filter (where status='confirmed')                      as confirmed,
          count(*) filter (where status='pending')                        as pending,
          count(*) filter (where status='confirmed' and checked_in)       as checkins,
          count(*) filter (where status='refunded')                       as refunded,
          coalesce(sum(price_cents) filter (where status='confirmed'), 0) as revenue_cents
        from tickets where event_id = %s""",
        (event["id"],),
    )
    return {**await cur.fetchone(), "available": await available_seats(conn, event)}
