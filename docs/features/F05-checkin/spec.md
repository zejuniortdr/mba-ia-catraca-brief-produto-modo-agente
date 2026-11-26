# F05 — Check-in: spec técnica

PRD: F05-AC-1..6, XF-6, XF-7, XF-8. Consome F02 (`get_owned_event`, `manage_context`, `render_manage`, `org/manage.html` com include de `org/_checkin.html`), F03 (tickets e status) e F04 (`GET /api/partner/tickets/{id}` lê `checked_in`). Wave paralela W5: não depende de F06/F07; status `cancelled` do evento é preparado por SQL nos testes.

## Decisões

**Módulo:** `app/checkin.py` (router + regra), template `app/templates/org/_checkin.html`.

**Regra** `async def check_in(conn, event, code: str) -> str`, numa transação, código normalizado `code.strip().upper()`. Primeira condição verdadeira, nesta ordem:
1. `SELECT ... FROM tickets WHERE code=%s AND event_id=%s FOR UPDATE` não encontra → `Ingresso inválido para este evento`
2. `event["status"] == "cancelled"` → `Evento cancelado`
3. `ticket["status"] != "confirmed"` → `Ingresso não confirmado`
4. `ticket["checked_in"]` → `Ingresso já utilizado`
5. `UPDATE tickets SET checked_in=true WHERE id=%s` → `Entrada liberada`

Mensagens como constantes no módulo, copiadas literalmente.

**Rota:** `POST /org/events/{id}/checkin` (`require_organizer`), form `code`. Evento inexistente ou de outro organizador → 404 (mesmo `404.html` de F02, sem dados). Sucesso → `ctx = await manage_context(...)`; `ctx["checkin_result"] = msg`; `render_manage(ctx)` com 200. O `FOR UPDATE` no ingresso impede dois check-ins simultâneos do mesmo código.

**Parcial** `org/_checkin.html`: `<form id="checkin-form" method="post" action="/org/events/{{ event.id }}/checkin"><input name="code"> <button>Check-in</button></form>` e, se `checkin_result`, `<p id="checkin-result">{{ checkin_result }}</p>`. O campo fica disponível mesmo com evento cancelado (vale a lista de R10).
