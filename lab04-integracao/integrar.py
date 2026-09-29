#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab 4 - Integracao dos tres bancos num cenario unico.

  MongoDB        fonte da verdade do catalogo, com escrita confirmada
  Elasticsearch  indice derivado, responde busca por relevancia
  Redis          cache da consulta, responde em memoria

O que o script demonstra, em ordem:
  1. grava o catalogo no MongoDB
  2. sincroniza para o Elasticsearch
  3. busca por texto e mostra o ranking por relevancia
  4. mede a mesma consulta com cache frio e com cache quente
  5. muda o preco na fonte e mostra o problema de invalidacao
  6. apaga Elasticsearch e Redis e reconstroi tudo a partir do MongoDB

uso: ./integrar.py
"""
import json
import statistics
import sys
import time

from clientes import Redis, Elastic, Mongo

INDICE = "produtos"
COLECAO = "produtos"
TERMO = "notebook leve para viagem"
CHAVE_CACHE = f"cache:busca:{TERMO}"
REPETICOES = 7

CATALOGO = [
    {"sku": "NB-001", "nome": "Notebook UltraLeve 13",
     "descricao": "Notebook leve de 13 polegadas com 1,1 kg, ideal para viagem de trabalho.",
     "categoria": "informatica", "preco": 6499.00, "estoque": 12},
    {"sku": "NB-002", "nome": "Notebook Gamer 17",
     "descricao": "Notebook potente de 17 polegadas para jogos, pesado e com bateria curta, nao recomendado para viagem.",
     "categoria": "informatica", "preco": 9299.00, "estoque": 4},
    {"sku": "NB-003", "nome": "Notebook Basico 15",
     "descricao": "Notebook de uso geral para estudo e escritorio, com boa autonomia de bateria.",
     "categoria": "informatica", "preco": 3199.00, "estoque": 27},
    {"sku": "MO-001", "nome": "Mochila para Notebook",
     "descricao": "Mochila leve com compartimento acolchoado para notebook, pensada para viagem de trabalho.",
     "categoria": "acessorios", "preco": 289.90, "estoque": 63},
    {"sku": "FO-001", "nome": "Fone com Cancelamento de Ruido",
     "descricao": "Fone de ouvido leve, dobravel, com cancelamento de ruido para uso em aviao e viagem.",
     "categoria": "audio", "preco": 1299.00, "estoque": 18},
    {"sku": "TB-001", "nome": "Tablet 11 polegadas",
     "descricao": "Tablet leve para leitura e video, boa opcao de viagem para quem nao precisa de teclado.",
     "categoria": "informatica", "preco": 2799.00, "estoque": 9},
    {"sku": "MN-001", "nome": "Monitor Ultrawide 34",
     "descricao": "Monitor ultrawide de 34 polegadas para produtividade em mesa fixa.",
     "categoria": "informatica", "preco": 3899.00, "estoque": 6},
    {"sku": "TC-001", "nome": "Teclado Mecanico Compacto",
     "descricao": "Teclado mecanico sem teclado numerico, compacto e leve para levar na mochila.",
     "categoria": "acessorios", "preco": 549.00, "estoque": 31},
    {"sku": "CB-001", "nome": "Carregador GaN 65W",
     "descricao": "Carregador compacto e leve de 65W que substitui a fonte do notebook em viagem.",
     "categoria": "acessorios", "preco": 329.00, "estoque": 44},
    {"sku": "HD-001", "nome": "SSD Externo 1TB",
     "descricao": "SSD externo portatil de 1TB, resistente e leve, para backup em viagem.",
     "categoria": "armazenamento", "preco": 699.00, "estoque": 22},
    {"sku": "CF-001", "nome": "Cafeteira Eletrica",
     "descricao": "Cafeteira eletrica de 1 litro para uso domestico.",
     "categoria": "casa", "preco": 259.00, "estoque": 15},
    {"sku": "CD-001", "nome": "Cadeira de Escritorio Ergonomica",
     "descricao": "Cadeira ergonomica com apoio lombar para longas jornadas sentado.",
     "categoria": "casa", "preco": 1899.00, "estoque": 7},
]

V, A, X, Z, N = "\033[32m", "\033[33m", "\033[31m", "\033[0m", "\033[2m"


def etapa(n, titulo):
    print(f"\n{'─' * 72}")
    print(f"ETAPA {n}  {titulo}")
    print("─" * 72)


def ok(msg):
    print(f"  {V}ok{Z}    {msg}")


def info(msg):
    print(f"        {msg}")


def nota(msg):
    print(f"  {N}{msg}{Z}")


# ─────────────────────────────────────────────────────────────────────
def indexar_tudo(es, mongo):
    """Le o catalogo do MongoDB e reconstroi o indice do Elasticsearch."""
    produtos = mongo.json(
        "print(EJSON.stringify(db.%s.find({}, {_id:0}).toArray()))" % COLECAO
    )
    es.req("DELETE", f"/{INDICE}")
    es.req("PUT", f"/{INDICE}", {
        "mappings": {"properties": {
            "sku": {"type": "keyword"},
            "nome": {"type": "text", "analyzer": "brazilian"},
            "descricao": {"type": "text", "analyzer": "brazilian"},
            "categoria": {"type": "keyword"},
            "preco": {"type": "double"},
            "estoque": {"type": "integer"},
        }}
    })
    linhas = []
    for p in produtos:
        linhas.append(json.dumps({"index": {"_index": INDICE, "_id": p["sku"]}}))
        linhas.append(json.dumps(p))
    r = es.req("POST", "/_bulk?refresh=true", "\n".join(linhas) + "\n", ndjson=True)
    if r.get("errors"):
        raise RuntimeError("o bulk falhou: " + json.dumps(r)[:300])
    return len(produtos)


def buscar_no_es(es, termo):
    r = es.req("POST", f"/{INDICE}/_search", {
        "size": 4,
        "query": {"multi_match": {
            "query": termo,
            "fields": ["nome^2", "descricao"],
            "type": "most_fields",
        }},
        "_source": ["sku", "nome", "preco"],
    })
    return [{"sku": h["_source"]["sku"],
             "nome": h["_source"]["nome"],
             "preco": h["_source"]["preco"],
             "score": round(h["_score"], 3)} for h in r["hits"]["hits"]]


def consultar(es, redis, termo, usar_cache=True):
    """Devolve (itens, origem, milissegundos)."""
    t0 = time.perf_counter()
    if usar_cache:
        bruto = redis.cmd("GET", CHAVE_CACHE)
        if bruto is not None:
            itens = json.loads(bruto)
            return itens, "redis", (time.perf_counter() - t0) * 1000
    itens = buscar_no_es(es, termo)
    redis.cmd("SET", CHAVE_CACHE, json.dumps(itens), "EX", 300)
    return itens, "elasticsearch", (time.perf_counter() - t0) * 1000


# ─────────────────────────────────────────────────────────────────────
def main():
    print()
    print("LAB 4 - INTEGRACAO: MongoDB, Elasticsearch e Redis")

    try:
        redis = Redis()
        es = Elastic()
        mongo = Mongo()
        if not es.req("GET", "/_cluster/health").get("status"):
            raise RuntimeError("Elasticsearch nao respondeu")
        redis.cmd("PING")
    except Exception as e:
        print(f"\n  {X}Ambiente nao esta pronto:{Z} {e}")
        print("  Rode o ./subir.sh na raiz do projeto antes.\n")
        return 1

    # ---------- 1 ----------
    etapa(1, "MongoDB grava o catalogo (fonte da verdade)")
    mongo.eval(f"db.{COLECAO}.drop()")
    mongo.eval(
        f"db.{COLECAO}.insertMany({json.dumps(CATALOGO, ensure_ascii=False)});"
        f"db.{COLECAO}.createIndex({{ sku: 1 }}, {{ unique: true }});"
    )
    total = int(mongo.eval(f"print(db.{COLECAO}.countDocuments({{}}))"))
    ok(f"{total} produtos gravados em loja.{COLECAO}")
    nota("indice unico em sku: quem garante a unicidade e o servidor, na escrita")

    # ---------- 2 ----------
    etapa(2, "Sincroniza MongoDB para o Elasticsearch")
    n = indexar_tudo(es, mongo)
    ok(f"{n} produtos indexados em '{INDICE}' via _bulk")
    nota("o Elasticsearch nao recebeu escrita direta: tudo veio do MongoDB")

    # ---------- 3 ----------
    etapa(3, f"Busca por relevancia: \"{TERMO}\"")
    itens = buscar_no_es(es, TERMO)
    print()
    print(f"        {'score':>7}  {'sku':<8} {'produto':<36} preco")
    for i in itens:
        print(f"        {i['score']:>7.3f}  {i['sku']:<8} {i['nome']:<36} R$ {i['preco']:>8.2f}")
    print()
    nota("o analyzer brazilian tira as stopwords e reduz ao radical:")
    nota('"notebook leve para viagem" vira [notebook, lev, viag]')
    print()
    print(f"  {A}repare{Z}  o primeiro lugar e uma MOCHILA, nao um notebook.")
    nota("o nome dela e curto e tem 'notebook', e a descricao tem 'leve' e")
    nota("'viagem': ela casa com os tres termos. O BM25 acertou as palavras")
    nota("e errou a intencao, porque ele nao sabe o que a pessoa quer comprar.")
    nota("e esse limite que a busca vetorial resolve, comparando significado")
    nota("em vez de grafia.")

    # ---------- 4 ----------
    etapa(4, "A mesma consulta, com cache frio e com cache quente")
    frios, quentes = [], []
    for _ in range(REPETICOES):
        redis.cmd("DEL", CHAVE_CACHE)
        _, origem, ms = consultar(es, redis, TERMO)
        assert origem == "elasticsearch"
        frios.append(ms)
        _, origem, ms = consultar(es, redis, TERMO)
        assert origem == "redis"
        quentes.append(ms)

    frio, quente = statistics.median(frios), statistics.median(quentes)
    print()
    info(f"cache frio   Elasticsearch   {frio:6.2f} ms   (mediana de {REPETICOES})")
    info(f"cache quente Redis           {quente:6.2f} ms   (mediana de {REPETICOES})")
    print()
    if quente > 0:
        ok(f"{frio / quente:.1f}x mais rapido vindo do cache")
    nota("o Redis nao e mais rapido por ser melhor: ele so nao precisa")
    nota("calcular nada, devolve o resultado que o Elasticsearch ja montou")

    # ---------- 5 ----------
    etapa(5, "O preco muda na fonte: o problema da invalidacao")
    mongo.eval(f"db.{COLECAO}.updateOne({{ sku: 'NB-001' }}, {{ $set: {{ preco: 5999.00 }} }})")
    novo = mongo.json(f"print(EJSON.stringify(db.{COLECAO}.findOne({{sku:'NB-001'}},{{_id:0,preco:1}})))")
    ok(f"MongoDB atualizado: NB-001 agora custa R$ {novo['preco']:.2f}")

    itens, origem, _ = consultar(es, redis, TERMO)
    antigo = next((i for i in itens if i["sku"] == "NB-001"), None)
    if antigo:
        print(f"  {A}atencao{Z}  a consulta ainda devolve R$ {antigo['preco']:.2f}, vindo do {origem}")
    nota("o cache nao sabe que a fonte mudou; o TTL limita quanto tempo essa")
    nota("divergencia dura, mas nao a impede")

    print()
    redis.cmd("DEL", CHAVE_CACHE)
    indexar_tudo(es, mongo)
    itens, origem, _ = consultar(es, redis, TERMO)
    corrigido = next((i for i in itens if i["sku"] == "NB-001"), None)
    if corrigido:
        ok(f"apos invalidar o cache e reindexar: R$ {corrigido['preco']:.2f}, vindo do {origem}")
    nota("invalidar tem que acontecer no mesmo fluxo que escreve no MongoDB")

    # ---------- 6 ----------
    etapa(6, "Elasticsearch e Redis sao descartaveis")
    es.req("DELETE", f"/{INDICE}")
    apagadas = 0
    for chave in (redis.cmd("KEYS", "cache:*") or []):
        apagadas += redis.cmd("DEL", chave)
    sumiu = es.req("GET", f"/{INDICE}").get("status") == 404
    ok(f"indice '{INDICE}' apagado: {sumiu} | {apagadas} chave(s) de cache removida(s)")
    nota("apaguei so o prefixo cache:, para nao levar junto as chaves demo:")

    n = indexar_tudo(es, mongo)
    itens, origem, ms = consultar(es, redis, TERMO)
    ok(f"reconstruido do MongoDB: {n} produtos, busca voltou {len(itens)} resultados")
    nota("nenhum dado de negocio se perdeu, porque a verdade nunca esteve neles")
    nota("se o MongoDB tivesse sido apagado, nao haveria de onde reconstruir")

    print(f"\n{'─' * 72}")
    print("RESUMO")
    print("─" * 72)
    info("MongoDB        fonte da verdade      escrita confirmada, indice unico")
    info("Elasticsearch  indice derivado       busca por relevancia, reconstruivel")
    info("Redis          cache                 %.1fx mais rapido, descartavel" % (frio / quente if quente else 0))
    print()
    info("MongoDB        loja.produtos                      (extensao do VS Code)")
    info("Elasticsearch  http://localhost:9200/produtos/_search?q=notebook")
    info("Redis          http://localhost:5540              (RedisInsight)")
    print()

    redis.fechar()
    return 0


if __name__ == "__main__":
    sys.exit(main())
