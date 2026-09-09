#!/bin/bash
ES=localhost:9200
OUT="$1"
SP="$(dirname "$0")"
: > "$OUT"

sec()  { { echo ""; echo "## $1"; } >> "$OUT"; }
sub()  { { echo ""; echo "### $1"; } >> "$OUT"; }
nota() { { echo ""; echo "> $1"; } >> "$OUT"; }

req() {
  local method="$1" path="$2" body="$3" titulo="$4"
  sub "$titulo"
  { echo ""; echo '```'; echo "$method $path"; [ -n "$body" ] && echo "$body"; echo '```'; echo ""; echo "**Resposta:**"; echo ""; echo '```json'
    if [ -n "$body" ]; then
      curl -s -X "$method" "$ES/$path" -H 'Content-Type: application/json' -d "$body" | python3 -m json.tool
    else
      curl -s -X "$method" "$ES/$path" | python3 -m json.tool
    fi
    echo '```'; } >> "$OUT"
  echo "OK: $titulo"
}

cat_req() {
  local path="$1" titulo="$2"
  sub "$titulo"
  { echo ""; echo '```'; echo "GET $path"; echo '```'; echo ""; echo "**Resposta:**"; echo ""; echo '```'
    curl -s "$ES/$path"
    echo '```'; } >> "$OUT"
  echo "OK: $titulo"
}

bulk_req() {
  local file="$1" titulo="$2"
  sub "$titulo"
  { echo ""; echo '```'; echo "POST _bulk  (arquivo NDJSON: $(basename "$file"), $(grep -c '"_index"' "$file") documentos)"; echo '```'; echo ""; echo "**Resposta (resumida):**"; echo ""; echo '```json'
    curl -s -X POST "$ES/_bulk" -H 'Content-Type: application/x-ndjson' --data-binary "@$file" \
      | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(json.dumps({'took': d['took'], 'errors': d['errors'], 'total_itens': len(d['items']),
 'resultados': sorted(set(i['index']['result'] for i in d['items'])),
 'status_codes': sorted(set(i['index']['status'] for i in d['items'])),
 'primeiro_item': d['items'][0]}, indent=2, ensure_ascii=False))"
    echo '```'; } >> "$OUT"
  echo "OK: $titulo"
}

echo "# LAB 04 – Partes 12, 13 e 14 – Evidências de execução" >> "$OUT"
echo "" >> "$OUT"
echo "Executado em $(date '+%d/%m/%Y %H:%M') · Elasticsearch 8.15.3 · macOS/OrbStack (1 nó)" >> "$OUT"

# ---------------- PARTE 12 ----------------
sec "PARTE 12 – Arquitetura e engine de busca"

sub "12.1 – Cluster, node, index, shard e replica"
req GET "_cluster/health" "" "Saúde do cluster"
cat_req "_cat/nodes?v" "Nós do cluster"
cat_req "_cat/shards/meu_indice-000001,transacoes-000001?v" "Shards dos índices do lab"
nota "Status **yellow**: com 1 nó só, as replicas ficam \`unassigned\` (não há segundo nó para hospedá-las). Em produção, com 2+ nós, elas seriam alocadas e o status viraria green."

sub "12.3 – Analyzer: tokenização e normalização"
req POST "_analyze" '{ "analyzer": "standard", "text": "JOÃO, da Silva; em BRASÍLIA!" }' "Analyzer standard"
nota "Repare: vira minúsculo e a pontuação some. É por isso que \`match: \"joao\"\` acha \"João\" — os dois passam pelo mesmo analyzer na indexação e na busca."

sub "12.4 – match vs term"
req GET "meu_indice/_search" '{ "query": { "match": { "nome": "João" } } }' "match (analisado)"
req GET "meu_indice/_search" '{ "query": { "term": { "cidade.keyword": "Brasília" } } }' "term (exato, sub-campo keyword)"

sub "12.5 – must vs filter"
req GET "meu_indice/_search" '{ "query": { "bool": { "must": [ { "match": { "nome": "João" } } ], "filter": [ { "term": { "cidade.keyword": "Brasília" } }, { "range": { "idade": { "gte": 30 } } } ] } } }' "bool: must + filter"

sub "12.6 – Score e BM25"
req GET "meu_indice/_search" '{ "query": { "match": { "nome": "João" } }, "explain": true }' "match com explain (BM25)"

sub "12.7 – Near real-time e refresh"
req GET "meu_indice/_settings" "" "Settings do índice"
req POST "meu_indice/_refresh" "" "Refresh forçado"

sub "12.8 – Bulk API (pessoas)"
bulk_req "$SP/bulk_pessoas.ndjson" "Bulk: 20 pessoas em meu_indice"
req POST "meu_indice/_refresh" "" "Refresh após bulk"
cat_req "_cat/indices/meu_indice-000001?v" "Contagem após bulk"

sub "12.9 – Aggregations"
bulk_req "$SP/bulk_transacoes.ndjson" "Bulk: 20 transações"
req POST "transacoes/_refresh" "" "Refresh após bulk"
req GET "transacoes/_search" '{ "size": 0, "aggs": { "total_por_tipo": { "terms": { "field": "tipo" } } } }' "Agregação: contagem por tipo"
req GET "transacoes/_search" '{ "size": 0, "aggs": { "valor_medio": { "avg": { "field": "valor" } } } }' "Agregação: valor médio"

# ---------------- PARTE 13 ----------------
sec "PARTE 13 – Busca vetorial (conceitos)"
nota "As seções 13.1, 13.5, 13.7 e 13.8 são conceituais (sem comandos). 13.3, 13.4 e 13.6 são marcadas como ilustrativas no roteiro porque os vetores estão truncados com \`...\`. Executamos aqui apenas 13.2, que é executável."

sub "13.2 – Campo dense_vector (dims 384)"
curl -s -X DELETE "$ES/documentos_vetoriais" > /dev/null
req PUT "documentos_vetoriais" '{ "mappings": { "properties": { "texto": { "type": "text" }, "embedding": { "type": "dense_vector", "dims": 384 } } } }' "Cria índice com dense_vector de 384 dimensões"
req GET "documentos_vetoriais/_mapping" "" "Mapping resultante"
nota "**Diferença de versão importante:** o roteiro foi escrito para ES 7.x, onde \`dense_vector\` só aceitava \`dims\`. Estamos no **ES 8.15**, então o campo ganhou \`index: true\` e \`similarity: cosine\` automaticamente (veja o mapping acima) — ou seja, ele já está indexado em HNSW e aceita a query \`knn\` nativa, que no 7.x não existia."

# ---------------- PARTE 14 ----------------
sec "PARTE 14 – Mapping vetorial, ingestão e busca semântica"

sub "14.1 – Índice com mapping vetorial"
req DELETE "indice_conhecimento" "" "Remove índice de tentativa anterior"
req PUT "indice_conhecimento" '{ "mappings": { "properties": {
  "titulo": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
  "conteudo": { "type": "text" },
  "categoria": { "type": "keyword" },
  "data_publicacao": { "type": "date", "format": "strict_date_optional_time||epoch_millis" },
  "embedding": { "type": "dense_vector", "dims": 10 }
} } }' "Cria indice_conhecimento (embedding dims 10)"

sub "14.2 – Ingestão manual com embedding"
req POST "indice_conhecimento/_doc/1" '{ "titulo": "Capital do Brasil", "conteudo": "Brasília é a capital federal do Brasil e sede do governo.", "categoria": "geografia", "data_publicacao": "2026-03-10T10:00:00", "embedding": [0.12, -0.44, 0.81, 0.33, -0.91, 0.17, 0.25, -0.08, 0.66, 0.14] }' "Documento 1 (geografia)"
req POST "indice_conhecimento/_doc/2" '{ "titulo": "Maior cidade brasileira", "conteudo": "São Paulo é a cidade mais populosa do Brasil e um importante centro econômico.", "categoria": "geografia", "data_publicacao": "2026-03-10T10:05:00", "embedding": [0.05, -0.11, 0.77, 0.41, -0.88, 0.09, 0.31, -0.02, 0.60, 0.21] }' "Documento 2 (geografia)"
req POST "indice_conhecimento/_doc/3" '{ "titulo": "Elastic e busca vetorial", "conteudo": "O Elasticsearch pode combinar busca lexical com busca vetorial para melhorar a relevância.", "categoria": "tecnologia", "data_publicacao": "2026-03-10T10:10:00", "embedding": [0.72, -0.13, 0.14, 0.55, -0.20, 0.61, 0.48, -0.09, 0.11, 0.39] }' "Documento 3 (tecnologia)"

sub "14.3 – Ingestão em lote (bulk)"
bulk_req "$SP/bulk_conhecimento.ndjson" "Bulk: 20 documentos (ids 4 a 23)"
req POST "indice_conhecimento/_refresh" "" "Refresh"

sub "14.4 – Consulta vetorial (script_score / cosine)"
req POST "indice_conhecimento/_search" '{ "query": { "script_score": { "query": { "match_all": {} }, "script": { "source": "cosineSimilarity(params.query_vector, '"'"'embedding'"'"') + 1.0", "params": { "query_vector": [0.11, -0.40, 0.80, 0.30, -0.89, 0.15, 0.20, -0.05, 0.62, 0.10] } } } }, "_source": ["titulo", "categoria"], "size": 3 }' "Top-3 por similaridade de cosseno"

sub "14.5 – Busca vetorial com filtro"
req POST "indice_conhecimento/_search" '{ "query": { "script_score": { "query": { "bool": { "filter": [ { "term": { "categoria": "tecnologia" } } ] } }, "script": { "source": "cosineSimilarity(params.query_vector, '"'"'embedding'"'"') + 1.0", "params": { "query_vector": [0.68, -0.08, 0.20, 0.50, -0.15, 0.55, 0.42, -0.06, 0.17, 0.40] } } } }, "_source": ["titulo", "categoria"], "size": 3 }' "Similaridade restrita a categoria=tecnologia"

sub "14.6 – Busca híbrida (BM25 + vetor)"
req POST "indice_conhecimento/_search" '{ "query": { "script_score": { "query": { "match": { "conteudo": "busca vetorial no elasticsearch" } }, "script": { "source": "cosineSimilarity(params.query_vector, '"'"'embedding'"'"') + 1.0", "params": { "query_vector": [0.70, -0.12, 0.16, 0.53, -0.19, 0.60, 0.46, -0.08, 0.13, 0.38] } } } }, "_source": ["titulo", "categoria", "conteudo"], "size": 3 }' "Híbrida: match filtra, cosseno reordena"

sub "EXTRA – Sintaxe knn nativa do ES 8.x (não existe no 7.x)"
req POST "indice_conhecimento/_search" '{ "knn": { "field": "embedding", "query_vector": [0.11, -0.40, 0.80, 0.30, -0.89, 0.15, 0.20, -0.05, 0.62, 0.10], "k": 3, "num_candidates": 100 }, "_source": ["titulo", "categoria"] }' "Mesma busca da 14.4, via knn/HNSW"
nota "Mesmo resultado da 14.4, mas o \`script_score\` faz varredura exaustiva (brute-force) em todos os documentos, enquanto o \`knn\` usa o grafo HNSW. Em milhões de documentos a diferença de custo é enorme."

sub "14.9 – Consulta de verificação"
req GET "indice_conhecimento/_search" '{ "query": { "match_all": {} }, "_source": ["titulo", "categoria"], "size": 5 }' "match_all (amostra de 5)"
req GET "indice_conhecimento/_count" "" "Total de documentos"
req GET "indice_conhecimento/_mapping" "" "Mapping criado"
