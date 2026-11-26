# F06 — Cancelamento: plano

Spec: `spec.md`. Branch `feat/f06-cancelamento` (wave paralela W5). **Primeiro commit e push logo na etapa 1.** Testes em `tests/test_f06_cancel.py` (scale de teste 0.01: 0003 responde em 0,3–0,4 s).

1. **Cancelamento e transições.** `test_cancel_published` (303; evento `cancelled`), `test_cancel_draft_409`, `test_cancel_twice_409`, `test_cancel_transitions` (confirmed → refunded, pending → cancelled, declined intocado), `test_other_org_cancel_404` (B em evento de A → 404, evento intacto).
2. **Resposta tardia.** `test_late_gateway_does_not_change_cancelled`: compra 0003 (pendente), cancela, aguarda > 0,5 s → continua `cancelled`; `test_late_gateway_approved_before_cancel_becomes_refunded` (0001 confirma, depois cancela → `refunded`).
3. **Bloqueio.** `test_edit_cancelled_409` (nada muda), `test_publish_cancelled_409`, `test_manage_page_cancelled_no_forms` (sem `edit-form`, `publish-form`, `cancel-form`; com `id="event-cancelled"`).
4. **Integração.** `test_cancelled_out_of_showcase_and_api` (XF-9/XF-10/XF-11: vitrine e `GET /api/partner/events` sem o evento; `GET /events/{id}` 404; compra web 404; compra API 404 `event_not_available`), `test_my_tickets_shows_refunded_and_cancelled` (XF-10: participante com 1 confirmado e 1 pendente → `estornado` e `cancelado`), `test_api_tickets_after_cancel` (XF-11: `GET /api/partner/tickets/{id}` → `refunded`/`cancelled`).
5. **Concorrência.** `test_cancel_during_burst_never_leaves_pending`: 20 compras API simultâneas + cancelamento simultâneo → ao final nenhum ingresso do evento em `pending` ou `confirmed`.
6. `./scripts/gates.sh` verde, push, PR.
