from app.auth import hash_password, new_user_id

SEED_USERS = [
    ("Organizador A", "org.a@catraca.local", "organizer"),
    ("Organizador B", "org.b@catraca.local", "organizer"),
    ("Participante Seed", "participante@catraca.local", "participant"),
]


async def seed(conn) -> None:
    for name, email, role in SEED_USERS:
        await conn.execute(
            "INSERT INTO users (id, name, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)"
            " ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name, role = EXCLUDED.role,"
            " password_hash = EXCLUDED.password_hash",
            (new_user_id(), name, email, hash_password("catraca123"), role),
        )
