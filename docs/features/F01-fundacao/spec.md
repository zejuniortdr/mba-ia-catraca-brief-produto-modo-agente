# F01 — Fundação: spec técnica

PRD: F01 (F01-AC-1..7). Provê para todas as outras features.

## Decisões

**Stack e dependências** (`requirements.txt`, uma lista só, imagem única para app e testes): `fastapi`, `uvicorn[standard]`, `jinja2`, `python-multipart`, `psycopg[binary]`, `psycopg_pool`, `itsdangerous`, `httpx`, `pytest`, `ruff`. Python 3.12 (`python:3.12-slim`).

**Docker Compose** (`compose.yml`, sem `name:` fixo — cada worktree vira projeto próprio):
- `db`: `postgres:16-alpine`, `POSTGRES_USER=catraca`, `POSTGRES_PASSWORD=catraca`, `POSTGRES_DB=catraca`, volume nomeado `pgdata`, healthcheck `pg_isready -U catraca`. Sem porta no host.
- `app`: build `.`, `ports: ["${WEB_PORT:-8000}:8000"]`, env `DATABASE_URL=postgresql://catraca:catraca@db:5432/catraca`, `PARTNER_API_KEY=${PARTNER_API_KEY:-catraca-parceiro-2026}`, `SESSION_SECRET=${SESSION_SECRET:-dev-secret-catraca}`, `GATEWAY_DELAY_SCALE=1.0`; `depends_on: db: condition: service_healthy`; healthcheck `python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/healthz')"`.
- `test`: mesma imagem, `profiles: ["test"]`, env `DATABASE_URL=postgresql://catraca:catraca@db:5432/catraca`, `TEST_DATABASE_URL=postgresql://catraca:catraca@db:5432/catraca_test`, `GATEWAY_DELAY_SCALE=0.01`, `depends_on db healthy`, `entrypoint: ["sh","-c","ruff check . && pytest -q \"$@\"","--"]`.

**Scripts** (bash, `set -euo pipefail`, `cd` para a raiz do repo):
- `scripts/up.sh`: `docker compose up -d --build --wait` e imprime `Catraca em http://localhost:${WEB_PORT:-8000}`.
- `scripts/down.sh`: `docker compose down --remove-orphans` e `docker compose -p "$(basename "$PWD")-gates" down -v --remove-orphans`. Mantém o volume do produto (subir de novo prova a seed idempotente).
- `scripts/gates.sh`: projeto separado `-p "$(basename "$PWD")-gates"`; `trap` que faz `down -v` ao sair; `docker compose -p ... --profile test build test` e `docker compose -p ... --profile test run --rm test "$@"`. Exit code do pytest propaga.

**Banco** (`app/db.py`): `pool = AsyncConnectionPool(DATABASE_URL, min_size=1, max_size=20, open=False, kwargs={"row_factory": dict_row})`; `get_conn()` dependency (`async with pool.connection() as conn: yield conn`); `apply_schema()` executa `app/schema.sql` (idempotente com `IF NOT EXISTS`). Schema completo do plano mestre (users, events, tickets) é criado aqui.

**App** (`app/main.py`): `create_app()` com lifespan: abre pool → `apply_schema()` → `seed()` → `await gateway.reschedule_pending()` só se `app.gateway` existir (F03 liga; aqui usar `importlib.util.find_spec`). `app = create_app()`. `SessionMiddleware(secret_key=SESSION_SECRET, same_site="lax")`. `GET /healthz` → `{"ok": true}`. Templates `Jinja2Templates(directory="app/templates")` exportado como `templates` em `app/web.py`.

**Auth** (`app/auth.py`):
- Senha: `hashlib.scrypt(pw, salt=os.urandom(16), n=2**14, r=8, p=1)`; armazenar `scrypt$<salt_hex>$<hash_hex>`; comparar com `hmac.compare_digest`.
- Sessão guarda só `user_id`. `current_user(request)` busca no banco.
- `require_user`: sem login → `HTTPException(303, headers={"Location": "/login"})`. `require_organizer`: sem login → 303 `/login`; participante → 403 (página "Acesso restrito a organizadores").
- IDs: `usr_<10 hex>` (`secrets.token_hex(5)`).

**Rotas F01:**
- `GET /signup` form `name`, `email`, `password`. `POST /signup`: valida campos não vazios, e-mail com `@`; e-mail existente → 422 com `<p class="error">E-mail já cadastrado</p>`; sucesso → cria participante, loga, 303 `/`.
- `GET /login` form `email`, `password`. `POST /login`: erro → 401 com `<p class="error">E-mail ou senha inválidos</p>`; sucesso → 303 para `/org/events` (organizador) ou `/` (participante).
- `POST /logout` → limpa sessão, 303 `/`.
- `GET /org/events` placeholder protegido por `require_organizer` (F02 substitui) para provar o guard.

**Layout** `app/templates/base.html`: nav com links Vitrine (`/`), Meus ingressos (participante), Área do organizador (organizador), Entrar/Cadastrar (visitante) ou nome + botão Sair (form POST `/logout`). Bloco `{% block content %}`. Sem CSS além do mínimo.

**Seed** (`app/seed.py`, `async def seed(conn)`): upsert por e-mail (`ON CONFLICT (email) DO UPDATE SET name=..., role=..., password_hash=...`) para as três contas do plano mestre, senha `catraca123`.

**Testes** (`tests/conftest.py`): cria `catraca_test` se não existir (conectando no `DATABASE_URL`), aponta `app.db` para `TEST_DATABASE_URL`, aplica schema, `TRUNCATE users, events, tickets CASCADE` antes de cada teste e roda seed. Fixture `client` = `httpx.AsyncClient(transport=ASGITransport(app), base_url="http://test")` com o lifespan executado via `async with app.router.lifespan_context(app)`. Fixtures `org_a`, `org_b`, `participant`: clients já logados. Testes async via plugin `anyio` (`@pytest.mark.anyio`, fixture `anyio_backend` → `"asyncio"`). `pyproject.toml` com config de ruff (`line-length = 110`) e pytest (`testpaths = ["tests"]`).

## Fora desta feature
Eventos, compra, API de parceiros (F02+).
