# F07 — Painel: spec técnica

PRD: F07-AC-1..4, XF-12, XF-13, XF-14. Consome F02 (`manage_context`, `available_seats`, filtro `brl`, `org/manage.html` com include de `org/_panel.html`), F03 (tickets com `price_cents` gravado) e F04 (tickets da API). Wave paralela W5: não depende de F05/F06; `checked_in` e `refunded` são preparados por SQL nos testes.

## Decisões

**Módulo:** `app/panel.py`, template `app/templates/org/_panel.html`. Sem rota nova.

**Métricas** `async def panel_metrics(conn, event) -> dict`, uma consulta só:
```sql
select
  count(*) filter (where status='confirmed')                      as confirmed,
  count(*) filter (where status='pending')                        as pending,
  count(*) filter (where status='confirmed' and checked_in)       as checkins,
  count(*) filter (where status='refunded')                       as refunded,
  coalesce(sum(price_cents) filter (where status='confirmed'), 0) as revenue_cents
from tickets where event_id = %s
```
mais `available = await available_seats(conn, event)` (0 em cancelado, R05).

**Integração:** em `manage_context` (F02), acrescentar `ctx["panel"] = await panel_metrics(conn, event)`. Toda renderização da página de gestão (GET, erros de edição, check-in, cancelamento) passa a mostrar o painel.

**Parcial** `org/_panel.html`, rótulos exatos de R12, valores com `data-metric`:
```html
<dl id="panel">
  <dt>Confirmados</dt><dd data-metric="confirmed">{{ panel.confirmed }}</dd>
  <dt>Pendentes</dt><dd data-metric="pending">{{ panel.pending }}</dd>
  <dt>Check-ins</dt><dd data-metric="checkins">{{ panel.checkins }}</dd>
  <dt>Vagas disponíveis</dt><dd data-metric="available">{{ panel.available }}</dd>
  <dt>Receita</dt><dd data-metric="revenue">{{ panel.revenue_cents|brl }}</dd>
  <dt>Estornados</dt><dd data-metric="refunded">{{ panel.refunded }}</dd>
</dl>
```
