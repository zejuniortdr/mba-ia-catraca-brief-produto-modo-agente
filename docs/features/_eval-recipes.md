# Receitas de avaliação (curl)

Escritas pelo orquestrador, não pelos implementadores. Os contratos referenciam estas receitas. Comandos para Linux (GNU `date`).

## Variáveis

```bash
export WEB_PORT=${WEB_PORT:-8000}
WEB=http://localhost:$WEB_PORT; API=$WEB; KEY=catraca-parceiro-2026
FUT=$(date -d '+30 days' +%Y-%m-%dT21:00)      # data futura no formato do formulário
PAST=$(date -d '-1 day' +%Y-%m-%dT21:00)
J=$(mktemp -d)                                   # pasta dos cookie jars
```

## Sessões

```bash
# login (303 = ok). Cookie jar por pessoa.
curl -s -c $J/a.jar -o /dev/null -w '%{http_code}\n' -X POST $WEB/login -d 'email=org.a@catraca.local&password=catraca123'
curl -s -c $J/b.jar -o /dev/null -w '%{http_code}\n' -X POST $WEB/login -d 'email=org.b@catraca.local&password=catraca123'
curl -s -c $J/p.jar -o /dev/null -w '%{http_code}\n' -X POST $WEB/login -d 'email=participante@catraca.local&password=catraca123'
# cadastro de participante novo (303 = ok, já entra logado)
curl -s -c $J/n.jar -o /dev/null -w '%{http_code}\n' -X POST $WEB/signup --data-urlencode 'name=Nova Pessoa' -d "email=nova$RANDOM@example.com&password=segredo123"
# logout
curl -s -b $J/n.jar -c $J/n.jar -o /dev/null -w '%{http_code}\n' -X POST $WEB/logout
```

## Eventos (organizador)

```bash
# criar (303 para /org/events/<id>); EID recebe o id
R=$(curl -s -b $J/a.jar -o /dev/null -w '%{http_code} %{redirect_url}' -X POST $WEB/org/events/new \
  --data-urlencode 'name=Jazz no Porão' -d "starts_at=$FUT" --data-urlencode 'venue=Bar do Zé' -d 'capacity=2' -d 'price=100,00')
echo $R; EID=${R##*/}
# publicar (303)
curl -s -b $J/a.jar -o /dev/null -w '%{http_code}\n' -X POST $WEB/org/events/$EID/publish
# editar (303 ok; 422 rejeitado, motivo em <p class="error">)
curl -s -b $J/a.jar -w '\n%{http_code}\n' -X POST $WEB/org/events/$EID/edit \
  --data-urlencode 'name=Jazz no Porão' -d "starts_at=$FUT" --data-urlencode 'venue=Bar do Zé' -d 'capacity=3' -d 'price=150,00' | grep -o 'class="error">[^<]*\|^[0-9]\{3\}$'
# página de gestão
curl -s -b $J/a.jar $WEB/org/events/$EID
# cancelar (303)
curl -s -b $J/a.jar -o /dev/null -w '%{http_code}\n' -X POST $WEB/org/events/$EID/cancel
# check-in: imprime a mensagem
curl -s -b $J/a.jar -X POST $WEB/org/events/$EID/checkin -d 'code=ZZZZZZZZ' | grep -o 'id="checkin-result">[^<]*'
# painel: imprime as métricas
curl -s -b $J/a.jar $WEB/org/events/$EID | grep -o 'data-metric="[a-z]*">[^<]*'
```

## Vitrine (participante)

```bash
curl -s $WEB/ | grep -o 'data-event-id="[^"]*"'
curl -s -b $J/p.jar $WEB/events/$EID | grep -o 'id="sold-out">[^<]*\|id="buy-form"'
curl -s -b $J/p.jar -o /dev/null -w '%{http_code} %{redirect_url}\n' -X POST $WEB/events/$EID/buy -d 'card_number=4000000000000001'
curl -s -b $J/p.jar $WEB/me/tickets | grep -o '<tr data-ticket-id.*</tr>'
```

## API de parceiros

```bash
curl -s -H "X-Api-Key: $KEY" $API/api/partner/events
curl -s -w '\n%{http_code}\n' -X POST $API/api/partner/events/$EID/purchases -H "X-Api-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"buyerEmail":"t2@example.com","cardNumber":"4000000000000004"}'
curl -s -w '\n%{http_code}\n' -H "X-Api-Key: $KEY" $API/api/partner/tickets/$TID
# rajada R07
seq 30 | xargs -P 30 -I{} curl -s -o /dev/null -w "%{http_code}\n" -X POST "$API/api/partner/events/$EID/purchases" \
  -H "X-Api-Key: $KEY" -H "Content-Type: application/json" -d '{"buyerEmail":"carga{}@example.com","cardNumber":"4000000000000001"}' | sort | uniq -c
```

## Banco

```bash
docker compose exec -T db psql -U catraca -d catraca -At -c "select status, checked_in, price_cents from tickets where event_id='$EID'"
```
