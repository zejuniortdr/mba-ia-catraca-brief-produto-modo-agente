# F02 — Eventos do organizador: spec técnica

PRD: F02-AC-1..7, XF-1. Consome F01 (`require_organizer`, `get_conn`, `templates`, schema). Provê para F03–F07.

## Decisões

**Módulos:** `app/events.py` (router + queries), `app/seats.py`, templates `app/templates/org/{list,new,manage}.html`, `app/templates/404.html`. Substitui o placeholder `GET /org/events` de F01.

**Formulário de evento** (criar e editar, mesmos campos): `name` (não vazio), `starts_at` (`YYYY-MM-DDTHH:MM`, `input type="datetime-local"`, interpretado no fuso fixo `-03:00`), `venue` (não vazio), `capacity` (inteiro ≥ 1), `price` (reais; aceita `100`, `100,00`, `100.00`; convertido para `price_cents` inteiro > 0). Função pura `parse_event_form(form, now) -> (dict | None, list[str])` com mensagens:
- `Nome é obrigatório`, `Local é obrigatório`
- `Data de início inválida`, `Data de início precisa estar no futuro`
- `Lotação deve ser um inteiro maior ou igual a 1`
- `Preço deve ser maior que zero`
Erro → re-render do formulário com status 422 e cada mensagem em `<p class="error">`.

**Queries** (`app/events.py`):
- `get_event(conn, event_id) -> dict | None`
- `get_owned_event(conn, event_id, organizer_id) -> dict | None` (`WHERE id=%s AND organizer_id=%s`)
- `list_on_sale(conn) -> list[dict]`: `status='published'`, `ORDER BY starts_at`.
- `list_by_organizer(conn, organizer_id) -> list[dict]`
- IDs `evt_<10 hex>`.

**Vagas** (`app/seats.py`):
- `occupied_seats(conn, event_id) -> int`: `count(*) WHERE status IN ('pending','confirmed')`.
- `available_seats(conn, event) -> int`: `0` se `event["status"]=='cancelled'`, senão `max(0, capacity - occupied)`.

**Edição com lock (R03):** `POST /org/events/{id}/edit` numa transação: `SELECT * FROM events WHERE id=%s AND organizer_id=%s FOR UPDATE` → se nova `capacity < occupied_seats` → 422 `Lotação não pode ser menor que as vagas ocupadas (N)` → `UPDATE`. Preço novo vale só para compras futuras (o ingresso grava o próprio preço em F03). Edição de evento `cancelled` é responsabilidade de F06 (aqui não precisa tratar).

**Publicação:** `POST /org/events/{id}/publish`: só de `draft` para `published` (`UPDATE ... WHERE id=%s AND organizer_id=%s AND status='draft'`); outro estado → 409 com `<p class="error">Evento não pode ser publicado</p>`. Sucesso → 303 para a página de gestão.

**Rotas** (todas com `require_organizer`):
- `GET /org/events`: lista própria; cada item `<li data-event-id="{id}"><a href="/org/events/{id}">{name}</a> <span>{status_label}</span></li>`; link "Novo evento".
- `GET /org/events/new`, `POST /org/events/new` → 303 `/org/events/{id}`.
- `GET /org/events/{id}`: página de gestão. Evento inexistente **ou de outro organizador** → 404 com `404.html` ("Evento não encontrado"), sem nenhum dado do evento. Mesmo 404 para todo POST em `/org/events/{id}/...`.
- `POST /org/events/{id}/edit`, `POST /org/events/{id}/publish`.

**Página de gestão** (`org/manage.html`), marcadores obrigatórios:
- `<h1 id="event-name">{name}</h1>`, `<span id="event-status">{rascunho|publicado|cancelado}</span>`
- dados: data/hora, local, lotação, preço `R$ 100,00`
- `<form id="edit-form" method="post" action="/org/events/{id}/edit">` com os campos preenchidos
- `<form id="publish-form" ...>` só quando `draft`
- `{% include "org/_checkin.html" ignore missing %}`, `{% include "org/_cancel.html" ignore missing %}`, `{% include "org/_panel.html" ignore missing %}`
- Contexto e renderização reutilizáveis em `app/events.py`:
  - `async def manage_context(request, conn, event, user) -> dict` → `{"request", "user", "event", "errors": []}`. F07 acrescenta a chave `panel` aqui.
  - `def render_manage(ctx: dict, status_code: int = 200) -> TemplateResponse` renderiza `org/manage.html`.
  - `GET /org/events/{id}` e os erros de edição/publicação usam essas duas funções; F05 e F06 também (ex.: `ctx["checkin_result"] = msg`).

**Formatação:** helper `format_brl(cents) -> str` em `app/web.py` (`10000` → `R$ 100,00`; `35000` → `R$ 350,00`), registrado como filtro Jinja `brl`. Rótulos de status do evento: `draft→rascunho`, `published→publicado`, `cancelled→cancelado`.
