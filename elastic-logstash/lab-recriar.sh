#!/bin/bash
ES=localhost:9200
OUT="$1"
: > "$OUT"

req() {
  local method="$1" path="$2" body="$3" titulo="$4"
  {
    echo ""
    echo "### $titulo"
    echo ""
    echo '```'
    echo "$method $path"
    [ -n "$body" ] && echo "$body"
    echo '```'
    echo ""
    echo "**Resposta:**"
    echo ""
    echo '```json'
    if [ -n "$body" ]; then
      curl -s -X "$method" "$ES/$path" -H 'Content-Type: application/json' -d "$body" | python3 -m json.tool
    else
      curl -s -X "$method" "$ES/$path" | python3 -m json.tool
    fi
    echo '```'
  } >> "$OUT"
  echo "OK: $titulo"
}

echo "# Lab 2 – Elastic – Parte 1 – Evidências de execução" >> "$OUT"
echo "" >> "$OUT"
echo "Executado em $(date '+%d/%m/%Y %H:%M') · Elasticsearch 8.15.3 · macOS/OrbStack" >> "$OUT"
echo "" >> "$OUT"
echo "## PARTE 6 – Templates de índice" >> "$OUT"

req PUT "_template/meu_template" '{
  "index_patterns": ["meu_indice-*"],
  "settings": { "index.lifecycle.name": "minha_politica", "index.lifecycle.rollover_alias": "meu_indice" },
  "mappings": { "properties": {
    "nome": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
    "idade": { "type": "integer" },
    "cidade": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } }
  } }
}' "Template genérico (meu_template)"

req PUT "_template/transacoes_template" '{
  "index_patterns": ["transacoes-*"],
  "settings": { "index.lifecycle.name": "politica_transacoes", "index.lifecycle.rollover_alias": "transacoes" },
  "mappings": { "properties": {
    "usuario": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
    "valor": { "type": "double" },
    "tipo": { "type": "keyword" },
    "data": { "type": "date", "format": "strict_date_optional_time||epoch_millis" }
  } }
}' "Template de transações (transacoes_template)"

echo "" >> "$OUT"; echo "## PARTE 7 – Índices com alias" >> "$OUT"
req PUT "meu_indice-000001" '{ "aliases": { "meu_indice": { "is_write_index": true } } }' "Índice meu_indice-000001 + alias"
req PUT "transacoes-000001" '{ "aliases": { "transacoes": { "is_write_index": true } } }' "Índice transacoes-000001 + alias"

echo "" >> "$OUT"; echo "## PARTE 8 – Inserção de documentos" >> "$OUT"
req POST "meu_indice-000001/_doc/1?refresh=true" '{ "nome": "João Silva", "idade": 30, "cidade": "Brasília" }' "Insere pessoa 1"
req POST "meu_indice-000001/_doc/2?refresh=true" '{ "nome": "Maria Souza", "idade": 25, "cidade": "São Paulo" }' "Insere pessoa 2"
req POST "transacoes-000001/_doc/1?refresh=true" '{ "usuario": "João Silva", "valor": 150.75, "tipo": "compra", "data": "2025-03-19T12:00:00" }' "Insere transação 1"
req POST "transacoes-000001/_doc/2?refresh=true" '{ "usuario": "Maria Souza", "valor": 200.50, "tipo": "venda", "data": "2025-03-18T10:30:00" }' "Insere transação 2"

echo "" >> "$OUT"; echo "## PARTE 9 – Consultas" >> "$OUT"
req GET "meu_indice/_doc/1" "" "Busca por ID (via alias)"
req GET "transacoes/_doc/2" "" "Busca por ID em transações"
req GET "meu_indice-000001/_search" '{ "query": { "match": { "nome": "João" } } }' "Full-text (match)"
req GET "transacoes/_search" '{ "query": { "range": { "valor": { "gte": 100 } } } }' "Intervalo numérico (range)"
req GET "meu_indice/_search" '{ "query": { "bool": { "must": [ { "match": { "cidade": "Brasília" } } ], "filter": [ { "range": { "idade": { "gte": 30 } } } ] } } }' "Composta (bool: must + filter)"

echo "" >> "$OUT"; echo "## PARTE 10 – Atualização" >> "$OUT"
req POST "meu_indice/_update/1?refresh=true" '{ "doc": { "idade": 31 } }' "Atualiza idade 30 -> 31"
req POST "transacoes/_update/1?refresh=true" '{ "doc": { "valor": 160.00 } }' "Atualiza valor 150.75 -> 160.00"
req GET "meu_indice/_doc/1" "" "Confirma atualização (idade = 31)"
req GET "transacoes/_doc/1" "" "Confirma atualização (valor = 160.0)"
