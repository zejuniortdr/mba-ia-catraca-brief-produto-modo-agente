# F07 — Painel: contrato

## Pré-requisitos
- Clone limpo do commit indicado, `WEB_PORT` livre, `./scripts/up.sh` (atrasos reais).
- Receitas: `docs/features/_eval-recipes.md` (a de painel imprime `data-metric`). Como A: evento E1 (lotação 2, `price=100,00`) publicado.

## Itens

| Item | Como verificar | Esperado |
|---|---|---|
| CTR-F07-1 | Página de gestão de E1 | contém os rótulos `Confirmados`, `Pendentes`, `Check-ins`, `Vagas disponíveis`, `Receita`, `Estornados`; métricas `confirmed 0, pending 0, checkins 0, available 2, revenue R$ 0,00, refunded 0` |
| CTR-F07-2 | Participante da seed compra E1 na vitrine (0001); API compra E1 (0003); painel imediatamente | `pending 2`, `available 0`, `confirmed 0` |
| CTR-F07-3 | `sleep 6`; painel | `confirmed 1`, `pending 1`, `revenue R$ 100,00` |
| CTR-F07-4 | `sleep 40`; A edita E1 com `price=150,00`, `capacity=3`; painel | `confirmed 2`, `pending 0`, `available 1`, `revenue R$ 200,00` (preço antigo mantido) |
| CTR-F07-5 | API compra E1 (0001); `sleep 6`; painel | `confirmed 3`, `available 0`, `revenue R$ 350,00` |
| CTR-F07-6 | `psql -c "update tickets set checked_in=true where id=(select id from tickets where event_id='$E1' and status='confirmed' limit 1)"`; painel | `checkins 1`, `confirmed 3` |
| CTR-F07-7 | Evento E9 (lotação 5, `price=10,00`) publicado; 2 compras API (0001) e 1 (0002); `sleep 6`; `psql` muda um confirmado para `refunded`; painel | `confirmed 1`, `refunded 1`, `revenue R$ 10,00` (estorno e recusa fora da receita) |
| CTR-F07-8 | `psql -c "update events set status='cancelled' where id='$E9'"`; painel | `available 0` |
| CTR-F07-9 | Como B: `GET /org/events/$E1` | `404`; corpo sem `id="panel"` e sem `R$ 350,00` |
| CTR-F07-10 | `./scripts/gates.sh` | exit 0, inclui `test_web_and_api_purchases_count` |

## Mapeamento PRD → itens

| Critério | Itens |
|---|---|
| F07-AC-1 | CTR-F07-1, CTR-F07-6 |
| F07-AC-2 | CTR-F07-4, CTR-F07-5 |
| F07-AC-3 | CTR-F07-7 |
| F07-AC-4 | CTR-F07-8 |
| XF-12 (F02→F07) | CTR-F07-1, CTR-F07-4, CTR-F07-9 |
| XF-13 (F03→F07) | CTR-F07-2, CTR-F07-3, CTR-F07-4 |
| XF-14 (F04→F07) | CTR-F07-2, CTR-F07-5 |
