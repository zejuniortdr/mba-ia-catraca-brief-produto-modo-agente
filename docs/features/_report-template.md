# Relatório de avaliação — FXX <nome>

| Campo | Valor |
|---|---|
| Data | YYYY-MM-DDTHH:MM:SS-03:00 |
| Commit avaliado | `<sha completo>` |
| Branch | `feat/fXX-...` |
| Ferramenta | Claude Code (subagente) |
| Modelo | `<id do modelo>` |
| Isolamento | Subagente novo, contexto vazio, sem acesso à conversa do implementador; recebeu só caminho do worktree, commit e contrato. |
| Contrato | `docs/features/FXX-.../contract.md` |

## Ambiente

Comandos usados para subir (com `WEB_PORT`) e resultado.

## Itens

| Item | Veredito | Evidência |
|---|---|---|
| CTR-FXX-1 | APROVADO / REPROVADO | saída literal (comando + resposta HTTP / trecho de HTML / saída de teste) |

### Evidências detalhadas

Para cada item: o comando exato e a saída relevante, em bloco de código.

## Veredito final

APROVADO (todos os itens) / REPROVADO (listar itens reprovados e o que falhou).
