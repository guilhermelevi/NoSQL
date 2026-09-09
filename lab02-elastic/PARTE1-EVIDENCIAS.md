# Lab 2 – Elastic – Parte 1 – Evidências de execução

Executado em 08/09/2026 20:01 · Elasticsearch 8.15.3 · macOS/OrbStack

## PARTE 6 – Templates de índice

### Template genérico (meu_template)

```
PUT _template/meu_template
{
  "index_patterns": ["meu_indice-*"],
  "settings": { "index.lifecycle.name": "minha_politica", "index.lifecycle.rollover_alias": "meu_indice" },
  "mappings": { "properties": {
    "nome": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
    "idade": { "type": "integer" },
    "cidade": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } }
  } }
}
```

**Resposta:**

```json
{
    "acknowledged": true
}
```

### Template de transações (transacoes_template)

```
PUT _template/transacoes_template
{
  "index_patterns": ["transacoes-*"],
  "settings": { "index.lifecycle.name": "politica_transacoes", "index.lifecycle.rollover_alias": "transacoes" },
  "mappings": { "properties": {
    "usuario": { "type": "text", "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },
    "valor": { "type": "double" },
    "tipo": { "type": "keyword" },
    "data": { "type": "date", "format": "strict_date_optional_time||epoch_millis" }
  } }
}
```

**Resposta:**

```json
{
    "acknowledged": true
}
```

## PARTE 7 – Índices com alias

### Índice meu_indice-000001 + alias

```
PUT meu_indice-000001
{ "aliases": { "meu_indice": { "is_write_index": true } } }
```

**Resposta:**

```json
{
    "acknowledged": true,
    "shards_acknowledged": true,
    "index": "meu_indice-000001"
}
```

### Índice transacoes-000001 + alias

```
PUT transacoes-000001
{ "aliases": { "transacoes": { "is_write_index": true } } }
```

**Resposta:**

```json
{
    "acknowledged": true,
    "shards_acknowledged": true,
    "index": "transacoes-000001"
}
```

## PARTE 8 – Inserção de documentos

### Insere pessoa 1

```
POST meu_indice-000001/_doc/1?refresh=true
{ "nome": "João Silva", "idade": 30, "cidade": "Brasília" }
```

**Resposta:**

```json
{
    "_index": "meu_indice-000001",
    "_id": "1",
    "_version": 1,
    "result": "created",
    "forced_refresh": true,
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 0,
    "_primary_term": 1
}
```

### Insere pessoa 2

```
POST meu_indice-000001/_doc/2?refresh=true
{ "nome": "Maria Souza", "idade": 25, "cidade": "São Paulo" }
```

**Resposta:**

```json
{
    "_index": "meu_indice-000001",
    "_id": "2",
    "_version": 1,
    "result": "created",
    "forced_refresh": true,
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 1,
    "_primary_term": 1
}
```

### Insere transação 1

```
POST transacoes-000001/_doc/1?refresh=true
{ "usuario": "João Silva", "valor": 150.75, "tipo": "compra", "data": "2025-03-19T12:00:00" }
```

**Resposta:**

```json
{
    "_index": "transacoes-000001",
    "_id": "1",
    "_version": 1,
    "result": "created",
    "forced_refresh": true,
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 0,
    "_primary_term": 1
}
```

### Insere transação 2

```
POST transacoes-000001/_doc/2?refresh=true
{ "usuario": "Maria Souza", "valor": 200.50, "tipo": "venda", "data": "2025-03-18T10:30:00" }
```

**Resposta:**

```json
{
    "_index": "transacoes-000001",
    "_id": "2",
    "_version": 1,
    "result": "created",
    "forced_refresh": true,
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 1,
    "_primary_term": 1
}
```

## PARTE 9 – Consultas

### Busca por ID (via alias)

```
GET meu_indice/_doc/1
```

**Resposta:**

```json
{
    "_index": "meu_indice-000001",
    "_id": "1",
    "_version": 1,
    "_seq_no": 0,
    "_primary_term": 1,
    "found": true,
    "_source": {
        "nome": "Jo\u00e3o Silva",
        "idade": 30,
        "cidade": "Bras\u00edlia"
    }
}
```

### Busca por ID em transações

```
GET transacoes/_doc/2
```

**Resposta:**

```json
{
    "_index": "transacoes-000001",
    "_id": "2",
    "_version": 1,
    "_seq_no": 1,
    "_primary_term": 1,
    "found": true,
    "_source": {
        "usuario": "Maria Souza",
        "valor": 200.5,
        "tipo": "venda",
        "data": "2025-03-18T10:30:00"
    }
}
```

### Full-text (match)

```
GET meu_indice-000001/_search
{ "query": { "match": { "nome": "João" } } }
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
        "max_score": 0.6931471,
        "hits": [
            {
                "_index": "meu_indice-000001",
                "_id": "1",
                "_score": 0.6931471,
                "_source": {
                    "nome": "Jo\u00e3o Silva",
                    "idade": 30,
                    "cidade": "Bras\u00edlia"
                }
            }
        ]
    }
}
```

### Intervalo numérico (range)

```
GET transacoes/_search
{ "query": { "range": { "valor": { "gte": 100 } } } }
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
            "value": 2,
            "relation": "eq"
        },
        "max_score": 1.0,
        "hits": [
            {
                "_index": "transacoes-000001",
                "_id": "1",
                "_score": 1.0,
                "_source": {
                    "usuario": "Jo\u00e3o Silva",
                    "valor": 150.75,
                    "tipo": "compra",
                    "data": "2025-03-19T12:00:00"
                }
            },
            {
                "_index": "transacoes-000001",
                "_id": "2",
                "_score": 1.0,
                "_source": {
                    "usuario": "Maria Souza",
                    "valor": 200.5,
                    "tipo": "venda",
                    "data": "2025-03-18T10:30:00"
                }
            }
        ]
    }
}
```

### Composta (bool: must + filter)

```
GET meu_indice/_search
{ "query": { "bool": { "must": [ { "match": { "cidade": "Brasília" } } ], "filter": [ { "range": { "idade": { "gte": 30 } } } ] } } }
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
        "max_score": 0.8025915,
        "hits": [
            {
                "_index": "meu_indice-000001",
                "_id": "1",
                "_score": 0.8025915,
                "_source": {
                    "nome": "Jo\u00e3o Silva",
                    "idade": 30,
                    "cidade": "Bras\u00edlia"
                }
            }
        ]
    }
}
```

## PARTE 10 – Atualização

### Atualiza idade 30 -> 31

```
POST meu_indice/_update/1?refresh=true
{ "doc": { "idade": 31 } }
```

**Resposta:**

```json
{
    "_index": "meu_indice-000001",
    "_id": "1",
    "_version": 2,
    "result": "updated",
    "forced_refresh": true,
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 2,
    "_primary_term": 1
}
```

### Atualiza valor 150.75 -> 160.00

```
POST transacoes/_update/1?refresh=true
{ "doc": { "valor": 160.00 } }
```

**Resposta:**

```json
{
    "_index": "transacoes-000001",
    "_id": "1",
    "_version": 2,
    "result": "updated",
    "forced_refresh": true,
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 2,
    "_primary_term": 1
}
```

### Confirma atualização (idade = 31)

```
GET meu_indice/_doc/1
```

**Resposta:**

```json
{
    "_index": "meu_indice-000001",
    "_id": "1",
    "_version": 2,
    "_seq_no": 2,
    "_primary_term": 1,
    "found": true,
    "_source": {
        "nome": "Jo\u00e3o Silva",
        "idade": 31,
        "cidade": "Bras\u00edlia"
    }
}
```

### Confirma atualização (valor = 160.0)

```
GET transacoes/_doc/1
```

**Resposta:**

```json
{
    "_index": "transacoes-000001",
    "_id": "1",
    "_version": 2,
    "_seq_no": 2,
    "_primary_term": 1,
    "found": true,
    "_source": {
        "usuario": "Jo\u00e3o Silva",
        "valor": 160.0,
        "tipo": "compra",
        "data": "2025-03-19T12:00:00"
    }
}
```

## PARTE 11 – Exclusão

### Exclui pessoa 1

```
DELETE meu_indice/_doc/1
```

**Resposta:**

```json
```

### Exclui pessoa 2

```
DELETE meu_indice/_doc/2
```

**Resposta:**

```json
```

### Exclui transação 1

```
DELETE transacoes/_doc/1
```

**Resposta:**

```json
```

### Exclui transação 2

```
DELETE transacoes/_doc/2
```

**Resposta:**

```json
```

### Exclui índice meu_indice-000001

```
DELETE meu_indice-000001
```

**Resposta:**

```json
```

### Exclui índice transacoes-000001

```
DELETE transacoes-000001
```

**Resposta:**

```json
```

### Exclui template meu_template

```
DELETE _template/meu_template
```

**Resposta:**

```json
```

### Exclui template transacoes_template

```
DELETE _template/transacoes_template
```

**Resposta:**

```json
```

## PARTE 11 – Exclusão

### Exclui pessoa 1

```
DELETE meu_indice/_doc/1
```

**Resposta:**

```json
{
    "_index": "meu_indice-000001",
    "_id": "1",
    "_version": 3,
    "result": "deleted",
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 3,
    "_primary_term": 1
}
```

### Exclui pessoa 2

```
DELETE meu_indice/_doc/2
```

**Resposta:**

```json
{
    "_index": "meu_indice-000001",
    "_id": "2",
    "_version": 2,
    "result": "deleted",
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 4,
    "_primary_term": 1
}
```

### Exclui transação 1

```
DELETE transacoes/_doc/1
```

**Resposta:**

```json
{
    "_index": "transacoes-000001",
    "_id": "1",
    "_version": 3,
    "result": "deleted",
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 3,
    "_primary_term": 1
}
```

### Exclui transação 2

```
DELETE transacoes/_doc/2
```

**Resposta:**

```json
{
    "_index": "transacoes-000001",
    "_id": "2",
    "_version": 2,
    "result": "deleted",
    "_shards": {
        "total": 2,
        "successful": 1,
        "failed": 0
    },
    "_seq_no": 4,
    "_primary_term": 1
}
```

### Exclui índice meu_indice-000001

```
DELETE meu_indice-000001
```

**Resposta:**

```json
{
    "acknowledged": true
}
```

### Exclui índice transacoes-000001

```
DELETE transacoes-000001
```

**Resposta:**

```json
{
    "acknowledged": true
}
```

### Exclui template meu_template

```
DELETE _template/meu_template
```

**Resposta:**

```json
{
    "acknowledged": true
}
```

### Exclui template transacoes_template

```
DELETE _template/transacoes_template
```

**Resposta:**

```json
{
    "acknowledged": true
}
```
