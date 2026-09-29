# Lab 4 — Integração dos três bancos

Os três laboratórios anteriores trataram cada banco separado. Este junta os três num cenário só, um catálogo de loja, com cada um no papel para o qual foi feito.

```
MongoDB          fonte da verdade      grava o produto, com escrita confirmada
   ↓  sincroniza
Elasticsearch    índice derivado       responde a busca por relevância
   ↓  cacheia
Redis            cache                 devolve a mesma consulta em memória
```

## Como rodar

O ambiente precisa estar no ar. Se não estiver:

```bash
../subir.sh
```

Depois:

```bash
./integrar.py
```

Leva uns 15 segundos e imprime as seis etapas.

## O que cada etapa mostra

**1. MongoDB grava o catálogo.** 12 produtos, com índice único em `sku`. A unicidade é garantida pelo servidor na escrita, não pela aplicação.

**2. Sincroniza para o Elasticsearch.** Lê do Mongo e indexa com `_bulk`. O Elasticsearch nunca recebe escrita direta: tudo que está nele veio da fonte.

**3. Busca por relevância.** `"notebook leve para viagem"`, com analyzer `brazilian` (tira stopwords e reduz ao radical) e `most_fields` para somar o score de nome e descrição.

O primeiro lugar é uma **mochila**, não um notebook. Não é defeito: o nome dela é curto e contém "notebook", e a descrição tem "leve" e "viagem", então ela casa com os três termos. O BM25 acertou as palavras e errou a intenção. É o limite da busca lexical, e é o que motiva a busca vetorial.

**4. Cache frio contra cache quente.** A mesma consulta, sete vezes cada. Medi do host e não por `docker exec`, porque o `docker exec` custa uns 50 ms e esconderia a diferença, que é de milissegundos.

Na última execução: 2,77 ms pelo Elasticsearch contra 0,18 ms pelo Redis, 15x.

**5. Invalidação.** Muda o preço no Mongo e refaz a consulta: ela ainda devolve o preço velho, vindo do cache. O TTL limita quanto tempo a divergência dura, mas não a impede. Invalidar tem que acontecer no mesmo fluxo que escreve.

**6. Descartabilidade.** Apaga o índice do Elasticsearch e as chaves de cache, e reconstrói tudo a partir do Mongo. Nenhum dado de negócio se perde, porque a verdade nunca esteve neles. Se o Mongo fosse apagado, não haveria de onde reconstruir.

## Arquivos

| | |
|---|---|
| `integrar.py` | o script da demonstração |
| `clientes.py` | clientes mínimos para os três bancos |

## Por que os clientes são feitos à mão

Nenhum driver instalado (`pymongo`, `redis`, `elasticsearch`), e não quis criar dependência para uma demonstração que precisa funcionar na hora.

- **Elasticsearch** fala HTTP, então `urllib` resolve.
- **Redis** fala RESP, que é simples o bastante para implementar em 30 linhas de socket.
- **MongoDB** fala protocolo binário, então vai por `mongosh` dentro do container. Nada do Mongo é cronometrado, então os 50 ms do `docker exec` não atrapalham.

## Onde ver o resultado

| | |
|---|---|
| MongoDB | `loja.produtos` pela extensão do VS Code |
| Elasticsearch | http://localhost:9200/produtos/_search?q=notebook |
| Redis | http://localhost:5540 (RedisInsight), chave `cache:busca:*` |

O script apaga só chaves com prefixo `cache:`. As `demo:` que o `subir.sh` cria para o RedisInsight ficam intactas.
