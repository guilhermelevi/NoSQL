#!/bin/bash
# Insere um documento no MongoDB e acompanha ele chegar no Elasticsearch.
# Serve para demonstrar a integracao ao vivo.
# uso: ./demo.sh [nome-do-cliente]
set -u
cd "$(dirname "$0")"

MARCA="${1:-DEMO-$(date +%H%M%S)}"
MONGO="docker exec mongodb-container mongosh --quiet -u admin -p 123456 --authenticationDatabase admin"

# o log de todas as operacoes some a cada restart do Mongo, entao garante aqui
SLOW=$($MONGO --eval 'print(db.getSiblingDB("demo").getProfilingStatus().slowms)' 2>/dev/null | tr -d '\r')
if [ "$SLOW" != "0" ]; then
  $MONGO --eval 'db.getSiblingDB("demo").setProfilingLevel(0, { slowms: 0 })' >/dev/null 2>&1
  echo "  (liguei o log de todas as operacoes, tinha voltado para slowms=$SLOW)"
fi

echo ""
echo "1. gravando no MongoDB"
echo ""
echo "   db.pedidos.insertOne({ cliente: \"$MARCA\", valor: 1234.56 })"
$MONGO --eval "
  const r = db.getSiblingDB('demo').pedidos.insertOne({ cliente: '$MARCA', valor: 1234.56, data: new Date() });
  print('   _id: ' + r.insertedId);
" 2>/dev/null

echo ""
echo "2. procurando no Elasticsearch"
echo ""
for i in $(seq 1 20); do
  N=$(curl -s "localhost:9200/mongodb-logs-*/_search" -H 'Content-Type: application/json' \
      -d "{\"size\":0,\"query\":{\"match_phrase\":{\"message\":\"$MARCA\"}}}" 2>/dev/null \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['hits']['total']['value'])" 2>/dev/null || echo 0)
  if [ "${N:-0}" -gt 0 ] 2>/dev/null; then
    echo "   chegou depois de ${i}x2 = $((i*2))s, $N documento(s)"
    break
  fi
  sleep 2
done

if [ "${N:-0}" -eq 0 ] 2>/dev/null; then
  echo "   nao chegou. Confira se o Logstash esta no ar: docker ps | grep logstash"
  exit 1
fi

echo ""
echo "3. o que o Elasticsearch guardou"
echo ""
curl -s "localhost:9200/mongodb-logs-*/_search" -H 'Content-Type: application/json' \
  -d "{\"size\":1,\"sort\":[{\"@timestamp\":\"desc\"}],\"query\":{\"match_phrase\":{\"message\":\"$MARCA\"}}}" \
  | python3 -c "
import sys, json
hit = json.load(sys.stdin)['hits']['hits'][0]
h = hit['_source']
m = json.loads(h['message'])
print('   indice     :', hit['_index'])
print('   container  :', h.get('container_name'))
print('   hora       :', m.get('t', {}).get('\$date', ''))
print('   comando    :', str(m.get('attr', {}).get('command', ''))[:150])
"

echo ""
echo "4. agora no Kibana"
echo ""
echo "   http://localhost:5601  ->  Discover  ->  busque:  $MARCA"
echo "   (period: Last 15 minutes, e clique em Refresh)"
echo ""
