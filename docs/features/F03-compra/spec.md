# F03 — Vitrine e compra: spec técnica

PRD: F03-AC-1..10, XF-2, XF-3. Consome F01 (`require_user`, `current_user`, `get_conn`, `pool`, `templates`) e F02 (`list_on_sale`, `get_event`, `occupied_seats`, `available_seats`, filtro `brl`). Provê `purchase` e o gateway para F04–F07.

## Gateway simulado (`app/gateway.py`)

- `decide(card_number: str) -> tuple[bool, float]` pelos 4 últimos dígitos; atraso `random.uniform(lo, hi) * GATEWAY_DELAY_SCALE` (env, default `1.0`):
  - `0001` → aprovado, 2–5 s · `0002` → recusado, 2–5 s · `0003` → aprovado, 30–40 s · `0004` → recusado, 30–40 s · outro → recusado, 2–5 s.
- `schedule(ticket_id, approved, due_at)`: `asyncio.get_running_loop().create_task(_run(...))`; `_run` dorme `max(0, due_at - now)` e chama `apply_result`. Manter referências das tasks num `set` (evita GC) e descartar no `done_callback`.
- `apply_result(ticket_id, approved)`: conexão própria do `pool`; `UPDATE tickets SET status=%s WHERE id=%s AND status='pending'` (`confirmed` se aprovado, `declined` se não). **Esse `WHERE` é o que impede resposta tardia de sobrescrever `cancelled` (F06).**
- `reschedule_pending()`: no startup (o lifespan de F01 já chama se o módulo existir), agenda todos os `pending` com `gateway_due_at` gravado.
- A decisão (`gateway_approved`) e o prazo (`gateway_due_at`) ficam gravados no ingresso na compra, para o reagendamento após reinício.

## Serviço de compra (`app/purchases.py`)

- Exceções: `InvalidRequest`, `EventNotAvailable`, `SoldOut`.
- `CARD_RE = re.compile(r"^\d{16}$")`.
- `async def purchase(conn, event_id, card_number, *, user_id=None, buyer_email=None) -> dict` retorna `{"id","code","status","event_id"}`:
  1. `card_number` não casa `CARD_RE` → `InvalidRequest` (nada é criado).
  2. `async with conn.transaction():` `SELECT * FROM events WHERE id=%s FOR UPDATE`.
  3. Inexistente ou `status != 'published'` → `EventNotAvailable`.
  4. `occupied_seats(conn, event_id) >= capacity` → `SoldOut`.
  5. `approved, delay = decide(card_number)`; insere ticket `tkt_<10 hex>`, `code` 8 chars de `string.ascii_uppercase + string.digits` via `secrets.choice`, `status='pending'`, `price_cents = event.price_cents`, `user_id`, `buyer_email`, `gateway_approved`, `gateway_due_at = now + delay`.
  6. Colisão de `code` (`UniqueViolation`) → nova tentativa (até 5) dentro de um savepoint.
  7. Depois do commit: `schedule(id, approved, due_at)`.
- Ordem das verificações é a do contrato da API de parceiros (corpo → evento → vaga). A validação de e-mail é da F04.

## Rotas (`app/shop.py`) e templates `app/templates/shop/`

- `GET /` (vitrine, público): `list_on_sale`; cada evento `<li data-event-id="{id}"><a href="/events/{id}">{name}</a> — {data} — {venue} — {price|brl}</li>`.
- `GET /events/{id}` (público): 404 se não `published`. Mostra nome, data, local, preço. Se `available_seats == 0`: `<p id="sold-out">Ingressos esgotados</p>` no lugar do formulário. Senão `<form id="buy-form" method="post" action="/events/{id}/buy">` com `card_number` (visitante vê o formulário; o POST pede login).
- `POST /events/{id}/buy` (`require_user`; visitante → 303 `/login`): chama `purchase(user_id=user.id, buyer_email=user.email)`.
  - sucesso → 303 `/me/tickets`
  - `InvalidRequest` → 422 re-render com `<p class="error">Número do cartão deve ter 16 dígitos</p>`
  - `SoldOut` → 409 re-render com `<p id="sold-out">Ingressos esgotados</p>`
  - `EventNotAvailable` → 404.
- `GET /me/tickets` (`require_user`): ingressos com `user_id` do usuário, mais recentes primeiro: `<tr data-ticket-id="{id}"><td class="event">{event.name}</td><td class="status">{rótulo}</td><td class="code">{code}</td></tr>`. Rótulos: `pending→pendente`, `confirmed→confirmado`, `declined→recusado`, `cancelled→cancelado`, `refunded→estornado` (dict `STATUS_LABELS` em `app/web.py`, reutilizado por outras features).

## Lifespan
F01 já chama `reschedule_pending()` se `app.gateway` existir; confirmar que funciona.
