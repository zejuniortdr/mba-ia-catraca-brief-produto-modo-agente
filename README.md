# Catraca — do brief ao produto em modo agente

[![CI](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)
[![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)](https://github.com/astral-sh/ruff)

Venda de ingressos para eventos pequenos (shows em bar, workshops, meetups). O MVP foi construído por agentes a partir do brief em [`docs/enunciado.md`](docs/enunciado.md). Cada feature tem spec, plano e contrato, e foi aprovada por um avaliador diferente de quem a implementou.

## Como rodar

**Pré-requisitos:** Linux ou macOS com bash, Docker (com Compose v2) e Git. Não é preciso Python nem Node no host, porque tudo roda em container.

| O quê | Comando |
|---|---|
| Subir tudo (build, banco, app e seed) | `./scripts/up.sh` |
| Derrubar tudo | `./scripts/down.sh` |
| Gates (ruff + pytest contra Postgres real, em projeto compose isolado) | `./scripts/gates.sh` |

**CI** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)): todo push na `main` e todo PR passam por três jobs. `gates` roda `./scripts/gates.sh`. `harness` sobe o produto, testa saúde, seed e chave da API, derruba e confere que nada continua rodando, e sobe de novo para provar que a seed é idempotente. `harness-container` repete subir, smoke e derrubar pela rota por container.

A subida não pede nenhum outro passo. O gateway de pagamento é simulado e não precisa de chave real.

O `./scripts/down.sh` para e remove os containers do produto e dos gates. O volume do banco é mantido, então, ao subir de novo, a seed roda outra vez sobre os dados existentes sem erro. Para usar outra porta, rode `WEB_PORT=8080 ./scripts/up.sh`.

### Alternativa: rodar os comandos por container

Use esta rota se a máquina não tiver bash ou Docker Compose v2 (o `--wait` do `up.sh` pede Compose ≥ 2.17). Ela só precisa do Docker Engine. A imagem [`harness/Dockerfile`](harness/Dockerfile) traz Docker CLI, Compose e bash, e executa os mesmos `scripts/*.sh` contra o daemon do host, pelo socket. O repositório é montado no mesmo caminho, então o nome do projeto Compose é o mesmo da rota direta: dá para subir por uma rota e derrubar pela outra.

```bash
docker build -t catraca-harness harness          # uma vez
H="docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v $PWD:$PWD -w $PWD catraca-harness"
$H ./scripts/up.sh       # subir (http://localhost:8000)
$H ./scripts/down.sh     # derrubar
$H ./scripts/gates.sh    # gates
```

Para outra porta, passe `-e WEB_PORT=8080` no `docker run`. No Docker Desktop (macOS), `/var/run/docker.sock` já existe por padrão.

## Endereços

| | URL |
|---|---|
| Produto (`$WEB`) | http://localhost:8000 |
| API de parceiros (`$API`) | http://localhost:8000 (rotas em `/api/partner/...`) |

## Credenciais

| Conta | E-mail | Senha |
|---|---|---|
| Organizador A | `org.a@catraca.local` | `catraca123` |
| Organizador B | `org.b@catraca.local` | `catraca123` |
| Participante da seed | `participante@catraca.local` | `catraca123` |
| Chave de parceiro (`$KEY`, cabeçalho `X-Api-Key`) | `catraca-parceiro-2026` | |

```bash
curl -s -H "X-Api-Key: catraca-parceiro-2026" http://localhost:8000/api/partner/events
```

## Cartões de teste (gateway simulado)

O gateway simulado decide pelos 4 últimos dígitos do cartão, conforme o brief ([`docs/enunciado.md`](docs/enunciado.md), seção "Gateway de pagamento simulado"; implementação em [`app/gateway.py`](app/gateway.py)). O cartão precisa ter 16 dígitos; fora disso, a compra é rejeitada antes de criar o ingresso.

| Final | Exemplo | Resultado |
|---|---|---|
| 0001 | `4000000000000001` | aprovado em 2–5 s |
| 0002 | `4000000000000002` | recusado em 2–5 s |
| 0003 | `4000000000000003` | aprovado em 30–40 s |
| 0004 | `4000000000000004` | recusado em 30–40 s |
| qualquer outro | `1111111111111111` | recusado em 2–5 s |

A compra nasce pendente e ocupa a vaga até a resposta do gateway. Recarregue a página para ver o status novo.

## Mapa dos artefatos

| Artefato | Caminho |
|---|---|
| Brief | [`docs/enunciado.md`](docs/enunciado.md) |
| PRD (features, Provê/Consome, grafo, waves, critérios, cross-feature, fora de escopo) | [`docs/PRD.md`](docs/PRD.md) |
| Design aprovado e plano mestre | [`docs/planning/design.md`](docs/planning/design.md), [`docs/planning/master-plan.md`](docs/planning/master-plan.md) |
| Estado do projeto | [`docs/state.json`](docs/state.json) |
| Fluxo do avaliador (passos 1–17) rodado na main, clone limpo | [`docs/evaluation/20261126-final-flow-e7ec2ec.md`](docs/evaluation/20261126-final-flow-e7ec2ec.md) |
| Porta de entrada dos agentes | [`AGENTS.md`](AGENTS.md) ([`CLAUDE.md`](CLAUDE.md) aponta para ele) |
| Receitas de avaliação e template de relatório | [`docs/features/_eval-recipes.md`](docs/features/_eval-recipes.md), [`docs/features/_report-template.md`](docs/features/_report-template.md) |

Cada pasta de feature tem `spec.md`, `plan.md`, `contract.md` e `reports/`:

| ID | Feature | Wave | Pasta | PR |
|---|---|---|---|---|
| F01 | Fundação (harness, contas, acesso) | W1 | [`docs/features/F01-fundacao/`](docs/features/F01-fundacao/) | [#4](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/4) |
| F02 | Eventos do organizador | W2 | [`docs/features/F02-eventos/`](docs/features/F02-eventos/) | [#5](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/5) |
| F03 | Vitrine e compra | W3 | [`docs/features/F03-compra/`](docs/features/F03-compra/) | [#6](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/6) |
| F04 | API de parceiros | W4 | [`docs/features/F04-api-parceiros/`](docs/features/F04-api-parceiros/) | [#7](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/7) |
| F05 | Check-in | **W5 (paralela)** | [`docs/features/F05-checkin/`](docs/features/F05-checkin/) | [#9](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/9) |
| F06 | Cancelamento | **W5 (paralela)** | [`docs/features/F06-cancelamento/`](docs/features/F06-cancelamento/) | [#10](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/10) |
| F07 | Painel | **W5 (paralela)** | [`docs/features/F07-painel/`](docs/features/F07-painel/) | [#8](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/8) |

**PRs da wave paralela W5:** [#8](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/8) (F07), [#9](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/9) (F05), [#10](https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente/pull/10) (F06). As três features foram implementadas ao mesmo tempo, cada uma na própria branch e no próprio worktree. Os primeiros commits caíram entre 17:22:37Z e 17:22:49Z, todos antes dos últimos commits dos outros PRs. Na integração, o conflito em `app/main.py` (registro dos routers de F05 e F06) foi resolvido no PR #10, mantendo os dois.

## Decisões

**Stack: Python 3.12 + FastAPI + Jinja2 (HTML no servidor) + Postgres 16 + psycopg 3 com SQL direto, tudo em docker compose.** O avaliador só tem Docker, Git e Node, então qualquer runtime precisa rodar em container. Um serviço só, com HTML renderizado no servidor, tem menos peças do que uma SPA separada, e nenhum critério avalia design. O Postgres foi escolhido pelo lock de linha que R07 exige. SQL direto deixa os locks explícitos no código.

**R07 sob concorrência.** Toda operação que muda ocupação ou lotação abre uma transação e trava a linha do evento com `SELECT ... FROM events WHERE id=%s FOR UPDATE`:
- a compra, pela vitrine ou pela API ([`app/purchases.py`](app/purchases.py));
- a edição de lotação ([`app/events.py`](app/events.py));
- o cancelamento ([`app/cancellation.py`](app/cancellation.py)).

Com o lock em mãos, a compra conta os ingressos reais `pending` + `confirmed`. Se não houver vaga, responde `sold_out`; se houver, insere o ingresso e faz commit. Compras do mesmo evento entram em fila e eventos diferentes não se bloqueiam. Não existe contador desnormalizado que possa dessincronizar.

A prova está no teste `test_burst_30_capacity_5` (5 rodadas de 30 POSTs simultâneos na API, cada rodada num evento novo de lotação 5, resultando em 5×202 e 25×409) e no `test_concurrent_purchases_never_exceed_capacity` (mesma carga no serviço, com uma conexão do pool por compra). Os dois rodam nos gates. Os avaliadores também repetiram a rajada com `curl` + `xargs -P 30` em 5 eventos novos.

**Resposta assíncrona do gateway** ([`app/gateway.py`](app/gateway.py)):
- Na compra, o gateway simulado decide pelo final do cartão se aprova ou recusa e sorteia o atraso dentro da faixa do brief. A decisão e o prazo (`gateway_due_at`) são gravados no ingresso.
- Depois do commit, uma `asyncio` task do próprio processo dorme até o prazo e roda `UPDATE tickets SET status=... WHERE id=%s AND status='pending'`. Por isso a compra responde na hora, com o ingresso pendente.
- O `WHERE status='pending'` garante que uma resposta que chegue depois do cancelamento não mude o status do ingresso (R11). O cancelamento muda tudo na mesma transação: `confirmed` passa a `refunded` e `pending` passa a `cancelled`.
- No startup, `reschedule_pending()` reagenda os pendentes, então um reinício do container não deixa ingresso preso.
- `GATEWAY_DELAY_SCALE` (padrão `1.0`) só é reduzido nos testes.

**Isolamento da avaliação.** Uma sessão do Claude Code orquestrou o trabalho. Ela não implementou código de produto, só resolveu o conflito de merge da W5. Para cada feature:
1. Um subagente implementador novo (Claude Code, modelo Sonnet) recebeu só `spec.md`, `plan.md` e `contract.md`. Ele implementou com TDD no próprio worktree e abriu o PR, sem permissão para escrever relatório.
2. Outro subagente novo (Claude Code, modelo Opus), de contexto vazio, sem acesso à conversa do implementador, recebeu só o caminho da branch, o sha e o contrato.
3. O avaliador clonou o sha num diretório limpo, subiu o produto numa porta própria e executou cada item do contrato com `curl`, `psql` e gates.
4. Ele escreveu um relatório novo em `reports/<data>-<sha7>.md` e fez commit só desse arquivo.

Relatórios nunca são editados. Cada um aparece em um único commit:

```bash
git log --format="%h %ad" --date=iso -- docs/features/F01-fundacao/reports/
```

O `docs/state.json` aponta para o relatório mais recente de cada feature.

## Regras de entrega

- Um projeto por repositório; tudo na branch `main`.
- Cada feature entrou na `main` por PR com merge commit (sem squash). Os PRs da wave paralela (#8, #9, #10) continuam visíveis no GitHub, mesmo com as branches apagadas depois do merge.
