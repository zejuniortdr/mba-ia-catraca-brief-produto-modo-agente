import hashlib
import hmac
import os
import secrets

from fastapi import HTTPException, Request

from app import db


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    h = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${h.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, h = stored.split("$")
        calc = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1)
    except ValueError:
        return False
    return hmac.compare_digest(calc.hex(), h)


def new_user_id() -> str:
    return f"usr_{secrets.token_hex(5)}"


async def current_user(request: Request) -> dict | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    async with db.pool.connection() as conn:
        cur = await conn.execute("SELECT id, name, email, role FROM users WHERE id = %s", (user_id,))
        return await cur.fetchone()


async def require_user(request: Request) -> dict:
    user = await current_user(request)
    if user is None:
        raise HTTPException(303, headers={"Location": "/login"})
    return user


async def require_organizer(request: Request) -> dict:
    user = await require_user(request)
    if user["role"] != "organizer":
        raise HTTPException(403, detail="Acesso restrito a organizadores")
    return user
