# F01 — Fundação: plano

Spec: `spec.md`. Branch `feat/f01-fundacao`. Commit ao fim de cada etapa.

1. **Esqueleto e harness.** `requirements.txt`, `pyproject.toml`, `Dockerfile` (`python:3.12-slim`, `pip install --no-cache-dir -r requirements.txt`, `COPY . .`, `CMD uvicorn app.main:app --host 0.0.0.0 --port 8000`), `.dockerignore` (`.git`, `.superpowers`, `__pycache__`), `compose.yml`, `scripts/{up,down,gates}.sh` (executáveis), `app/main.py` com `/healthz`, `app/db.py`, `app/schema.sql`. Teste `tests/test_f01_health.py::test_healthz_ok` (200 `{"ok": true}`). Verificar: `./scripts/gates.sh` verde; `./scripts/up.sh` e `curl -s localhost:8000/healthz`; `./scripts/down.sh` e `docker ps` sem containers do projeto.
2. **Schema.** `tests/test_f01_schema.py`: `test_schema_has_tables` (users, events, tickets existem), `test_event_capacity_check` (insert capacity 0 falha), `test_ticket_status_check` (status `foo` falha), `test_ticket_code_unique`.
3. **Seed idempotente.** `tests/test_f01_seed.py::test_seed_twice_no_duplicates` (rodar `seed` 2× → 3 usuários, papéis corretos).
4. **Signup/login/logout.** `tests/test_f01_auth.py`: `test_signup_creates_participant_and_logs_in` (303 `/`, depois `/` mostra nome), `test_signup_duplicate_email_422`, `test_login_wrong_password_401` (contém `E-mail ou senha inválidos`), `test_login_organizer_redirects_org`, `test_login_participant_redirects_home`, `test_logout_clears_session`, `test_password_stored_hashed` (hash começa com `scrypt$` e não contém a senha).
5. **Guarda de papel.** `tests/test_f01_access.py`: `test_visitor_org_redirects_login` (303 `/login`), `test_participant_org_forbidden` (403), `test_organizer_org_ok` (200).
6. **Layout base** com navegação por papel; verificação manual `./scripts/up.sh`, abrir `/login`.
7. `./scripts/gates.sh` verde, push, PR.
