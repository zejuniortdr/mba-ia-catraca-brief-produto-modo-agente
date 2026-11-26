import pytest

from app import db as app_db
from app.seed import seed


@pytest.mark.anyio
async def test_seed_twice_no_duplicates(running_app, db):
    # Act
    async with app_db.pool.connection() as conn:
        await seed(conn)
        await seed(conn)
    cur = await db.execute("SELECT email, role FROM users ORDER BY email")
    rows = await cur.fetchall()

    # Assert
    assert [(r["email"], r["role"]) for r in rows] == [
        ("org.a@catraca.local", "organizer"),
        ("org.b@catraca.local", "organizer"),
        ("participante@catraca.local", "participant"),
    ]
