# AGENTS.md — porta de entrada dos agentes

Catraca: venda de ingressos para eventos pequenos. Brief em `docs/enunciado.md`, requisitos em `docs/PRD.md`.

## Comandos

| O quê | Comando |
|---|---|
| Subir tudo (build + banco + app + seed) | `./scripts/up.sh` |
| Derrubar tudo | `./scripts/down.sh` |
| Gates (ruff + pytest, banco de teste isolado) | `./scripts/gates.sh` |
| Gates só de um teste | `./scripts/gates.sh tests/test_f03_purchase.py::test_nome` |
| CI (GitHub Actions: gates + harness up/smoke/down) | `.github/workflows/ci.yml`, roda em push na `main` e em PR |
| SQL no banco do produto | `docker compose exec -T db psql -U catraca -d catraca -c "..."` |

Produto e API de parceiros: `http://localhost:${WEB_PORT:-8000}`. Chave de parceiro: `catraca-parceiro-2026`. Seed (senha `catraca123`): `org.a@catraca.local`, `org.b@catraca.local`, `participante@catraca.local`.

Pré-requisitos no host: bash, Docker com Compose v2, Git. Nada de Python no host.

## Regras do projeto

- Stack: Python 3.12, FastAPI, Jinja2 (HTML no servidor), Postgres 16, psycopg 3 com SQL direto. Tudo em docker compose.
- Contratos compartilhados (schema, interfaces Python, rotas, marcadores HTML) estão em `docs/planning/master-plan.md` → "Contratos compartilhados" e nas specs das features. Não mude assinatura de outra feature sem registrar na spec dela.
- R07: toda operação que muda ocupação ou lotação trava a linha do evento com `SELECT ... FOR UPDATE`.
- Gateway: `apply_result` só muda ingresso `pending` (`WHERE status='pending'`).
- Modo padrão usa o gateway simulado com atrasos do brief. `GATEWAY_DELAY_SCALE` só muda em teste.
- Mensagens, rótulos e códigos de erro são copiados literalmente do brief.
- Código, identificadores e commits em inglês; documentação em pt-BR.
- TDD: teste falhando antes do código. `./scripts/gates.sh` verde antes de cada push.
- Git: branch `feat/fXX-<slug>`, commits pequenos, PR para `main`, merge com `--merge`. Nunca push direto na `main`. Stage explícito (sem `git add -A`).

## Fluxo implementar → avaliar → corrigir

1. Implementador lê `spec.md`, `plan.md` e `contract.md` da feature, implementa com TDD, roda gates, abre PR. **Não escreve relatório.**
2. Avaliador é outro agente, de contexto vazio. Executa cada item do `contract.md` no commit indicado e cria `docs/features/FXX-*/reports/<YYYYMMDD-HHMM>-<sha7>.md` a partir de `docs/features/_report-template.md`. Commita só o relatório.
3. Item reprovado volta para correção e para nova avaliação, com relatório **novo**. Relatório commitado nunca é editado.
4. `docs/state.json` é atualizado pelo orquestrador: status e caminho do relatório mais recente.

## Mapa de artefatos

| Artefato | Caminho |
|---|---|
| Brief | `docs/enunciado.md` |
| PRD | `docs/PRD.md` |
| Design e plano mestre | `docs/planning/design.md`, `docs/planning/master-plan.md` |
| Features (spec, plano, contrato, relatórios) | `docs/features/F01-fundacao/` … `docs/features/F07-painel/` |
| Receitas de avaliação (curl) | `docs/features/_eval-recipes.md` |
| Template de relatório | `docs/features/_report-template.md` |
| Estado do projeto | `docs/state.json` |
| Código | `app/`, testes em `tests/`, scripts em `scripts/` |
