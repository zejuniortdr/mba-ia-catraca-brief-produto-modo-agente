# F04 — API de parceiros: spec técnica

PRD: F04-AC-1..7, XF-4, XF-5. Consome F02 (`list_on_sale`, `available_seats`, `get_event`) e F03 (`purchase`, exceções, tabela `tickets`). Contrato fixo do enunciado, copiado literalmente.

## Decisões

**Módulo:** `app/partner_api.py` com `APIRouter(prefix="/api/partner")`, incluído em `create_app()`.

**Autenticação:** dependency `require_partner_key(request)`: `X-Api-Key` ausente ou diferente de `PARTNER_API_KEY` (comparação `hmac.compare_digest`) → `JSONResponse(401, {"error":"unauthorized"})`. Aplicada nas três rotas, antes de qualquer outra validação (inclusive do corpo). Implementar levantando uma exceção própria tratada por exception handler, para o 401 vir antes da validação do FastAPI.

**Respostas JSON exatas** (sem campos extras nos erros):
- `GET /api/partner/events` → 200, lista de `{"id","name","startsAt","priceCents","availableSeats"}`; `startsAt` = `starts_at.astimezone(-03:00).isoformat()` (ex.: `2026-12-05T21:00:00-03:00`); `availableSeats = available_seats(conn, event)`.
- `POST /api/partner/events/{eventId}/purchases` → 202 `{"ticketId","code","status":"pending"}`.
- `GET /api/partner/tickets/{ticketId}` → 200 `{"ticketId","code","eventId","status","checkedIn"}`; inexistente → 404 `{"error":"ticket_not_found"}`. Vale para ingresso de qualquer canal.

**Validação da compra, nesta ordem** (depois da chave):
1. Corpo: ler `await request.body()`, `json.loads`; não é objeto JSON, `buyerEmail` não é string que casa `^[^@\s]+@[^@\s]+\.[^@\s]+$`, ou `cardNumber` não é string que casa `^\d{16}$` → 422 `{"error":"invalid_request"}`. **Não** declarar modelo Pydantic no parâmetro (o 422 padrão do FastAPI tem outro formato).
2. `purchase(conn, eventId, cardNumber, buyer_email=buyerEmail)` (sem `user_id`): `EventNotAvailable` → 404 `{"error":"event_not_available"}`; `SoldOut` → 409 `{"error":"sold_out"}`; `InvalidRequest` (não deve ocorrer após o passo 1) → 422.

**Concorrência:** nada novo — o `FOR UPDATE` de `purchase` garante R07. Uvicorn com 1 worker; pool de 20 conexões (rajada de 30 espera no pool).
