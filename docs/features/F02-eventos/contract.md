# F02 — Eventos do organizador: contrato

## Pré-requisitos
- Clone limpo do commit indicado, `WEB_PORT` livre, `./scripts/up.sh`.
- Receitas: `docs/features/_eval-recipes.md` (login A, B e participante; criar, publicar, editar evento).
- Para preparar vagas ocupadas (F03 ainda não existe), inserir ingressos por SQL:
  `docker compose exec -T db psql -U catraca -d catraca -c "insert into tickets(id,event_id,code,status,price_cents) values ('tkt_t1','$EID','TESTAA01','pending',10000),('tkt_t2','$EID','TESTAA02','confirmed',10000)"`

## Itens

| Item | Como verificar | Esperado |
|---|---|---|
| CTR-F02-1 | Como A, criar evento (receita) com `capacity=2`, `price=100,00`, `starts_at=$FUT` | `303 .../org/events/evt_...` |
| CTR-F02-2 | Página de gestão do evento | `200`; contém `id="event-name">Jazz no Porão`, `id="event-status">rascunho`, `R$ 100,00`, `id="edit-form"`, `id="publish-form"`; URL `/org/events/<id>` |
| CTR-F02-3 | Criar com `starts_at=$PAST` | `422`, `Data de início precisa estar no futuro` |
| CTR-F02-4 | Criar com `capacity=0`; depois com `price=0` | `422` com `Lotação deve ser um inteiro maior ou igual a 1`; `422` com `Preço deve ser maior que zero` |
| CTR-F02-5 | Editar o evento com `starts_at=$PAST` | `422`, `Data de início precisa estar no futuro` |
| CTR-F02-6 | `psql -At -c "select status from events where id='$EID'"`; `GET /org/events` (A) | `draft`; lista contém `data-event-id="$EID"` |
| CTR-F02-7 | Publicar (receita); `psql` status; página de gestão | `303`; `published`; `id="event-status">publicado`, sem `publish-form` |
| CTR-F02-8 | Publicar de novo | `409` |
| CTR-F02-9 | Inserir 2 ingressos (pending + confirmed) por SQL; editar com `capacity=1` | `422`, `Lotação não pode ser menor que as vagas ocupadas` |
| CTR-F02-10 | Editar com `capacity=3`, `price=150,00`; página de gestão | `303`; mostra lotação 3 e `R$ 150,00` |
| CTR-F02-11 | Como B: `GET /org/events` | sem `data-event-id="$EID"` |
| CTR-F02-12 | Como B: `GET /org/events/$EID` | `404`; corpo **não** contém `Jazz no Porão`, `Bar do Zé`, `100,00`, `150,00` |
| CTR-F02-13 | Como B: `POST /org/events/$EID/edit` (campos válidos) e `POST .../publish` | `404` nos dois; `psql` mostra evento inalterado |
| CTR-F02-14 | Como participante da seed: `GET /org/events` e `GET /org/events/$EID`; sem cookie: `GET /org/events/$EID` | `403`, `403`; `303 .../login` |
| CTR-F02-15 | `./scripts/gates.sh tests/test_f02_seats.py -v` | `test_occupied_counts_pending_confirmed` e `test_available_cancelled_zero` passam |
| CTR-F02-16 | `./scripts/gates.sh` | exit 0 |

## Mapeamento PRD → itens

| Critério | Itens |
|---|---|
| F02-AC-1 | CTR-F02-1, CTR-F02-4 |
| F02-AC-2 | CTR-F02-3, CTR-F02-5 |
| F02-AC-3 | CTR-F02-6, CTR-F02-7, CTR-F02-8 |
| F02-AC-4 | CTR-F02-9, CTR-F02-10 |
| F02-AC-5 | CTR-F02-2, CTR-F02-7, CTR-F02-10 |
| F02-AC-6 | CTR-F02-11, CTR-F02-12, CTR-F02-13 |
| F02-AC-7 | CTR-F02-15 |
| XF-1 (F01→F02) | CTR-F02-1 (login A da seed), CTR-F02-14 |
