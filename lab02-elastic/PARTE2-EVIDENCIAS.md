# Lab 2 – Elastic – Parte 2 – Evidências de execução

Executado em 08/09/2026 20:20 · Elasticsearch 8.15.3 · macOS/OrbStack (1 nó)

## PARTE 12 – Arquitetura e engine de busca

### 12.1 – Cluster, node, index, shard e replica

### Saúde do cluster

```
GET _cluster/health
```

**Resposta:**

```json
{
    "cluster_name": "docker-cluster",
    "status": "yellow",
    "timed_out": false,
    "number_of_nodes": 1,
    "number_of_data_nodes": 1,
    "active_primary_shards": 33,
    "active_shards": 33,
    "relocating_shards": 0,
    "initializing_shards": 0,
    "unassigned_shards": 3,
    "delayed_unassigned_shards": 0,
    "number_of_pending_tasks": 0,
    "number_of_in_flight_fetch": 0,
    "task_max_waiting_in_queue_millis": 0,
    "active_shards_percent_as_number": 91.66666666666666
}
```

### Nós do cluster

```
GET _cat/nodes?v
```

**Resposta:**

```
ip            heap.percent ram.percent cpu load_1m load_5m load_15m node.role   master name
192.168.107.2           37          45   1    0.22    0.19     0.22 cdfhilmrstw *      96ef8f7b41d1
```

### Shards dos índices do lab

```
GET _cat/shards/meu_indice-000001,transacoes-000001?v
```

**Resposta:**

```
index             shard prirep state      docs  store dataset ip            node
transacoes-000001 0     p      STARTED       2   18kb    18kb 192.168.107.2 96ef8f7b41d1
transacoes-000001 0     r      UNASSIGNED                                   
meu_indice-000001 0     p      STARTED       2 17.7kb  17.7kb 192.168.107.2 96ef8f7b41d1
meu_indice-000001 0     r      UNASSIGNED                                   
```

> Status **yellow**: com 1 nó só, as replicas ficam `unassigned` (não há segundo nó para hospedá-las). Em produção, com 2+ nós, elas seriam alocadas e o status viraria green.

### 12.3 – Analyzer: tokenização e normalização

### Analyzer standard

```
POST _analyze
{ "analyzer": "standard", "text": "JOÃO, da Silva; em BRASÍLIA!" }
```

**Resposta:**

```json
{
    "tokens": [
        {
            "token": "jo\u00e3o",
            "start_offset": 0,
            "end_offset": 4,
            "type": "<ALPHANUM>",
            "position": 0
        },
        {
            "token": "da",
            "start_offset": 6,
            "end_offset": 8,
            "type": "<ALPHANUM>",
            "position": 1
        },
        {
            "token": "silva",
            "start_offset": 9,
            "end_offset": 14,
            "type": "<ALPHANUM>",
            "position": 2
        },
        {
            "token": "em",
            "start_offset": 16,
            "end_offset": 18,
            "type": "<ALPHANUM>",
            "position": 3
        },
        {
            "token": "bras\u00edlia",
            "start_offset": 19,
            "end_offset": 27,
            "type": "<ALPHANUM>",
            "position": 4
        }
    ]
}
```

> Repare: vira minúsculo e a pontuação some. É por isso que `match: "joao"` acha "João" — os dois passam pelo mesmo analyzer na indexação e na busca.

### 12.4 – match vs term

### match (analisado)

```
GET meu_indice/_search
{ "query": { "match": { "nome": "João" } } }
```

**Resposta:**

```json
{
    "took": 2,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 1,
            "relation": "eq"
        },
        "max_score": 0.4700036,
        "hits": [
            {
                "_index": "meu_indice-000001",
                "_id": "1",
                "_score": 0.4700036,
                "_source": {
                    "nome": "Jo\u00e3o Silva",
                    "idade": 31,
                    "cidade": "Bras\u00edlia"
                }
            }
        ]
    }
}
```

### term (exato, sub-campo keyword)

```
GET meu_indice/_search
{ "query": { "term": { "cidade.keyword": "Brasília" } } }
```

**Resposta:**

```json
{
    "took": 1,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 1,
            "relation": "eq"
        },
        "max_score": 0.4700036,
        "hits": [
            {
                "_index": "meu_indice-000001",
                "_id": "1",
                "_score": 0.4700036,
                "_source": {
                    "nome": "Jo\u00e3o Silva",
                    "idade": 31,
                    "cidade": "Bras\u00edlia"
                }
            }
        ]
    }
}
```

### 12.5 – must vs filter

### bool: must + filter

```
GET meu_indice/_search
{ "query": { "bool": { "must": [ { "match": { "nome": "João" } } ], "filter": [ { "term": { "cidade.keyword": "Brasília" } }, { "range": { "idade": { "gte": 30 } } } ] } } }
```

**Resposta:**

```json
{
    "took": 1,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 1,
            "relation": "eq"
        },
        "max_score": 0.4700036,
        "hits": [
            {
                "_index": "meu_indice-000001",
                "_id": "1",
                "_score": 0.4700036,
                "_source": {
                    "nome": "Jo\u00e3o Silva",
                    "idade": 31,
                    "cidade": "Bras\u00edlia"
                }
            }
        ]
    }
}
```

### 12.6 – Score e BM25

### match com explain (BM25)

```
GET meu_indice/_search
{ "query": { "match": { "nome": "João" } }, "explain": true }
```

**Resposta:**

```json
{
    "took": 5,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 1,
            "relation": "eq"
        },
        "max_score": 0.4700036,
        "hits": [
            {
                "_shard": "[meu_indice-000001][0]",
                "_node": "k5ED-O4nRqm6EAfdG9V6bA",
                "_index": "meu_indice-000001",
                "_id": "1",
                "_score": 0.4700036,
                "_source": {
                    "nome": "Jo\u00e3o Silva",
                    "idade": 31,
                    "cidade": "Bras\u00edlia"
                },
                "_explanation": {
                    "value": 0.4700036,
                    "description": "weight(nome:jo\u00e3o in 0) [PerFieldSimilarity], result of:",
                    "details": [
                        {
                            "value": 0.4700036,
                            "description": "score(freq=1.0), computed as boost * idf * tf from:",
                            "details": [
                                {
                                    "value": 2.2,
                                    "description": "boost",
                                    "details": []
                                },
                                {
                                    "value": 0.47000363,
                                    "description": "idf, computed as log(1 + (N - n + 0.5) / (n + 0.5)) from:",
                                    "details": [
                                        {
                                            "value": 2,
                                            "description": "n, number of documents containing term",
                                            "details": []
                                        },
                                        {
                                            "value": 3,
                                            "description": "N, total number of documents with field",
                                            "details": []
                                        }
                                    ]
                                },
                                {
                                    "value": 0.45454544,
                                    "description": "tf, computed as freq / (freq + k1 * (1 - b + b * dl / avgdl)) from:",
                                    "details": [
                                        {
                                            "value": 1.0,
                                            "description": "freq, occurrences of term within document",
                                            "details": []
                                        },
                                        {
                                            "value": 1.2,
                                            "description": "k1, term saturation parameter",
                                            "details": []
                                        },
                                        {
                                            "value": 0.75,
                                            "description": "b, length normalization parameter",
                                            "details": []
                                        },
                                        {
                                            "value": 2.0,
                                            "description": "dl, length of field",
                                            "details": []
                                        },
                                        {
                                            "value": 2.0,
                                            "description": "avgdl, average length of field",
                                            "details": []
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }
}
```

### 12.7 – Near real-time e refresh

### Settings do índice

```
GET meu_indice/_settings
```

**Resposta:**

```json
{
    "meu_indice-000001": {
        "settings": {
            "index": {
                "lifecycle": {
                    "name": "minha_politica",
                    "rollover_alias": "meu_indice"
                },
                "routing": {
                    "allocation": {
                        "include": {
                            "_tier_preference": "data_content"
                        }
                    }
                },
                "number_of_shards": "1",
                "provided_name": "meu_indice-000001",
                "creation_date": "1788909485651",
                "number_of_replicas": "1",
                "uuid": "u-9LWYp2QomWHlV_YyY4jw",
                "version": {
                    "created": "8512000"
                }
            }
        }
    }
}
```

### Refresh forçado

```
POST meu_indice/_refresh
```

**Resposta:**

```json
{
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    }
}
```

### 12.8 – Bulk API (pessoas)

### Bulk: 20 pessoas em meu_indice

```
POST _bulk  (arquivo NDJSON: bulk_pessoas.ndjson, 20 documentos)
```

**Resposta (resumida):**

```json
{
  "took": 205,
  "errors": false,
  "total_itens": 20,
  "resultados": [
    "created"
  ],
  "status_codes": [
    201
  ],
  "primeiro_item": {
    "index": {
      "_index": "meu_indice-000001",
      "_id": "t1pSg6AB_mLDPrQsTWXv",
      "_version": 1,
      "result": "created",
      "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
      },
      "_seq_no": 3,
      "_primary_term": 1,
      "status": 201
    }
  }
}
```

### Refresh após bulk

```
POST meu_indice/_refresh
```

**Resposta:**

```json
{
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    }
}
```

### Contagem após bulk

```
GET _cat/indices/meu_indice-000001?v
```

**Resposta:**

```
health status index             uuid                   pri rep docs.count docs.deleted store.size pri.store.size dataset.size
yellow open   meu_indice-000001 u-9LWYp2QomWHlV_YyY4jw   1   1         22            1     26.5kb         26.5kb       26.5kb
```

### 12.9 – Aggregations

### Bulk: 20 transações

```
POST _bulk  (arquivo NDJSON: bulk_transacoes.ndjson, 20 documentos)
```

**Resposta (resumida):**

```json
{
  "took": 0,
  "errors": false,
  "total_itens": 20,
  "resultados": [
    "created"
  ],
  "status_codes": [
    201
  ],
  "primeiro_item": {
    "index": {
      "_index": "transacoes-000001",
      "_id": "y1pSg6AB_mLDPrQsTmU1",
      "_version": 1,
      "result": "created",
      "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
      },
      "_seq_no": 3,
      "_primary_term": 1,
      "status": 201
    }
  }
}
```

### Refresh após bulk

```
POST transacoes/_refresh
```

**Resposta:**

```json
{
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    }
}
```

### Agregação: contagem por tipo

```
GET transacoes/_search
{ "size": 0, "aggs": { "total_por_tipo": { "terms": { "field": "tipo" } } } }
```

**Resposta:**

```json
{
    "took": 2,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 22,
            "relation": "eq"
        },
        "max_score": null,
        "hits": []
    },
    "aggregations": {
        "total_por_tipo": {
            "doc_count_error_upper_bound": 0,
            "sum_other_doc_count": 0,
            "buckets": [
                {
                    "key": "compra",
                    "doc_count": 12
                },
                {
                    "key": "venda",
                    "doc_count": 10
                }
            ]
        }
    }
}
```

### Agregação: valor médio

```
GET transacoes/_search
{ "size": 0, "aggs": { "valor_medio": { "avg": { "field": "valor" } } } }
```

**Resposta:**

```json
{
    "took": 9,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 22,
            "relation": "eq"
        },
        "max_score": null,
        "hits": []
    },
    "aggregations": {
        "valor_medio": {
            "value": 302.26590909090913
        }
    }
}
```

## PARTE 13 – Busca vetorial (conceitos)

> As seções 13.1, 13.5, 13.7 e 13.8 são conceituais (sem comandos). 13.3, 13.4 e 13.6 são marcadas como ilustrativas no roteiro porque os vetores estão truncados com `...`. Executamos aqui apenas 13.2, que é executável.

### 13.2 – Campo dense_vector (dims 384)

### Cria índice com dense_vector de 384 dimensões

```
PUT documentos_vetoriais
{ "mappings": { "properties": { "texto": { "type": "text" }, "embedding": { "type": "dense_vector", "dims": 384 } } } }
```

**Resposta:**

```json
{
    "acknowledged": true,
    "shards_acknowledged": true,
    "index": "documentos_vetoriais"
}
```

### Mapping resultante

```
GET documentos_vetoriais/_mapping
```

**Resposta:**

```json
{
    "documentos_vetoriais": {
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": true,
                    "similarity": "cosine",
                    "index_options": {
                        "type": "int8_hnsw",
                        "m": 16,
                        "ef_construction": 100
                    }
                },
                "texto": {
                    "type": "text"
                }
            }
        }
    }
}
```

> **Diferença de versão importante:** o roteiro foi escrito para ES 7.x, onde `dense_vector` só aceitava `dims`. Estamos no **ES 8.15**, então o campo ganhou `index: true` e `similarity: cosine` automaticamente (veja o mapping acima) — ou seja, ele já está indexado em HNSW e aceita a query `knn` nativa, que no 7.x não existia.

## PARTE 14 – Mapping vetorial, ingestão e busca semântica

### 14.1 – Índice com mapping vetorial

### Remove índice de tentativa anterior

```
DELETE indice_conhecimento
```

**Resposta:**

```json
{
    "error": {
        "root_cause": [
            {
                "type": "index_not_found_exception",
                "reason": "no such index [indice_conhecimento]",
                "resource.type": "index_or_alias",
                "resource.id": "indice_conhecimento",
                "index_uuid": "_na_",
                "index": "indice_conhecimento"
            }
        ],
        "type": "index_not_found_exception",
        "reason": "no such index [indice_conhecimento]",
        "resource.type": "index_or_alias",
        "resource.id": "indice_conhecimento",
        "index_uuid": "_na_",
        "index": "indice_conhecimento"
    },
    "status": 404
}
```

### Cria indice_conhecimento (embedding dims 10)

```
PUT indice_conhecimento
{ "mappings": { "properties": {
  "titulo": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
  "conteudo": { "type": "text" },
  "categoria": { "type": "keyword" },
  "data_publicacao": { "type": "date", "format": "strict_date_optional_time||epoch_millis" },
  "embedding": { "type": "dense_vector", "dims": 10 }
} } }
```

**Resposta:**

```json
{
    "acknowledged": true,
    "shards_acknowledged": true,
    "index": "indice_conhecimento"
}
```

### 14.2 – Ingestão manual com embedding

### Documento 1 (geografia)

```
POST indice_conhecimento/_doc/1
{ "titulo": "Capital do Brasil", "conteudo": "Brasília é a capital federal do Brasil e sede do governo.", "categoria": "geografia", "data_publicacao": "2026-03-10T10:00:00", "embedding": [0.12, -0.44, 0.81, 0.33, -0.91, 0.17, 0.25, -0.08, 0.66, 0.14] }
```

**Resposta:**

```json
{
    "_index": "indice_conhecimento",
    "_id": "1",
    "_version": 1,
    "result": "created",
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 0,
    "_primary_term": 1
}
```

### Documento 2 (geografia)

```
POST indice_conhecimento/_doc/2
{ "titulo": "Maior cidade brasileira", "conteudo": "São Paulo é a cidade mais populosa do Brasil e um importante centro econômico.", "categoria": "geografia", "data_publicacao": "2026-03-10T10:05:00", "embedding": [0.05, -0.11, 0.77, 0.41, -0.88, 0.09, 0.31, -0.02, 0.60, 0.21] }
```

**Resposta:**

```json
{
    "_index": "indice_conhecimento",
    "_id": "2",
    "_version": 1,
    "result": "created",
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 1,
    "_primary_term": 1
}
```

### Documento 3 (tecnologia)

```
POST indice_conhecimento/_doc/3
{ "titulo": "Elastic e busca vetorial", "conteudo": "O Elasticsearch pode combinar busca lexical com busca vetorial para melhorar a relevância.", "categoria": "tecnologia", "data_publicacao": "2026-03-10T10:10:00", "embedding": [0.72, -0.13, 0.14, 0.55, -0.20, 0.61, 0.48, -0.09, 0.11, 0.39] }
```

**Resposta:**

```json
{
    "_index": "indice_conhecimento",
    "_id": "3",
    "_version": 1,
    "result": "created",
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 2,
    "_primary_term": 1
}
```

### 14.3 – Ingestão em lote (bulk)

### Bulk: 20 documentos (ids 4 a 23)

```
POST _bulk  (arquivo NDJSON: bulk_conhecimento.ndjson, 20 documentos)
```

**Resposta (resumida):**

```json
{
  "took": 201,
  "errors": false,
  "total_itens": 20,
  "resultados": [
    "created"
  ],
  "status_codes": [
    201
  ],
  "primeiro_item": {
    "index": {
      "_index": "indice_conhecimento",
      "_id": "4",
      "_version": 1,
      "result": "created",
      "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
      },
      "_seq_no": 3,
      "_primary_term": 1,
      "status": 201
    }
  }
}
```

### Refresh

```
POST indice_conhecimento/_refresh
```

**Resposta:**

```json
{
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    }
}
```

### 14.4 – Consulta vetorial (script_score / cosine)

### Top-3 por similaridade de cosseno

```
POST indice_conhecimento/_search
{ "query": { "script_score": { "query": { "match_all": {} }, "script": { "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0", "params": { "query_vector": [0.11, -0.40, 0.80, 0.30, -0.89, 0.15, 0.20, -0.05, 0.62, 0.10] } } } }, "_source": ["titulo", "categoria"], "size": 3 }
```

**Resposta:**

```json
{
    "took": 12,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 23,
            "relation": "eq"
        },
        "max_score": 1.9989467,
        "hits": [
            {
                "_index": "indice_conhecimento",
                "_id": "16",
                "_score": 1.9989467,
                "_source": {
                    "titulo": "Curitiba",
                    "categoria": "geografia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "12",
                "_score": 1.9989382,
                "_source": {
                    "titulo": "Cerrado brasileiro",
                    "categoria": "geografia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "1",
                "_score": 1.9987481,
                "_source": {
                    "titulo": "Capital do Brasil",
                    "categoria": "geografia"
                }
            }
        ]
    }
}
```

### 14.5 – Busca vetorial com filtro

### Similaridade restrita a categoria=tecnologia

```
POST indice_conhecimento/_search
{ "query": { "script_score": { "query": { "bool": { "filter": [ { "term": { "categoria": "tecnologia" } } ] } }, "script": { "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0", "params": { "query_vector": [0.68, -0.08, 0.20, 0.50, -0.15, 0.55, 0.42, -0.06, 0.17, 0.40] } } } }, "_source": ["titulo", "categoria"], "size": 3 }
```

**Resposta:**

```json
{
    "took": 1,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 12,
            "relation": "eq"
        },
        "max_score": 1.999091,
        "hits": [
            {
                "_index": "indice_conhecimento",
                "_id": "5",
                "_score": 1.999091,
                "_source": {
                    "titulo": "Busca h\u00edbrida",
                    "categoria": "tecnologia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "19",
                "_score": 1.9989983,
                "_source": {
                    "titulo": "Microsservi\u00e7os",
                    "categoria": "tecnologia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "11",
                "_score": 1.998364,
                "_source": {
                    "titulo": "NoSQL e bancos de dados distribu\u00eddos",
                    "categoria": "tecnologia"
                }
            }
        ]
    }
}
```

### 14.6 – Busca híbrida (BM25 + vetor)

### Híbrida: match filtra, cosseno reordena

```
POST indice_conhecimento/_search
{ "query": { "script_score": { "query": { "match": { "conteudo": "busca vetorial no elasticsearch" } }, "script": { "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0", "params": { "query_vector": [0.70, -0.12, 0.16, 0.53, -0.19, 0.60, 0.46, -0.08, 0.13, 0.38] } } } }, "_source": ["titulo", "categoria", "conteudo"], "size": 3 }
```

**Resposta:**

```json
{
    "took": 2,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 7,
            "relation": "eq"
        },
        "max_score": 1.9995801,
        "hits": [
            {
                "_index": "indice_conhecimento",
                "_id": "3",
                "_score": 1.9995801,
                "_source": {
                    "titulo": "Elastic e busca vetorial",
                    "conteudo": "O Elasticsearch pode combinar busca lexical com busca vetorial para melhorar a relev\u00e2ncia.",
                    "categoria": "tecnologia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "21",
                "_score": 1.9989514,
                "_source": {
                    "titulo": "Elasticsearch avan\u00e7ado",
                    "conteudo": "O Elasticsearch oferece recursos avan\u00e7ados como agrega\u00e7\u00f5es, ILM, snapshots e busca vetorial.",
                    "categoria": "tecnologia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "23",
                "_score": 1.9988296,
                "_source": {
                    "titulo": "RAG com Elasticsearch",
                    "conteudo": "RAG usa o Elasticsearch como base de conhecimento para recuperar contexto antes de acionar um LLM.",
                    "categoria": "tecnologia"
                }
            }
        ]
    }
}
```

### EXTRA – Sintaxe knn nativa do ES 8.x (não existe no 7.x)

### Mesma busca da 14.4, via knn/HNSW

```
POST indice_conhecimento/_search
{ "knn": { "field": "embedding", "query_vector": [0.11, -0.40, 0.80, 0.30, -0.89, 0.15, 0.20, -0.05, 0.62, 0.10], "k": 3, "num_candidates": 100 }, "_source": ["titulo", "categoria"] }
```

**Resposta:**

```json
{
    "took": 17,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 3,
            "relation": "eq"
        },
        "max_score": 0.9993628,
        "hits": [
            {
                "_index": "indice_conhecimento",
                "_id": "16",
                "_score": 0.9993628,
                "_source": {
                    "titulo": "Curitiba",
                    "categoria": "geografia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "12",
                "_score": 0.99935234,
                "_source": {
                    "titulo": "Cerrado brasileiro",
                    "categoria": "geografia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "1",
                "_score": 0.99923646,
                "_source": {
                    "titulo": "Capital do Brasil",
                    "categoria": "geografia"
                }
            }
        ]
    }
}
```

> Mesmo resultado da 14.4, mas o `script_score` faz varredura exaustiva (brute-force) em todos os documentos, enquanto o `knn` usa o grafo HNSW. Em milhões de documentos a diferença de custo é enorme.

### 14.9 – Consulta de verificação

### match_all (amostra de 5)

```
GET indice_conhecimento/_search
{ "query": { "match_all": {} }, "_source": ["titulo", "categoria"], "size": 5 }
```

**Resposta:**

```json
{
    "took": 0,
    "timed_out": false,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    },
    "hits": {
        "total": {
            "value": 23,
            "relation": "eq"
        },
        "max_score": 1.0,
        "hits": [
            {
                "_index": "indice_conhecimento",
                "_id": "1",
                "_score": 1.0,
                "_source": {
                    "titulo": "Capital do Brasil",
                    "categoria": "geografia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "2",
                "_score": 1.0,
                "_source": {
                    "titulo": "Maior cidade brasileira",
                    "categoria": "geografia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "3",
                "_score": 1.0,
                "_source": {
                    "titulo": "Elastic e busca vetorial",
                    "categoria": "tecnologia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "4",
                "_score": 1.0,
                "_source": {
                    "titulo": "Banco vetorial",
                    "categoria": "tecnologia"
                }
            },
            {
                "_index": "indice_conhecimento",
                "_id": "5",
                "_score": 1.0,
                "_source": {
                    "titulo": "Busca h\u00edbrida",
                    "categoria": "tecnologia"
                }
            }
        ]
    }
}
```

### Total de documentos

```
GET indice_conhecimento/_count
```

**Resposta:**

```json
{
    "count": 23,
    "_shards": {
        "total": 1,
        "successful": 1,
        "skipped": 0,
        "failed": 0
    }
}
```

### Mapping criado

```
GET indice_conhecimento/_mapping
```

**Resposta:**

```json
{
    "indice_conhecimento": {
        "mappings": {
            "properties": {
                "categoria": {
                    "type": "keyword"
                },
                "conteudo": {
                    "type": "text"
                },
                "data_publicacao": {
                    "type": "date"
                },
                "embedding": {
                    "type": "dense_vector",
                    "dims": 10,
                    "index": true,
                    "similarity": "cosine",
                    "index_options": {
                        "type": "int8_hnsw",
                        "m": 16,
                        "ef_construction": 100
                    }
                },
                "titulo": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "ignore_above": 256
                        }
                    }
                }
            }
        }
    }
}
```
