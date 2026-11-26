# F03 — Vitrine e compra: contrato

## Pré-requisitos
- Clone limpo do commit indicado, `WEB_PORT` livre, `./scripts/up.sh` (gateway com atrasos reais do brief).
- Receitas: `docs/features/_eval-recipes.md`. Criar como A um evento E (lotação 2, `price=100,00`) e publicar; criar um rascunho D.

## Itens

| Item | Como verificar | Esperado |
|---|---|---|
| CTR-F03-1 | `curl -s $WEB/` | contém `data-event-id="$E"`; **não** contém `data-event-id="$D"` |
| CTR-F03-2 | Signup de participante novo (jar `n`); `GET /events/$E` | `303`; contém `id="buy-form"` |
| CTR-F03-3 | Sem cookie: `POST /events/$E/buy -d card_number=4000000000000001` | `303 .../login`; nenhum ticket criado (`psql`) |
| CTR-F03-4 | Com jar `n`: `POST /events/$E/buy -d card_number=4000000000000001` medindo tempo (`-w '%{time_total}'`); logo depois `GET /me/tickets` | `303 .../me/tickets` em < 1 s; linha com `class="event">` nome do evento, `class="status">pendente`, `class="code">` 8 caracteres `[A-Z0-9]` |
| CTR-F03-5 | `sleep 5`; `GET /me/tickets` | mesma linha com `confirmado` |
| CTR-F03-6 | `POST /events/$E/buy -d card_number=123` | `422`, `Número do cartão deve ter 16 dígitos`; contagem de tickets do evento inalterada |
| CTR-F03-7 | Com jar `n`, comprar com `4000000000000004` (pendente 30–40 s); `GET /events/$E` como participante da seed | `id="sold-out">Ingressos esgotados`, sem `buy-form` (lotação 2: 1 confirmado + 1 pendente) |
| CTR-F03-8 | Ainda dentro de 30 s: participante da seed `POST /events/$E/buy` (0001) | `409`, `Ingressos esgotados`; nenhum ticket novo |
| CTR-F03-9 | `sleep 45` após CTR-F03-7; `psql` status do ticket 0004; `GET /events/$E` | `declined`; `buy-form` de volta (vaga liberada) |
| CTR-F03-10 | Compra com `4000000000000002`; `sleep 6`; `psql` | `declined` |
| CTR-F03-11 | `psql -At -c "select code from tickets" \| sort \| uniq -d` | vazio |
| CTR-F03-12 | Como A, editar E para `price=150,00`, `capacity=4`; comprar de novo (0001); `psql -At -c "select price_cents from tickets where event_id='$E' order by created_at"` | primeiros ingressos `10000`, último `15000` |
| CTR-F03-13 | Com E tendo 2 ocupadas (pendente+confirmado), A edita `capacity=1` | `422`, `Lotação não pode ser menor que as vagas ocupadas` |
| CTR-F03-14 | Comprar com `4000000000000003`; imediatamente `docker compose restart app`; após subir, `sleep 45`; `psql` status | `confirmed` (pendente reagendado após reinício) |
| CTR-F03-15 | `./scripts/gates.sh tests/test_f03_purchase.py -v` | `test_concurrent_purchases_never_exceed_capacity` passa (5 rodadas × 30 compras → 5 sucessos) |
| CTR-F03-16 | `GET /me/tickets` com jar do participante da seed | não contém ingressos do participante `n` |
| CTR-F03-17 | `./scripts/gates.sh` | exit 0 |

## Mapeamento PRD → itens

| Critério | Itens |
|---|---|
| F03-AC-1 | CTR-F03-1 |
| F03-AC-2 | CTR-F03-4, CTR-F03-16 |
| F03-AC-3 | CTR-F03-5, CTR-F03-9, CTR-F03-10 |
| F03-AC-4 | CTR-F03-6 |
| F03-AC-5 | CTR-F03-7, CTR-F03-9 |
| F03-AC-6 | CTR-F03-7, CTR-F03-8 |
| F03-AC-7 | CTR-F03-15 |
| F03-AC-8 | CTR-F03-4, CTR-F03-11 |
| F03-AC-9 | CTR-F03-12 |
| F03-AC-10 | CTR-F03-14 |
| XF-2 (F01→F03) | CTR-F03-2, CTR-F03-3, CTR-F03-4 |
| XF-3 (F02→F03) | CTR-F03-1, CTR-F03-12, CTR-F03-13 |
