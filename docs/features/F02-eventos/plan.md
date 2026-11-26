# F02 — Eventos do organizador: plano

Spec: `spec.md`. Branch `feat/f02-eventos`. Commit ao fim de cada etapa. Testes em `tests/test_f02_*.py`, usando fixtures `org_a`, `org_b`, `participant`, `client` de F01.

1. **Parsing do formulário.** `tests/test_f02_form.py`: `test_parse_valid` (price `100,00` → 10000), `test_parse_price_variants` (`100`, `100.00`, `150,50` → 15050), `test_capacity_zero_rejected`, `test_price_zero_rejected`, `test_past_date_rejected` (mensagem `Data de início precisa estar no futuro`), `test_missing_name_rejected`, `test_starts_at_offset_minus3` (`2026-12-05T21:00` → `datetime(2026,12,5,21,0,tzinfo=-03:00)`). Implementar `parse_event_form` e `format_brl` (`test_format_brl`).
2. **Criar e listar.** `tests/test_f02_crud.py`: `test_create_event_draft` (303 para `/org/events/evt_...`; status `draft`), `test_create_past_date_422`, `test_org_list_only_own` (A cria, B lista: sem `data-event-id` de A), `test_participant_seed_forbidden_org_events` (403) e `test_org_a_seed_access_org_events` (200) para XF-1.
3. **Página de gestão e isolamento.** `test_manage_page_markers` (`id="event-name"`, `id="edit-form"`, `id="publish-form"`), `test_other_org_manage_404_no_data` (B em evento de A → 404, corpo sem o nome), `test_other_org_post_edit_404`, `test_other_org_post_publish_404`.
4. **Publicação e on-sale.** `tests/test_f02_publish.py`: `test_draft_not_on_sale`, `test_publish_then_on_sale`, `test_publish_twice_409`.
5. **Vagas.** `tests/test_f02_seats.py` (insere tickets direto por SQL): `test_occupied_counts_pending_confirmed` (pending+confirmed contam; declined/cancelled/refunded não), `test_available_cancelled_zero`.
6. **Edição com lock.** `tests/test_f02_edit.py`: `test_edit_capacity_below_occupied_422` (2 tickets pending+confirmed, capacity 1 → 422 com `Lotação não pode ser menor que as vagas ocupadas`), `test_edit_capacity_increase_ok`, `test_edit_past_date_422`, `test_edit_price_ok`.
7. `./scripts/gates.sh` verde, push, PR.
