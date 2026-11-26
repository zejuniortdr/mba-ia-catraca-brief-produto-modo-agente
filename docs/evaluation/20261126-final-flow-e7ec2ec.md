# Relatório final: Fluxo do avaliador (passos 1 a 17)

- **Data/hora:** 2026-11-26T14:33:52-03:00 (início) a 2026-11-26T14:39:29-03:00 (fim)
- **Commit avaliado:** `e7ec2ecfa118141a8ed6dcaa175f5c9049142003` (`main`, "Merge pull request #11 from zejuniortdr/docs/readme")
- **Ferramenta:** Claude Code (subagente avaliador final)
- **Modelo:** `claude-opus-5-5`
- **Isolamento:** subagente novo, de contexto vazio, sem acesso a quem implementou. Clone limpo do GitHub em `/tmp/catraca-final/repo` (`git clone https://github.com/zejuniortdr/mba-ia-catraca-brief-produto-modo-agente.git`). Na primeira subida o volume do banco foi criado do zero (`Volume repo_pgdata Created`). Nenhum arquivo do repositório foi alterado (`git status --short` vazio ao final).
- **Endereços:** `$WEB=$API=http://localhost:8000`, `$KEY=catraca-parceiro-2026` (README, porta padrão, sem `WEB_PORT`).
- **Método:** as ações de interface foram feitas com `curl` (POST de formulário com cookie jar por pessoa), conferindo o HTML retornado pelos marcadores de `docs/features/_eval-recipes.md`. As datas usadas ficam no mês seguinte: `starts_at=2026-12-15T21:00`. A data passada usada foi `2026-11-25T21:00`. Os atrasos do gateway foram os reais (`GATEWAY_DELAY_SCALE` padrão).

## Resumo

| Passo | Veredito | Evidência (resumo literal) |
|---|---|---|
| 1 | APROVADO | `./scripts/up.sh` saiu com rc=0 e imprimiu `Catraca em http://localhost:8000`. `GET /` deu `200`. Login das 3 contas da seed deu `303`. |
| 2 | APROVADO | Criar E1 deu `303 .../org/events/evt_8b892febf6`. A vitrine contém E1: `0`. API: `[]` |
| 3 | APROVADO | `class="error">Data de início precisa estar no futuro` e `HTTP 422`. O evento não aparece na lista. |
| 4 | APROVADO | Publicar deu `303`. A vitrine mostra `data-event-id="evt_8b892febf6"`. API: `"priceCents":10000,"availableSeats":2` |
| 5 | APROVADO | Signup deu `303`. A compra pela vitrine deu `303 /me/tickets`. O status foi `pendente`, depois `confirmado` em t+3.13s, com código `GDLD5SHI` (C1). |
| 6 | APROVADO | `{"ticketId":"tkt_0ada21e043","code":"G0PPLSGU","status":"pending"}` e `HTTP 202`. A listagem mostra `"availableSeats":0`. |
| 7 | APROVADO | Em t+1s: `{"error":"sold_out"}` e `HTTP 409`. A vitrine mostra `id="sold-out">Ingressos esgotados`. |
| 8 | APROVADO | Em t+45s, T2 tem `"status":"declined"` e a listagem `"availableSeats":1`. T3 (`tkt_66cbf49fee`) ficou `confirmed` em t+3.08s. |
| 9 | APROVADO | Lotação 1 deu `Lotação não pode ser menor que as vagas ocupadas (2)` e `422`. Preço 150 com lotação 3 deu `303`. T4 ficou `confirmed`. Painel: `3/0/0/0/R$ 350,00/0` |
| 10 | APROVADO | `Entrada liberada`, `Ingresso já utilizado`, `Ingresso não confirmado` e `Ingresso inválido para este evento`. Check-ins passou a `1`. |
| 11 | APROVADO | A lista de B não contém E1. O endereço de E1 deu `404` para B, `403` para o participante e `303 /login` deslogado, sem dados de E1 em nenhum caso. E2 foi criado e comprado (`202`, C3=`XEU2SLNB`). C3 em E1 deu `Ingresso inválido para este evento`. |
| 12 | APROVADO | T5 (0003) e T6 (0001) deram `202 pending`. T6 ficou `confirmed` em t+4s. O cancelamento de E3 deu `303` em t+4s desde T5, antes de 30s. |
| 13 | APROVADO | E3 saiu da vitrine e da API (`0`). Compra: `{"error":"event_not_available"} HTTP 404`. Em t+0s: T6 `refunded` e T5 `cancelled`. A gestão não tem mais formulário de edição, e o POST de edição deu `409 Evento cancelado não pode ser editado`. |
| 14 | APROVADO | Em t+45s desde T5, T5 continua `cancelled`. Check-in de C6 deu `Evento cancelado`. Painel: `0/0/0/0/R$ 0,00/1` |
| 15 | APROVADO | 5 rodadas (E4 a E8). Em todas: `5 202` e `25 409`. Painel em t+5s: Confirmados 5, Vagas 0. Banco: `confirmed:5` |
| 16 | APROVADO | 6 combinações (3 rotas, sem chave e com chave errada) deram `{"error":"unauthorized"} 401`. `cardNumber:"123"` deu `{"error":"invalid_request"} 422`. Ticket inexistente deu `{"error":"ticket_not_found"} 404`. |
| 17 | APROVADO | Gates: rc=0, `All checks passed!`, `141 passed in 41.09s`. Down: `curl 8000` deu `000` (rc=7) e `docker ps` ficou vazio. A segunda subida deu rc=0, a seed continuou funcionando (3 logins `303`) e não houve `error/traceback` nos logs do app. |

## Evidências detalhadas

### Passo 1: subida
```
$ git rev-parse HEAD
e7ec2ecfa118141a8ed6dcaa175f5c9049142003
$ ./scripts/up.sh      # rc=0, 7s
 Volume repo_pgdata Created
Catraca em http://localhost:8000
$ curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/
200
login org.a 303 http://localhost:8000/org/events
login org.b 303 http://localhost:8000/org/events
login participante 303 http://localhost:8000/
```

### Passos 2 e 3: rascunho oculto e data passada
```
create E1: 303 http://localhost:8000/org/events/evt_8b892febf6
vitrine contém E1? 0
API contém E1? 0
$ curl -s -H "X-Api-Key: $KEY" "$API/api/partner/events"
[]
# POST /org/events/new starts_at=2026-11-25T21:00
class="error">Data de início precisa estar no futuro
HTTP 422
evento 'Ontem' na lista do org A: 0
```

### Passos 4 e 5: publicação e compra pela vitrine
```
publish 303
vitrine: data-event-id="evt_8b892febf6"
[{"id":"evt_8b892febf6","name":"E1 Final Flow","startsAt":"2026-12-15T21:00:00-03:00","priceCents":10000,"availableSeats":2}]
signup 303 http://localhost:8000/
id="buy-form"
buy 303 http://localhost:8000/me/tickets
<tr data-ticket-id="tkt_4f0e205742"><td class="event">E1 Final Flow</td><td class="status">pendente</td><td class="code">GDLD5SHI</td></tr>
t+1.06s ... pendente ...
t+2.09s ... pendente ...
t+3.13s <tr data-ticket-id="tkt_4f0e205742"><td class="event">E1 Final Flow</td><td class="status">confirmado</td><td class="code">GDLD5SHI</td></tr>
```

### Passos 6 a 8: pendente ocupa vaga e recusa libera
```
[6] 14:34:57
{"ticketId":"tkt_0ada21e043","code":"G0PPLSGU","status":"pending"}
HTTP 202
[{"id":"evt_8b892febf6",...,"priceCents":10000,"availableSeats":0}]
[7] t+1s
{"error":"sold_out"}
HTTP 409
vitrine (participante passo 5): id="sold-out">Ingressos esgotados  t+1s
{"ticketId":"tkt_0ada21e043",...,"status":"pending","checkedIn":false}   (ainda pendente em t+1s)
[8] t+45s
{"ticketId":"tkt_0ada21e043","code":"G0PPLSGU","eventId":"evt_8b892febf6","status":"declined","checkedIn":false}
[{"id":"evt_8b892febf6",...,"availableSeats":1}]
{"ticketId":"tkt_66cbf49fee","code":"8AB93BNG","status":"pending"}  HTTP 202
t+3.08s {"ticketId":"tkt_66cbf49fee",...,"status":"confirmed","checkedIn":false}
```

### Passo 9: lotação, preço vigente e painel
```
[9a] reduzir lotação p/ 1:
class="error">Lotação não pode ser menor que as vagas ocupadas (2)
422
[9b] preço 150 + lotação 3:
303
[{"id":"evt_8b892febf6",...,"priceCents":15000,"availableSeats":1}]
{"ticketId":"tkt_599c75bb15","code":"9U8ZHM1L","status":"pending"}  HTTP 202
t+5s {"ticketId":"tkt_599c75bb15",...,"status":"confirmed"}
data-metric="confirmed">3
data-metric="pending">0
data-metric="checkins">0
data-metric="available">0
data-metric="revenue">R$ 350,00
data-metric="refunded">0
# banco (status|checked_in|price_cents)
confirmed|f|10000
declined|f|10000
confirmed|f|10000
confirmed|f|15000
```
A receita confere com o banco: 100 + 100 + 150 = R$ 350,00.

### Passo 10: check-in
```
GDLD5SHI -> id="checkin-result">Entrada liberada
GDLD5SHI -> id="checkin-result">Ingresso já utilizado
G0PPLSGU -> id="checkin-result">Ingresso não confirmado
ZZZZZZZZ -> id="checkin-result">Ingresso inválido para este evento
data-metric="checkins">1
URL=http://localhost:8000/org/events/evt_8b892febf6
```

### Passo 11: isolamento entre organizadores
```
[B lista] contém E1? 0
[B URL] HTTP 404
  nome/código/metric presentes: 0
create E2: 303 http://localhost:8000/org/events/evt_2454b165ee
publish E2 303
[{"id":"evt_8b892febf6",...},{"id":"evt_2454b165ee","name":"E2 Org B",...,"priceCents":2000,"availableSeats":1}]
E2 via API=evt_2454b165ee
{"ticketId":"tkt_072bd31b1d","code":"XEU2SLNB","status":"pending"} HTTP 202
[participante URL] HTTP 403
  dados E1: 0
[deslogado URL] HTTP 303 http://localhost:8000/login
  dados E1: 0
[A] C3=XEU2SLNB -> id="checkin-result">Ingresso inválido para este evento
[B POST checkin E1] HTTP 404     (verificação extra)
```

### Passos 12 a 14: cancelamento
```
create E3: 303 http://localhost:8000/org/events/evt_f093e4f1d9
publish 303
gestão E3 aberta: edit-links=1
T5: {"ticketId":"tkt_6f4e5cb683","code":"5S8XVIN3","status":"pending"} HTTP 202
T6: {"ticketId":"tkt_d4618bd1c0","code":"PZAVNU5J","status":"pending"} HTTP 202
T6 t+4s {"ticketId":"tkt_d4618bd1c0",...,"status":"confirmed","checkedIn":false}
T5 antes do cancel: {...,"status":"pending",...}
[12] cancel E3 303 em t+4s desde T5
[13] vitrine contém E3? 0
[13] API contém E3? 0
{"error":"event_not_available"} HTTP 404
t+0s após cancel: T6={"ticketId":"tkt_d4618bd1c0",...,"status":"refunded","checkedIn":false}
   T5={"ticketId":"tkt_6f4e5cb683",...,"status":"cancelled","checkedIn":false}
gestão E3 pós-cancel: edit-links=0, form edição=0
POST edit: 409  class="error">Evento cancelado não pode ser editado
Este evento foi cancelado.
[14] t+45s T5: {"ticketId":"tkt_6f4e5cb683",...,"status":"cancelled","checkedIn":false}
POST checkin C6: id="checkin-result">Evento cancelado
data-metric="confirmed">0
data-metric="pending">0
data-metric="checkins">0
data-metric="available">0
data-metric="revenue">R$ 0,00
data-metric="refunded">1
# banco
cancelled|f|5000
refunded|f|5000
```
Depois do cancelamento, a página de E3 mantém o campo de check-in, e o check-in devolve `Evento cancelado`, conforme R10.

### Passo 15: rajada R07 (5 rodadas)
```
== Rodada E4 (evt_548e981c0f)
      5 202
     25 409
  painel t+5s: confirmed">5 pending">0 checkins">0 available">0 revenue">R$ 50,00 refunded">0   DB: confirmed:5
== Rodada E5 (evt_74d04968ea)
      5 202
     25 409
  painel t+5s: confirmed">5 ... available">0 ...   DB: confirmed:5
== Rodada E6 (evt_1f609d41f7)
      5 202
     25 409
  painel t+5s: confirmed">5 ... available">0 ...   DB: confirmed:5
== Rodada E7 (evt_1197fbe426)
      5 202
     25 409
  painel t+5s: confirmed">5 ... available">0 ...   DB: confirmed:5
== Rodada E8 (evt_7b04033642)
      5 202
     25 409
  painel t+5s: confirmed">5 ... available">0 ...   DB: confirmed:5
```
O comando foi o do enunciado (`seq 30 | xargs -P 30 ... | sort | uniq -c`). Os e-mails tinham sufixo por rodada.

### Passo 16: autenticação e erros
```
[none] GET events: {"error":"unauthorized"} 401
[none] POST purchase: {"error":"unauthorized"} 401
[none] GET ticket: {"error":"unauthorized"} 401
[wrong] GET events: {"error":"unauthorized"} 401
[wrong] POST purchase: {"error":"unauthorized"} 401
[wrong] GET ticket: {"error":"unauthorized"} 401
card 123: {"error":"invalid_request"} 422
ticket inexistente: {"error":"ticket_not_found"} 404
```

### Passo 17: gates, derrubar e subir de novo
```
$ ./scripts/gates.sh     # rc=0, 47s
All checks passed!
141 passed in 41.09s
$ docker ps   (antes do down)
repo-app-1 0.0.0.0:8000->8000/tcp
repo-db-1 5432/tcp
$ ./scripts/down.sh      # rc=0
 Network repo_default Removed
$ curl -s -m 3 http://localhost:8000/
curl 8000: 000   (rc=7, conexão recusada)
$ docker ps
(vazio)
$ docker compose ls
NAME  STATUS  CONFIG FILES   (vazio)
$ ./scripts/up.sh        # rc=0
Catraca em http://localhost:8000
login org.a 303 http://localhost:8000/org/events
login org.b 303 http://localhost:8000/org/events
login participante 303 http://localhost:8000/
login senha errada 401   (controle negativo)
E1 ainda presente para A (volume mantido): 1
erros/tracebacks no log do app após re-subida: 0
```
Ao final foi rodado `./scripts/down.sh` de novo: rc=0, `docker ps -q` vazio e `curl` na 8000 com rc=7.

## Veredito final

**APROVADO.** Os 17 passos do Fluxo do avaliador passaram na `main` em `e7ec2ec`, a partir de um clone limpo e com os atrasos reais do gateway. Nenhum passo foi reprovado. O passo 18 (conferência documental) estava fora do escopo desta execução.
