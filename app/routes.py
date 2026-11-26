from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app import auth, db
from app.web import render

router = APIRouter()


def _redirect(url: str) -> RedirectResponse:
    return RedirectResponse(url, status_code=303)


@router.get("/signup")
async def signup_form(request: Request):
    return render(request, "signup.html", await auth.current_user(request))


@router.post("/signup")
async def signup(request: Request, name: str = Form(""), email: str = Form(""), password: str = Form("")):
    name, email = name.strip(), email.strip().lower()
    error = None
    if not name or not email or not password or "@" not in email:
        error = "Preencha nome, e-mail válido e senha"
    async with db.pool.connection() as conn:
        if error is None:
            cur = await conn.execute("SELECT 1 FROM users WHERE email = %s", (email,))
            if await cur.fetchone():
                error = "E-mail já cadastrado"
        if error:
            return render(request, "signup.html", None, 422, error=error)
        user_id = auth.new_user_id()
        await conn.execute(
            "INSERT INTO users (id, name, email, password_hash, role) VALUES (%s,%s,%s,%s,'participant')",
            (user_id, name, email, auth.hash_password(password)),
        )
    request.session["user_id"] = user_id
    return _redirect("/")


@router.get("/login")
async def login_form(request: Request):
    return render(request, "login.html", await auth.current_user(request))


@router.post("/login")
async def login(request: Request, email: str = Form(""), password: str = Form("")):
    async with db.pool.connection() as conn:
        cur = await conn.execute(
            "SELECT id, role, password_hash FROM users WHERE email = %s", (email.strip().lower(),)
        )
        row = await cur.fetchone()
    if row is None or not auth.verify_password(password, row["password_hash"]):
        return render(request, "login.html", None, 401, error="E-mail ou senha inválidos")
    request.session["user_id"] = row["id"]
    return _redirect("/org/events" if row["role"] == "organizer" else "/")


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return _redirect("/")
