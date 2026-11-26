# F06 — Cancelamento: contrato

## Pré-requisitos
- Clone limpo do commit indicado, `WEB_PORT` livre, `./scripts/up.sh` (atrasos reais).
- Receitas: `docs/features/_eval-recipes.md`. Como A: evento E3 (lotação 5, `price=50,00`) publicado; rascunho D.

## Itens

| Item | Como verificar | Esperado |
|---|---|---|
| CTR-F06-1 | Página de gestão de E3 | contém `id="cancel-form"` |
| CTR-F06-2 | `POST /org/events/$D/cancel` (rascunho) | `409`, `Só evento publicado pode ser cancelado`; D segue `draft` |
| CTR-F06-3 | Como B: `POST /org/events/$E3/cancel` | `404`, corpo sem o nome de E3; E3 segue `published` |
| CTR-F06-4 | API: compra T5 (0003) e logo T6 (0001); participante da seed compra na vitrine TW (0001); `sleep 6`; `GET tickets/$T6` | T6 `confirmed`, T5 `pending` |
| CTR-F06-5 | Antes de 30 s da compra de T5: cancelar E3; medir até `GET tickets/$T6` = `refunded` e `GET tickets/$T5` = `cancelled` | `303`; ambos em ≤ 10 s |
| CTR-F06-6 | `curl $WEB/`; `GET /api/partner/events` | E3 ausente nos dois |
| CTR-F06-7 | Compra API em E3 | `404` `{"error":"event_not_available"}` |
| CTR-F06-8 | Participante da seed: `GET /events/$E3`; `POST /events/$E3/buy` (0001) | `404`; `404`, nenhum ticket novo |
| CTR-F06-9 | Participante da seed: `GET /me/tickets` | linha de TW com `estornado` |
| CTR-F06-10 | `sleep` até 45 s após a compra de T5; `GET tickets/$T5` | continua `"status":"cancelled"` |
| CTR-F06-11 | Página de gestão de E3 | `id="event-status">cancelado`, `id="event-cancelled"`; **sem** `edit-form`, `publish-form`, `cancel-form` |
| CTR-F06-12 | `POST /org/events/$E3/edit` (campos válidos); `POST .../publish`; `POST .../cancel` | `409` nos três; `psql` E3 `cancelled`, campos inalterados |
| CTR-F06-13 | `psql -At -c "select status, count(*) from tickets where event_id='$E3' group by 1"` | só `refunded` e `cancelled` |
| CTR-F06-14 | `./scripts/gates.sh tests/test_f06_cancel.py -v` | `test_late_gateway_does_not_change_cancelled` e `test_cancel_during_burst_never_leaves_pending` passam |
| CTR-F06-15 | `./scripts/gates.sh` | exit 0 |

## Mapeamento PRD → itens

| Critério | Itens |
|---|---|
| F06-AC-1 | CTR-F06-2, CTR-F06-5, CTR-F06-12 |
| F06-AC-2 | CTR-F06-6, CTR-F06-7, CTR-F06-8 |
| F06-AC-3 | CTR-F06-5, CTR-F06-13 |
| F06-AC-4 | CTR-F06-10, CTR-F06-14 |
| F06-AC-5 | CTR-F06-11, CTR-F06-12 |
| F06-AC-6 | CTR-F06-3 |
| XF-9 (F02→F06) | CTR-F06-1, CTR-F06-6, CTR-F06-11, CTR-F06-12 |
| XF-10 (F03→F06) | CTR-F06-6, CTR-F06-8, CTR-F06-9 |
| XF-11 (F04→F06) | CTR-F06-5, CTR-F06-7, CTR-F06-10 |
