# F05 — Check-in: contrato

## Pré-requisitos
- Clone limpo do commit indicado, `WEB_PORT` livre, `./scripts/up.sh` (atrasos reais).
- Receitas: `docs/features/_eval-recipes.md`. Como A: evento E (lotação 5) publicado. Como B: evento G publicado.
- Ingressos de E: C1 (participante da seed na vitrine, cartão 0001), C2 (API, cartão 0004, fica pendente 30–40 s), CA (API, cartão 0001). Ingresso de G: CG (API, 0001). `sleep 6` antes dos itens.

## Itens

| Item | Como verificar | Esperado |
|---|---|---|
| CTR-F05-1 | Página de gestão de E (A) | contém `id="checkin-form"` |
| CTR-F05-2 | Check-in C1 | `id="checkin-result">Entrada liberada` |
| CTR-F05-3 | Check-in C1 de novo | `Ingresso já utilizado` |
| CTR-F05-4 | Check-in C2 (pendente, dentro de 30 s) | `Ingresso não confirmado` |
| CTR-F05-5 | Check-in `ZZZZZZZZ` | `Ingresso inválido para este evento` |
| CTR-F05-6 | Check-in CG (código de outro evento) em E | `Ingresso inválido para este evento` |
| CTR-F05-7 | Check-in CA; `GET /api/partner/tickets/<id de CA>` | `Entrada liberada`; `"checkedIn":true` |
| CTR-F05-8 | Check-in de C1 em minúsculas com espaços (`code=%20<c1 minúsculo>%20`) | `Ingresso já utilizado` (código normalizado) |
| CTR-F05-9 | Como B: `POST /org/events/$E/checkin -d code=<CA>` | `404`, corpo sem nome de E |
| CTR-F05-10 | `psql -c "update tickets set status='declined' where code='<C2>'"`; check-in C2 | `Ingresso não confirmado` |
| CTR-F05-11 | Ingresso CX de E confirmado sem check-in (API, 0001, `sleep 6`); `psql -c "update events set status='cancelled' where id='$E'"`; check-in CX; check-in CG | `Evento cancelado`; `Ingresso inválido para este evento` |
| CTR-F05-12 | `./scripts/gates.sh tests/test_f05_checkin.py -v` | `test_not_confirmed` cobre pending, declined, cancelled, refunded e passa |
| CTR-F05-13 | `./scripts/gates.sh` | exit 0 |

## Mapeamento PRD → itens

| Critério | Itens |
|---|---|
| F05-AC-1 | CTR-F05-5 |
| F05-AC-2 | CTR-F05-11 |
| F05-AC-3 | CTR-F05-4, CTR-F05-10, CTR-F05-12 |
| F05-AC-4 | CTR-F05-3, CTR-F05-8 |
| F05-AC-5 | CTR-F05-2, CTR-F05-7 |
| F05-AC-6 | CTR-F05-6, CTR-F05-11 |
| XF-6 (F02→F05) | CTR-F05-1, CTR-F05-9 |
| XF-7 (F03→F05) | CTR-F05-2, CTR-F05-4, CTR-F05-6 |
| XF-8 (F04→F05) | CTR-F05-7 |
