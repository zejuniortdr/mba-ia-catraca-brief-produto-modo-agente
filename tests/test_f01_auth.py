import pytest


@pytest.mark.anyio
async def test_signup_creates_participant_and_logs_in(client, db):
    # Act
    r = await client.post("/signup", data={"name": "Maria Nova", "email": "maria@x.com", "password": "pw"})
    home = await client.get("/")

    # Assert
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert "Maria Nova" in home.text
    cur = await db.execute("SELECT role FROM users WHERE email='maria@x.com'")
    assert (await cur.fetchone())["role"] == "participant"


@pytest.mark.anyio
async def test_signup_duplicate_email_422(client):
    # Arrange
    data = {"name": "A", "email": "dup@x.com", "password": "pw"}
    await client.post("/signup", data=data)
    client.cookies.clear()

    # Act
    r = await client.post("/signup", data=data)

    # Assert
    assert r.status_code == 422
    assert '<p class="error">E-mail já cadastrado</p>' in r.text


@pytest.mark.anyio
async def test_signup_invalid_fields_422(client):
    # Act
    r = await client.post("/signup", data={"name": "A", "email": "sem-arroba", "password": "pw"})

    # Assert
    assert r.status_code == 422


@pytest.mark.anyio
async def test_login_wrong_password_401(client):
    # Act
    r = await client.post("/login", data={"email": "org.a@catraca.local", "password": "errada"})

    # Assert
    assert r.status_code == 401
    assert "E-mail ou senha inválidos" in r.text


@pytest.mark.anyio
async def test_login_organizer_redirects_org(client):
    # Act
    r = await client.post("/login", data={"email": "org.a@catraca.local", "password": "catraca123"})

    # Assert
    assert r.status_code == 303 and r.headers["location"] == "/org/events"


@pytest.mark.anyio
async def test_login_participant_redirects_home(client):
    # Act
    r = await client.post("/login", data={"email": "participante@catraca.local", "password": "catraca123"})

    # Assert
    assert r.status_code == 303 and r.headers["location"] == "/"


@pytest.mark.anyio
async def test_logout_clears_session(participant):
    # Arrange
    assert "Participante Seed" in (await participant.get("/")).text

    # Act
    r = await participant.post("/logout")
    home = await participant.get("/")

    # Assert
    assert r.status_code == 303
    assert "Participante Seed" not in home.text


@pytest.mark.anyio
async def test_password_stored_hashed(client, db):
    # Act
    cur = await db.execute("SELECT password_hash FROM users WHERE email='participante@catraca.local'")
    h = (await cur.fetchone())["password_hash"]

    # Assert
    assert h.startswith("scrypt$") and "catraca123" not in h
