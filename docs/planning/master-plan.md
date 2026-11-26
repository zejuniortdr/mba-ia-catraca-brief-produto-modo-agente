# Catraca MVP — Plano mestre de execução

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar o MVP Catraca (R01–R13 + API de parceiros) com PRD, spec/plano/contrato por feature, relatórios de avaliação independentes, harness, estado e uma wave paralela integrada por PRs.

**Architecture:** Um serviço FastAPI (HTML via Jinja2 + API JSON de parceiros) sobre Postgres, em docker compose. SQL direto via psycopg 3 (async pool) para deixar locks explícitos. Gateway simulado por `asyncio` tasks no processo. Sessão principal orquestra; cada feature é implementada por subagente novo (Sonnet) e avaliada por outro subagente novo de contexto vazio (Opus).

**Tech Stack:** Python 3.12, FastAPI, uvicorn, Jinja2, python-multipart, psycopg[binary] 3 + psycopg_pool, itsdangerous (SessionMiddleware), hashlib.scrypt (stdlib), pytest + httpx, ruff, Postgres 16, Docker Compose v2.

**Spec:** `docs/planning/design.md` + `docs/enunciado.md` (fonte de verdade do comportamento).

## Global Constraints

- Máquina do avaliador: só Linux/macOS, Docker, Git, Node LTS. Nada roda no host além de bash + docker.
- `./scripts/up.sh` sobe tudo de clone limpo com seed; `./scripts/down.sh` derruba tudo (nenhuma porta, nenhum container); `./scripts/gates.sh` roda ruff + pytest e passa na main.
- `$WEB` = `$API` = `http://localhost:8000` (porta via env `WEB_PORT`, default `8000`). Postgres não expõe porta no host.
- Modo padrão: gateway simulado com atrasos exatos do brief. `GATEWAY_DELAY_SCALE` (default `1.0`) só é alterado em testes.
- Chave de parceiro: env `PARTNER_API_KEY`, default `catraca-parceiro-2026`.
- Seed (idempotente, upsert por e-mail, senha `catraca123` para todos):
  - Organizador A: `org.a@catraca.local` (nome "Organizador A")
  - Organizador B: `org.b@catraca.local` (nome "Organizador B")
  - Participante: `participante@catraca.local` (nome "Participante Seed")
- Rótulos de UI exatos: `pendente`, `confirmado`, `recusado`, `cancelado`, `estornado`; valores API: `pending`, `confirmed`, `declined`, `cancelled`, `refunded`.
- Mensagens exatas: `Ingressos esgotados`; check-in: `Ingresso inválido para este evento`, `Evento cancelado`, `Ingresso não confirmado`, `Ingresso já utilizado`, `Entrada liberada`.
- Erros API exatos: 401 `{"error":"unauthorized"}`, 422 `{"error":"invalid_request"}`, 404 `{"error":"event_not_available"}`, 409 `{"error":"sold_out"}`, 404 `{"error":"ticket_not_found"}`.
- Fuso fixo `-03:00` (`timezone(timedelta(hours=-3))`); `startsAt` serializado ISO-8601 com offset, ex.: `2026-12-05T21:00:00-03:00`.
- Dinheiro em centavos inteiros. Preço do ingresso gravado em `tickets.price_cents` na compra.
- Documentação em pt-BR; código, identificadores e commits em inglês.
- Branch por feature `feat/fXX-<slug>`, PR para `main`, merge com `gh pr merge --merge` (sem squash, preserva commits dos relatórios). Nunca push direto na `main`. Stage explícito, sem `git add -A`.
- Relatórios de avaliação: um arquivo novo por avaliação, nunca editado depois do commit.

## Contratos compartilhados (todas as features obedecem)

**Layout:**
```
app/main.py            # create_app(): middlewares, routers, startup (schema, seed, reschedule)
app/db.py              # pool: AsyncConnectionPool; get_conn() dependency; apply_schema()
app/schema.sql         # schema completo (F01)
app/auth.py            # F01
app/seed.py            # F01
app/events.py          # F02 (rotas org + queries de evento)
app/seats.py           # F02
app/gateway.py         # F03
app/purchases.py       # F03 (serviço de compra)
app/shop.py            # F03 (rotas vitrine/compra/meus ingressos)
app/partner_api.py     # F04
app/checkin.py         # F05
app/cancellation.py    # F06
app/panel.py           # F07
app/templates/...      # base.html (F01); org/*.html (F02, F05–F07); shop/*.html (F03)
tests/conftest.py      # F01: DB de teste `catraca_test`, client httpx ASGI, fixtures de login
tests/test_fXX_*.py
scripts/{up,down,gates}.sh
Dockerfile, compose.yml, pyproject.toml
```

**Schema (F01 cria tudo; features seguintes não alteram colunas existentes):**
```sql
users(id text pk, name text, email text unique, password_hash text,
      role text check (role in ('participant','organizer')), created_at timestamptz default now())
events(id text pk /* evt_<10 hex> */, organizer_id text fk users, name text, starts_at timestamptz,
       venue text, capacity int check (capacity >= 1), price_cents int check (price_cents > 0),
       status text check (status in ('draft','published','cancelled')) default 'draft',
       created_at timestamptz default now())
tickets(id text pk /* tkt_<10 hex> */, event_id text fk events, user_id text null fk users,
        buyer_email text, code text unique /* 8 chars [A-Z0-9] */,
        status text check (status in ('pending','confirmed','declined','cancelled','refunded')),
        price_cents int, checked_in boolean default false,
        gateway_approved boolean, gateway_due_at timestamptz, created_at timestamptz default now())
```
Feature que precisar de coluna nova adiciona `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` ao fim de `app/schema.sql`.

**Interfaces Python:**
- F01 `app/db.py`: `pool`, `async def get_conn() -> AsyncIterator[AsyncConnection]` (dependency), `async def apply_schema() -> None`.
- F01 `app/auth.py`: `async def current_user(request) -> dict | None` (`{id,name,email,role}`), `async def require_user(request) -> dict` (sem login → redirect 303 `/login`), `async def require_organizer(request) -> dict` (visitante → 303 `/login`; participante → 403).
- F02 `app/events.py`: `async def get_event(conn, event_id) -> dict | None`, `async def get_owned_event(conn, event_id, organizer_id) -> dict | None`, `async def list_on_sale(conn) -> list[dict]` (published, ordem `starts_at`).
- F02 `app/seats.py`: `async def occupied_seats(conn, event_id) -> int` (pending+confirmed), `async def available_seats(conn, event) -> int` (cancelled → 0; senão `capacity - occupied`).
- F03 `app/gateway.py`: `def decide(card_number: str) -> tuple[bool, float]` (aprovado?, atraso s, sorteado na faixa do brief × `GATEWAY_DELAY_SCALE`); `def schedule(ticket_id: str, approved: bool, due_at: datetime) -> None`; `async def apply_result(ticket_id, approved) -> None` (`UPDATE ... WHERE id=%s AND status='pending'`); `async def reschedule_pending() -> None`.
- F03 `app/purchases.py`: exceções `InvalidRequest`, `EventNotAvailable`, `SoldOut`; `async def purchase(conn, event_id, card_number, *, user_id=None, buyer_email=None) -> dict` (`{id, code, status, event_id}`): valida cartão (16 dígitos) → `SELECT ... FROM events WHERE id=%s FOR UPDATE` → status != published → `EventNotAvailable` → `occupied_seats >= capacity` → `SoldOut` → insere pending com `price_cents` do evento → commit → `schedule(...)`.
- F02 edição de lotação e F06 cancelamento usam o mesmo `SELECT ... FOR UPDATE` na linha do evento.

**Rotas:**
- F01: `GET/POST /signup`, `GET/POST /login`, `POST /logout`.
- F02: `GET /org/events`, `GET/POST /org/events/new`, `GET /org/events/{id}` (página de gestão), `POST /org/events/{id}/edit`, `POST /org/events/{id}/publish`. Evento de outro organizador → 404 sem dados.
- F03: `GET /` (vitrine), `GET /events/{id}`, `POST /events/{id}/buy`, `GET /me/tickets`.
- F04: `GET /api/partner/events`, `POST /api/partner/events/{id}/purchases`, `GET /api/partner/tickets/{id}`.
- F05: `POST /org/events/{id}/checkin` (renderiza a página de gestão com a mensagem).
- F06: `POST /org/events/{id}/cancel`.
- F07: sem rota; seção do painel na página de gestão.

**Página de gestão (`app/templates/org/manage.html`, F02):** blocos `{% include "org/_checkin.html" ignore missing %}`, `{% include "org/_cancel.html" ignore missing %}`, `{% include "org/_panel.html" ignore missing %}`. F05/F06/F07 criam o próprio parcial e acrescentam suas chaves ao contexto do handler `GET /org/events/{id}` (conflito esperado, resolvido na integração).

## Review Focus

1. Resposta tardia do gateway após cancelamento (cartão `...0003`) não pode sobrescrever `cancelled` → teste em F06 com `GATEWAY_DELAY_SCALE` pequeno: cancela antes do `due_at`, espera, status segue `cancelled`.
2. Rajada de 30 compras em lotação 5 → exatamente 5×202 / 25×409, repetida em ≥5 eventos novos → teste em F04 (e F03 no nível de serviço).
3. Reinício do container com pendentes → `reschedule_pending` resolve vencidos imediatamente e agenda futuros → teste em F03.
4. Organizador B acessando `/org/events/{id}` de A, `POST .../edit|publish|cancel|checkin` de A → 404 sem nome do evento no corpo → testes em F02, F05, F06.
5. Edição de evento cancelado (e republicação) via POST direto → rejeitada → teste em F06; data passada em edição → rejeitada → teste em F02.

---

### Task 0: Bootstrap do repositório

**Files:** Create `.gitignore`. Commit `docs/enunciado.md`, `docs/planning/design.md`, `docs/planning/master-plan.md`.

- [ ] **Step 1:** `git remote set-url origin https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente.git`; `gh auth status`; `git remote -v` confirma repo do usuário.
- [ ] **Step 2:** Branch `chore/bootstrap`, commit dos docs, push, PR, merge `--merge`.

### Task 1: PRD

**Files:** Create `docs/PRD.md`.

Conteúdo obrigatório (requisito 1): visão; personas; status do ingresso; features F01–F07 com ID, descrição, **Provê** / **Consome**; grafo de dependências (mermaid + lista de arestas); waves; critérios de aceite por feature com IDs `FXX-AC-n`; critérios cross-feature `XF-n`, ao menos um por aresta do grafo (`F01→F02`, `F01→F03`, `F02→F03`, `F02→F04`, `F03→F04`, `F02→F05`, `F03→F05`, `F04→F05`, `F02→F06`, `F03→F06`, `F04→F06`, `F02→F07`, `F03→F07`, `F04→F07`), cada um indicando aresta e feature cujo contrato o cobre; tabela de rastreabilidade R01–R13 → critérios; seção Fora de escopo (copiar do enunciado).

- [ ] **Step 1:** Escrever PRD.
- [ ] **Step 2:** Verificar: `for r in R01 R02 R03 R04 R05 R06 R07 R08 R09 R10 R11 R12 R13; do grep -c "$r" docs/PRD.md; done` todos ≥1; cada aresta aparece em algum `XF-`.
- [ ] **Step 3:** Branch `docs/prd`, PR, merge.

### Task 2: Specs, planos, contratos, AGENTS.md, estado

**Files:** Create `docs/features/F0X-<slug>/{spec.md,plan.md,contract.md}` para F01-fundacao, F02-eventos, F03-compra, F04-api-parceiros, F05-checkin, F06-cancelamento, F07-painel; `docs/features/_report-template.md`; `AGENTS.md`; `CLAUDE.md` (uma linha: "Leia AGENTS.md."); `docs/state.json`.

- spec.md: decisões técnicas da feature, restritas aos Contratos compartilhados acima.
- plan.md: etapas TDD com arquivos, assinaturas e testes.
- contract.md: (a) pré-requisitos de ambiente; (b) itens `CTR-FXX-n`, cada um com comando (curl/pytest/sql) e resultado esperado; (c) tabela de mapeamento `FXX-AC-n`/`XF-n` → `CTR-FXX-n`. Todo `XF-n` mapeado em ≥1 contrato.
- Template de relatório: data ISO, commit avaliado (sha completo), branch, ferramenta (Claude Code), modelo, isolamento declarado, tabela item → veredito (APROVADO/REPROVADO) → evidência (saída literal), veredito final.
- `state.json`: `{"features":[{"id","name","wave","status":"pending|in_progress|in_review|changes_requested|done","branch","pr","latestReport"}]}`.
- AGENTS.md: comandos, regras do projeto (Global Constraints + Contratos compartilhados resumidos), fluxo implementar→avaliar→corrigir, regra "quem implementa não avalia, não edita relatório", mapa de artefatos.

- [ ] **Step 1:** Escrever docs das 7 features (skill `writing-technical-specs`).
- [ ] **Step 2:** Verificar cobertura: todo `FXX-AC-n` e `XF-n` do PRD aparece em alguma tabela de mapeamento (`grep -o "XF-[0-9]*" docs/PRD.md | sort -u` ⊆ union dos contratos).
- [ ] **Step 3:** Branch `docs/specs`, PR, merge.

### Task 3–9: Ciclo por feature (W1 F01 → W2 F02 → W3 F03 → W4 F04 → W5 F05‖F06‖F07)

Para cada feature `FXX`:

- [ ] **Step 1 — Implementar:** subagente novo (`general-purpose`, model `sonnet`) em worktree `../catraca-fXX` na branch `feat/fXX-<slug>` a partir da `main`. Prompt: ler `AGENTS.md`, `spec.md`, `plan.md`, `contract.md` da feature; executar `plan.md` com TDD; commits pequenos desde o primeiro passo; `./scripts/gates.sh` verde; push; abrir PR. Não escrever relatório. Retorno: sha final, URL do PR, saída resumida dos gates.
- [ ] **Step 2 — Estado:** `state.json` → `in_review`, branch, pr.
- [ ] **Step 3 — Avaliar:** subagente novo (`general-purpose`, model `opus`), contexto vazio, recebe só: caminho do worktree, sha, `contract.md`, template. Sobe o ambiente (`WEB_PORT` livre), executa cada item do contrato, escreve `docs/features/FXX-*/reports/<YYYYMMDD-HHMM>-<sha7>.md`, commita só esse arquivo, derruba ambiente. Retorno: veredito por item.
- [ ] **Step 4 — Corrigir se reprovado:** novo subagente implementador recebe itens reprovados + relatório; corrige; volta ao Step 3 com avaliador novo (relatório novo, o antigo intocado).
- [ ] **Step 5 — Fechar:** `state.json` → `done`, `latestReport`; commit; merge do PR `--merge`; remover worktree.

**W5 paralela:** criar os 3 worktrees da mesma `main` e despachar os 3 implementadores na mesma mensagem (concorrentes). Cada um commita e faz push já na primeira etapa, para que o primeiro commit de cada PR anteceda o último dos outros. Avaliações depois, uma por feature. Merge em sequência F05, F06, F07, resolvendo conflitos em `app/main.py`/`app/events.py`/`manage.html`/`state.json`; após cada merge, `./scripts/gates.sh` na main.

### Task 10: README e verificação final

**Files:** Create `README.md` (Como rodar, Endereços, Credenciais, Mapa dos artefatos com links dos PRs da W5, Decisões: stack e por quê, R07, gateway assíncrono, isolamento da avaliação, Regras de entrega).

- [ ] **Step 1:** Escrever README; branch `docs/readme`, PR, merge.
- [ ] **Step 2:** Clone limpo da main em pasta temporária; subagente novo (`opus`) executa Fluxo do avaliador passos 1–17 via curl (sessão por cookie jar para UI) e reporta falhas. Falha → ciclo de correção na feature dona + reavaliação.
- [ ] **Step 3:** Rajada do passo 15 rodada ≥5 vezes em eventos novos: todas 5×202 / 25×409.
- [ ] **Step 4:** Verificar passo 18: `git log --format="%h %ad" --date=iso -- <relatório>` = 1 commit para cada relatório; `state.json` todos `done` e caminhos existem; commits dos PRs da W5 sobrepostos (`gh pr view <n> --json commits`).
- [ ] **Step 5:** Pedir confirmação do usuário e tornar repo público (`gh repo edit --visibility public --accept-visibility-change-consequences`).
