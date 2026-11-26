# F06 — Cancelamento: spec técnica

PRD: F06-AC-1..6, XF-9, XF-10, XF-11. Consome F02 (`get_owned_event`, `manage_context`, `render_manage`, rotas de edição/publicação, `list_on_sale`), F03 (`purchase`, `apply_result`, "Meus ingressos") e F04 (compra e consulta pela API). Wave paralela W5: não depende de F05/F07.

## Decisões

**Módulo:** `app/cancellation.py` (router), template `app/templates/org/_cancel.html`.

**Rota** `POST /org/events/{id}/cancel` (`require_organizer`), numa transação:
1. `SELECT * FROM events WHERE id=%s AND organizer_id=%s FOR UPDATE` → não encontrado → 404 (`404.html`, sem dados).
2. `status != 'published'` → 409, re-render com `<p class="error">Só evento publicado pode ser cancelado</p>` (rascunho não cancela; cancelado não "re-cancela").
3. `UPDATE events SET status='cancelled' WHERE id=%s`.
4. `UPDATE tickets SET status = CASE status WHEN 'confirmed' THEN 'refunded' ELSE 'cancelled' END WHERE event_id=%s AND status IN ('pending','confirmed')`.
5. Commit → 303 para a página de gestão.

A transição é síncrona (bem dentro dos 10 s de R11). O mesmo `FOR UPDATE` serializa com compras em andamento (`purchase` trava a mesma linha), então nenhuma compra entra depois do cancelamento. Resposta tardia do gateway não muda nada porque `apply_result` só atualiza `status='pending'` (F03) — esta feature tem teste que prova isso.

**Bloqueio de edição e republicação** (alteração em `app/events.py` de F02):
- `POST /org/events/{id}/edit` com evento `cancelled` → 409, re-render com `<p class="error">Evento cancelado não pode ser editado</p>`, sem alterar nada. A checagem acontece depois do `FOR UPDATE` já existente.
- `POST .../publish` já só aceita `draft` (F02) → 409.
- `org/manage.html`: `edit-form` e `publish-form` só aparecem se `event.status != 'cancelled'`.

**Parcial** `org/_cancel.html`: se `event.status == 'published'`, `<form id="cancel-form" method="post" action="/org/events/{{ event.id }}/cancel" onsubmit="return confirm('Cancelar o evento? Não há volta.')"><button>Cancelar evento</button></form>`; se `cancelled`, `<p id="event-cancelled">Este evento foi cancelado.</p>`.

**Já coberto por outras features e só verificado aqui:** saída da vitrine e da API (`list_on_sale` filtra `published`), compra 404 (`purchase` exige `published`), vagas 0 (`available_seats`).
