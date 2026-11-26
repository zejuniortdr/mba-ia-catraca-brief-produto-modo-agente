# Catraca MVP — Design

Fonte: `docs/enunciado.md` (brief R01–R13, requisitos 1–6, Fluxo do avaliador).

## Intenção
Entregar o MVP da Catraca construído por agentes, com features que funcionam juntas (não só isoladas), cada uma aprovada por avaliador independente, e passar nos 18 passos do Fluxo do avaliador a partir de clone limpo.

## Objetivos
- Produto conforme R01–R13 e contrato fixo da API de parceiros.
- PRD, spec/plano/contrato por feature, relatórios de avaliação, `state.json`, harness, AGENTS.md, README.
- Wave paralela integrada por PRs com commits sobrepostos no tempo.

## Não-objetivos
Tudo da seção "Fora de escopo" do enunciado (deploy, gateway real, e-mail, design visual, cadastro de organizador, multi-ingresso, tempo real, fuso).

## Anti-objetivos (falha mesmo "funcionando")
- Feature aprovada isolada que quebra quando integrada (evento cancelado deixando entrar, estorno somado como receita, overbooking).
- Relatório escrito ou alterado por quem implementou.
- Qualquer passo extra além do comando de subida.

## Restrições
- Máquina do avaliador: Linux/macOS, Docker, Git, Node LTS. Python só em container.
- Modo padrão usa gateway simulado com os atrasos exatos do brief; atraso configurável só em teste.

## Decisões (escolhidas pelo usuário)
| Tema | Escolha | Alternativas descartadas |
|---|---|---|
| Stack | FastAPI + Jinja2 (SSR) + Postgres, docker compose | SPA separada (mais peças, design não avaliado); SQLite (lock fraco p/ R07) |
| Agentes | Sessão principal orquestra; subagente implementador por feature (Sonnet), subagente avaliador novo de contexto vazio (Opus) | Sessões tmux manuais; avaliador em outra ferramenta |
| Gateway assíncrono | `asyncio` task no processo: dorme o atraso, `UPDATE ... WHERE status='pending'`; reagenda pendentes no startup | Worker com fila no Postgres; gateway HTTP + webhook |
| R07 concorrência | `SELECT ... FOR UPDATE` na linha do evento, conta pending+confirmed reais antes de inserir; mesmo lock em edição de lotação e cancelamento | Contador desnormalizado; SERIALIZABLE + retry |
| Cancelamento | Transação síncrona muda confirmed→refunded e pending→cancelled na hora | — |

## Features e waves (aprovadas)
| ID | Feature | Regras |
|---|---|---|
| F01 | Fundação: harness, compose, schema, contas participante, organizadores seed, guarda de papel | R13 |
| F02 | Eventos do organizador: CRUD, rascunho/publicação, página de gestão, isolamento | R01–R04, R13 |
| F03 | Vitrine e compra: vitrine, serviço de compra com lock, gateway simulado, Meus ingressos, código único | R05–R09 |
| F04 | API de parceiros (3 rotas, X-Api-Key, ordem de erros) | R02, R05–R07 |
| F05 | Check-in | R10 |
| F06 | Cancelamento | R11 |
| F07 | Painel | R12 |

Waves: W1 F01 · W2 F02 · W3 F03 · W4 F04 · **W5 paralela: F05, F06, F07** (cada uma consome F02, F03, F04).

## Layout de artefatos
- `docs/PRD.md`, `docs/state.json`, `AGENTS.md` (+ `CLAUDE.md` apontando), `README.md`.
- `docs/features/FXX-nome/{spec.md, plan.md, contract.md, reports/YYYY-MM-DD-HHMM-<commit>.md}`.

## Calls do builder (decididos pelo agente, corrigíveis)
- Comandos: `./scripts/up.sh`, `./scripts/down.sh`, `./scripts/gates.sh` (bash, sem `make`, pois o avaliador só garante Docker/Git/Node). `down` = `docker compose down -v --remove-orphans`.
- `$WEB` = `$API` = `http://localhost:8000`.
- Seed idempotente (upsert por e-mail) roda no startup do container da app.
- Gates: ruff + pytest rodando em container contra Postgres real, incluindo teste de rajada R07 repetido em eventos novos.
- Auth web: sessão por cookie assinado (Starlette `SessionMiddleware`), senha com hash (`passlib`/bcrypt ou `hashlib.scrypt` da stdlib).
- IDs: `evt_<hex>`, `tkt_<hex>`; código do ingresso 8 chars `[A-Z0-9]`, único por constraint.
- Dinheiro em centavos inteiros; preço gravado no ingresso no momento da compra (R03/R12).
- Página de gestão de evento de outro organizador responde 404 sem dados (R13).
- Fluxo: cada feature em branch própria + PR; W5 em 3 worktrees simultâneos.
- Remote trocado para HTTPS (regra global do usuário).

## Deixado para o builder
Estrutura interna de módulos, templates, nomes de tabelas, testes por feature — definidos nas specs de cada feature.
