# F04 — API de parceiros: plano

Spec: `spec.md`. Branch `feat/f04-api-parceiros`. Commit ao fim de cada etapa. Testes em `tests/test_f04_api.py`; header `X-Api-Key` igual ao `PARTNER_API_KEY` do ambiente de teste.

1. **Chave.** `test_unauthorized_without_key` e `test_unauthorized_wrong_key` para as 3 rotas (parametrize) → 401 `{"error":"unauthorized"}`; `test_unauthorized_before_body_validation` (sem chave + corpo inválido → 401).
2. **Listagem (XF-4).** `test_list_only_published` (rascunho fora; publicado com `availableSeats == capacity`, `priceCents == 10000`; cancelado por SQL fora), `test_list_fields_exact` (chaves exatamente `{"id","name","startsAt","priceCents","availableSeats"}`; `startsAt` termina em `-03:00`).
3. **Compra.** `test_purchase_202_pending` (chaves exatas `ticketId, code, status`), `test_invalid_body_422` (parametrize: corpo vazio, não-JSON, sem `buyerEmail`, e-mail `ana@`, `cardNumber` `123`, `cardNumber` inteiro) → `{"error":"invalid_request"}`, `test_error_order_invalid_before_not_found` (evento inexistente + cartão `123` → 422), `test_event_not_available_404` (inexistente, rascunho, cancelado), `test_not_found_before_sold_out` (rascunho lotado → 404), `test_sold_out_409`.
4. **Rajada (R07).** `test_burst_30_capacity_5`: 5 rodadas, evento novo lotação 5 em cada, 30 POSTs simultâneos (`asyncio.gather` no client ASGI) → `Counter` de status `{202: 5, 409: 25}`.
5. **Consulta (XF-5).** `test_ticket_lookup_fields` (chaves exatas, `checkedIn` false), `test_ticket_not_found_404`, `test_web_ticket_visible_in_api` (compra pela vitrine com participante → GET pela API retorna o mesmo `code`), `test_api_sellout_shows_sold_out_on_showcase` (lotação 1, compra API → `/events/{id}` contém `Ingressos esgotados`), `test_declined_frees_seat` (cartão 0004 com scale de teste → `declined`; `availableSeats` volta).
6. `./scripts/gates.sh` verde, push, PR.
