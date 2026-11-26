# F05 — Check-in: plano

Spec: `spec.md`. Branch `feat/f05-checkin` (wave paralela W5). **Primeiro commit e push logo na etapa 1.** Testes em `tests/test_f05_checkin.py`; ingressos preparados por `purchase` (F03) ou por SQL.

1. **Regra.** `test_unknown_code_invalid`, `test_cancelled_event_message` (evento `cancelled` por SQL + ingresso do próprio evento → `Evento cancelado`), `test_not_confirmed` (parametrize pending, declined, cancelled, refunded → `Ingresso não confirmado`), `test_already_used`, `test_entry_allowed_marks_checked_in`, `test_other_event_code_invalid_even_if_cancelled` (ordem: código de outro evento em evento cancelado → inválido), `test_code_normalized` (minúsculo com espaços funciona).
2. **Rota e parcial.** `test_checkin_page_has_form` (`id="checkin-form"` na página de gestão), `test_checkin_post_shows_message` (`id="checkin-result">Entrada liberada`), `test_other_org_checkin_404` (B em evento de A → 404, ingresso não marcado) (XF-6).
3. **Integração.** `test_web_ticket_flow` (XF-7: compra vitrine 0001 confirmada → `Entrada liberada`; compra pendente 0003 → `Ingresso não confirmado`; código de ingresso de outro evento → inválido), `test_api_ticket_checkin_reflects_in_api` (XF-8: compra pela API, confirmar, check-in, `GET /api/partner/tickets/{id}` → `checkedIn: true`).
4. `./scripts/gates.sh` verde, push, PR.
