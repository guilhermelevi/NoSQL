#!/bin/bash
# Sobe os tres laboratorios integrados e deixa o ambiente pronto para demonstrar.
# uso: ./subir.sh
set -u
cd "$(dirname "$0")"

MONGO="docker exec mongodb-container mongosh --quiet -u admin -p 123456 --authenticationDatabase admin"

ok()   { printf "  \033[32mok\033[0m    %s\n" "$1"; }
espera(){ printf "  ...   %s" "$1"; }
fim()  { printf "\r  \033[32mok\033[0m    %s          \n" "$1"; }
erro() { printf "  \033[31mfalhou\033[0m %s\n" "$1"; }

echo ""
echo "SUBINDO O AMBIENTE"
echo ""

# ---------- 1. Docker ----------
if ! docker info >/dev/null 2>&1; then
  espera "iniciando o OrbStack"
  open -a OrbStack 2>/dev/null
  for i in $(seq 1 60); do docker info >/dev/null 2>&1 && break; sleep 2; done
  docker info >/dev/null 2>&1 || { erro "Docker nao subiu"; exit 1; }
  fim "OrbStack no ar"
else
  ok "Docker ja estava no ar"
fi

# ---------- 2. Elastic primeiro ----------
# O Logstash precisa estar escutando na 12201 antes do Mongo subir,
# senao os logs desse intervalo se perdem (GELF e UDP, nao tem buffer).
espera "subindo Elasticsearch, Kibana e Logstash"
(cd lab02-elastic && docker compose up -d) >/dev/null 2>&1
for i in $(seq 1 90); do curl -sf localhost:9200/_cluster/health >/dev/null 2>&1 && break; sleep 2; done
fim "Elasticsearch respondendo"

espera "subindo Redis e RedisInsight"
(cd lab03-redis && docker compose up -d) >/dev/null 2>&1
for i in $(seq 1 60); do docker exec redis redis-cli PING >/dev/null 2>&1 && break; sleep 1; done
fim "Redis respondendo"

espera "subindo MongoDB"
(cd lab01-mongodb && docker compose up -d) >/dev/null 2>&1
for i in $(seq 1 90); do $MONGO --eval "db.adminCommand('ping').ok" 2>/dev/null | grep -q 1 && break; sleep 2; done
fim "MongoDB respondendo"

espera "aguardando o Kibana (costuma demorar ~1 min)"
for i in $(seq 1 120); do
  [ "$(curl -s localhost:5601/api/status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin)["status"]["overall"]["level"])' 2>/dev/null)" = "available" ] && break
  sleep 3
done
fim "Kibana disponivel"

echo ""
echo "INTEGRANDO"
echo ""

# ---------- 3. log de todas as operacoes ----------
# Sem isto o insert nao gera linha de log e a demo mostra so ruido de conexao.
# Some a cada restart do Mongo, por isso e refeito aqui toda vez.
$MONGO --eval 'db.getSiblingDB("demo").setProfilingLevel(0, { slowms: 0 })' >/dev/null 2>&1
SLOW=$($MONGO --eval 'print(db.getSiblingDB("demo").getProfilingStatus().slowms)' 2>/dev/null | tr -d '\r')
[ "$SLOW" = "0" ] && ok "MongoDB registrando todas as operacoes do banco demo" \
                  || erro "slowms ficou em $SLOW, o insert nao vai aparecer no log"

# ---------- 4. data view no Kibana ----------
if curl -s "localhost:5601/api/data_views" -H "kbn-xsrf: true" | grep -q "mongodb-logs-\*"; then
  ok "Kibana com a data view mongodb-logs-*"
else
  curl -s -X POST "localhost:5601/api/data_views/data_view" -H "kbn-xsrf: true" \
    -H "Content-Type: application/json" \
    -d '{"data_view":{"title":"mongodb-logs-*","name":"mongodb-logs-*","timeFieldName":"@timestamp"}}' >/dev/null
  ok "Kibana: data view mongodb-logs-* criada"
fi

# ---------- 5. Redis no RedisInsight ----------
if curl -s localhost:5540/api/databases 2>/dev/null | grep -q '"host":"redis"'; then
  ok "RedisInsight ja conectado ao Redis"
else
  curl -s -X POST localhost:5540/api/databases -H "Content-Type: application/json" \
    -d '{"name":"Redis Lab 3","host":"redis","port":6379,"username":"","password":"","tls":false}' >/dev/null
  ok "RedisInsight: conexao com o Redis registrada"
fi

# ---------- 6. conteudo de demonstracao no Redis ----------
# O lab 3 termina limpando o banco, entao o RedisInsight abriria sem nada
# para mostrar. Cria um conjunto com prefixo demo: so quando estiver vazio.
if [ -z "$(docker exec redis redis-cli --scan --pattern 'demo:*' | head -1)" ]; then
  docker exec -i redis redis-cli >/dev/null 2>&1 <<'REDIS'
SET demo:cache:pagina:/home "<html>HOME</html>" EX 3600
SET demo:contador:visitas 1042
HSET demo:user:1001 nome "Guilherme Levi" curso "Engenharia de Software" cidade "Brasilia"
HSET demo:user:1002 nome "Ana Ribeiro" curso "Ciencia de Dados" cidade "Sao Paulo"
RPUSH demo:fila:emails "email:boas-vindas" "email:confirmacao" "email:nota-fiscal"
SADD demo:tags:redis "cache" "fila" "ranking" "sessao"
ZADD demo:ranking:turma 9.0 "Diana" 8.0 "Bruno" 8.0 "Carlos" 7.5 "Ana" 5.5 "Eduardo"
XADD demo:stream:pedidos * pedido_id 1001 status novo
XADD demo:stream:pedidos * pedido_id 1002 status pago
REDIS
  ok "Redis populado com chaves demo: ($(docker exec redis redis-cli DBSIZE | tr -d '\r') chaves, uma de cada estrutura)"
else
  ok "Redis com $(docker exec redis redis-cli DBSIZE | tr -d '\r') chaves"
fi

# ---------- 7. confere o caminho do log de ponta a ponta ----------
espera "testando o caminho Mongo -> Logstash -> Elasticsearch"
ANTES=$(curl -s "localhost:9200/mongodb-logs-*/_count" 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo 0)
$MONGO --eval 'db.getSiblingDB("demo").ensaio.insertOne({marca:"ENSAIO-SUBIR", quando:new Date()})' >/dev/null 2>&1
for i in $(seq 1 20); do
  N=$(curl -s "localhost:9200/mongodb-logs-*/_search" -H 'Content-Type: application/json' \
      -d '{"size":0,"query":{"match_phrase":{"message":"ENSAIO-SUBIR"}}}' 2>/dev/null \
      | python3 -c "import sys,json;print(json.load(sys.stdin)['hits']['total']['value'])" 2>/dev/null || echo 0)
  [ "$N" -gt 0 ] 2>/dev/null && break
  sleep 2
done
if [ "${N:-0}" -gt 0 ] 2>/dev/null; then
  fim "caminho do log funcionando (insert chegou no Elasticsearch)"
else
  printf "\r"; erro "o insert nao chegou no Elasticsearch"
fi

TOTAL=$(curl -s "localhost:9200/mongodb-logs-*/_count" 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin).get('count',0))" 2>/dev/null)

echo ""
echo "PRONTO"
echo ""
echo "  ABRE NO NAVEGADOR"
echo "    Kibana         http://localhost:5601    Discover > mongodb-logs-* > Last 15 minutes"
echo "    RedisInsight   http://localhost:5540    ja conectado, clique em Redis Lab 3"
echo "    Elasticsearch  http://localhost:9200    $TOTAL documentos de log"
echo ""
echo "  NAO ABRE NO NAVEGADOR (protocolo binario, precisa de cliente)"
echo "    MongoDB        extensao do VS Code, folha verde na barra lateral:"
echo "                   mongodb://admin:123456@localhost:27017/?authSource=admin"
echo "                   ou: docker exec -it mongodb-container mongosh -u admin -p 123456 --authenticationDatabase admin"
echo "    Redis          use o RedisInsight acima"
echo "                   ou: docker exec -it redis redis-cli"
echo ""
echo "  Para demonstrar:  ./demo.sh"
echo ""
