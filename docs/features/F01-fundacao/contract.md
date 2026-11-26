# F01 — Fundação: contrato

## Pré-requisitos
- Linux com bash, Docker + Compose v2, Git, curl. Porta livre exportada em `WEB_PORT` (padrão 8000).
- Avaliar em um **clone limpo** do commit indicado (`git clone <worktree> /tmp/eval-f01 && git -C /tmp/eval-f01 checkout <sha>`).
- Variáveis e sessões: `docs/features/_eval-recipes.md`.

## Itens

| Item | Como verificar | Esperado |
|---|---|---|
| CTR-F01-1 | No clone limpo: `./scripts/up.sh`; depois `curl -s -o /dev/null -w '%{http_code}' $WEB/healthz` e `$WEB/login` | exit 0; `200` e `200`, sem nenhum outro passo e sem variável de pagamento |
| CTR-F01-2 | Login das 3 contas da seed (receitas) | `303` para cada uma |
| CTR-F01-3 | `./scripts/down.sh`; `curl -s -m 3 $WEB/healthz; echo $?`; `docker compose ps -a -q \| wc -l` | curl falha (exit ≠ 0); contagem `0` |
| CTR-F01-4 | `./scripts/up.sh` de novo; login das 3 contas; `psql -c "select email, count(*) from users group by email having count(*)>1"` | sobe sem erro; `303` ×3; nenhuma linha (sem duplicatas) |
| CTR-F01-5 | `./scripts/gates.sh; echo $?` | saída do ruff sem erros, pytest com testes executados e passando; `0` |
| CTR-F01-6 | Signup (receita) com e-mail novo; `GET /` com o jar mostra o nome; `POST /logout`; `GET /` com o jar sem o nome | `303`; nome visível; depois do logout nome ausente |
| CTR-F01-7 | Signup repetindo o mesmo e-mail | `422` com `E-mail já cadastrado` |
| CTR-F01-8 | Login com senha errada | `401` com `E-mail ou senha inválidos` |
| CTR-F01-9 | `curl -s -o /dev/null -w '%{http_code} %{redirect_url}' $WEB/org/events` sem cookie | `303 .../login` |
| CTR-F01-10 | Mesmo GET com jar do participante | `403` |
| CTR-F01-11 | Mesmo GET com jar do organizador A | `200` |
| CTR-F01-12 | `psql -At -c "select password_hash from users where email='participante@catraca.local'"` | começa com `scrypt$`, não contém `catraca123` |
| CTR-F01-13 | `grep -E 'up.sh\|down.sh\|gates.sh' AGENTS.md`; `grep -i 'mapa' AGENTS.md`; `cat CLAUDE.md` | os três comandos e a seção de mapa presentes; CLAUDE.md aponta para AGENTS.md |
| CTR-F01-14 | `grep -rniE 'stripe\|pagar\.me\|api_key.*pay' compose.yml app/ \|\| echo none`; `grep GATEWAY_DELAY_SCALE compose.yml` | `none`; app com `1.0` |

## Mapeamento PRD → itens

| Critério | Itens |
|---|---|
| F01-AC-1 | CTR-F01-1, CTR-F01-14 |
| F01-AC-2 | CTR-F01-3, CTR-F01-4 |
| F01-AC-3 | CTR-F01-5 |
| F01-AC-4 | CTR-F01-2, CTR-F01-4 |
| F01-AC-5 | CTR-F01-6, CTR-F01-7, CTR-F01-8, CTR-F01-12 |
| F01-AC-6 | CTR-F01-9, CTR-F01-10, CTR-F01-11 |
| F01-AC-7 | CTR-F01-13 |
