# F04 — API de parceiros: contrato

## Pré-requisitos
- Clone limpo do commit indicado, `WEB_PORT` livre, `./scripts/up.sh` (atrasos reais).
- Receitas: `docs/features/_eval-recipes.md`. Como A: evento E (lotação 2, `price=100,00`) publicado; rascunho D.

## Itens

| Item | Como verificar | Esperado |
|---|---|---|
| CTR-F04-1 | Nas 3 rotas (`GET /events`, `POST /events/$E/purchases` com corpo válido, `GET /tickets/qualquer`): sem header e com `X-Api-Key: errada` | 6 respostas, todas `401` com corpo exatamente `{"error":"unauthorized"}` |
| CTR-F04-2 | `GET /api/partner/events` com chave | `200`; contém E com `"availableSeats":2`, `"priceCents":10000`, `startsAt` ISO com offset `-03:00`; chaves exatas `id,name,startsAt,priceCents,availableSeats`; **não** contém D |
| CTR-F04-3 | `POST .../events/$E/purchases` `{"buyerEmail":"t2@example.com","cardNumber":"4000000000000004"}` | `202`, corpo `{"ticketId":"...","code":"<8 [A-Z0-9]>","status":"pending"}` |
| CTR-F04-4 | `GET .../tickets/$TID` | `200`, `{"ticketId","code","eventId":"$E","status":"pending","checkedIn":false}` |
| CTR-F04-5 | Corpo inválido: `cardNumber":"123"`; sem `buyerEmail`; `buyerEmail":"ana@"`; corpo `xyz` | `422` `{"error":"invalid_request"}` em todos |
| CTR-F04-6 | `cardNumber":"123"` para evento `evt_naoexiste` | `422` (corpo validado antes do evento) |
| CTR-F04-7 | Compra válida em `evt_naoexiste` e em D | `404` `{"error":"event_not_available"}` |
| CTR-F04-8 | Compra (0001) em E até lotar; mais uma | última `409` `{"error":"sold_out"}`; `GET /events` mostra `"availableSeats":0` |
| CTR-F04-9 | Com E lotado pela API: `GET /events/$E` na vitrine (participante da seed) | contém `Ingressos esgotados` |
| CTR-F04-10 | `sleep 45` após CTR-F04-3; `GET .../tickets/$TID`; `GET /events` | `"status":"declined"`; E com `"availableSeats":1` |
| CTR-F04-11 | Participante da seed compra na vitrine um evento publicado F (0001); pegar id em `psql`; `GET .../tickets/<id>` | `200` com o mesmo `code` e `eventId` de F |
| CTR-F04-12 | `GET .../tickets/tkt_inexistente` | `404` `{"error":"ticket_not_found"}` |
| CTR-F04-13 | Rajada R07 (receita) em **5** eventos novos de lotação 5, um por rodada | cada rodada: `5 202` e `25 409` |
| CTR-F04-14 | `./scripts/gates.sh` | exit 0, inclui `test_burst_30_capacity_5` |

## Mapeamento PRD → itens

| Critério | Itens |
|---|---|
| F04-AC-1 | CTR-F04-1 |
| F04-AC-2 | CTR-F04-2 |
| F04-AC-3 | CTR-F04-3 |
| F04-AC-4 | CTR-F04-5, CTR-F04-6, CTR-F04-7, CTR-F04-8 |
| F04-AC-5 | CTR-F04-13, CTR-F04-14 |
| F04-AC-6 | CTR-F04-4, CTR-F04-12 |
| F04-AC-7 | CTR-F04-10 |
| XF-4 (F02→F04) | CTR-F04-2 |
| XF-5 (F03→F04) | CTR-F04-8, CTR-F04-9, CTR-F04-11 |
