#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clientes minimos para os tres bancos, sem instalar nenhuma dependencia.

Elasticsearch fala HTTP, entao urllib resolve.
Redis fala RESP, que e simples o bastante para implementar em 30 linhas.
MongoDB fala um protocolo binario, entao vai por mongosh dentro do container.

O motivo de conectar direto no Redis e no Elasticsearch, em vez de usar
docker exec nos dois, e que o docker exec custa ~50 ms por chamada. Como a
demonstracao compara uma consulta de ~10 ms com uma de ~1 ms, esse overhead
esconderia justamente o numero que interessa.
"""
import json
import socket
import subprocess
import urllib.request
import urllib.error


class Redis:
    """Cliente RESP minimo. Suporta o suficiente para esta demonstracao."""

    def __init__(self, host="localhost", port=6379):
        self.sock = socket.create_connection((host, port), timeout=5)
        self.buf = self.sock.makefile("rb")

    def cmd(self, *args):
        saida = b"*%d\r\n" % len(args)
        for a in args:
            b = str(a).encode()
            saida += b"$%d\r\n%s\r\n" % (len(b), b)
        self.sock.sendall(saida)
        return self._ler()

    def _ler(self):
        linha = self.buf.readline()
        if not linha:
            raise RuntimeError("conexao com o Redis caiu")
        tipo, corpo = linha[:1], linha[1:].rstrip(b"\r\n")
        if tipo == b"+":
            return corpo.decode()
        if tipo == b"-":
            raise RuntimeError(corpo.decode())
        if tipo == b":":
            return int(corpo)
        if tipo == b"$":
            n = int(corpo)
            if n == -1:
                return None
            return self.buf.read(n + 2)[:-2].decode()
        if tipo == b"*":
            n = int(corpo)
            if n == -1:
                return None
            return [self._ler() for _ in range(n)]
        raise RuntimeError("resposta inesperada do Redis: %r" % linha)

    def fechar(self):
        try:
            self.sock.close()
        except OSError:
            pass


class Elastic:
    """Cliente HTTP para o Elasticsearch."""

    def __init__(self, base="http://localhost:9200"):
        self.base = base.rstrip("/")

    def req(self, metodo, caminho, corpo=None, ndjson=False):
        url = self.base + caminho
        dados = None
        cabecalhos = {}
        if corpo is not None:
            if ndjson:
                dados = corpo.encode()
                cabecalhos["Content-Type"] = "application/x-ndjson"
            else:
                dados = json.dumps(corpo).encode()
                cabecalhos["Content-Type"] = "application/json"
        r = urllib.request.Request(url, data=dados, headers=cabecalhos, method=metodo)
        try:
            with urllib.request.urlopen(r, timeout=30) as resp:
                bruto = resp.read().decode()
                return json.loads(bruto) if bruto else {}
        except urllib.error.HTTPError as e:
            bruto = e.read().decode()
            try:
                return json.loads(bruto)
            except json.JSONDecodeError:
                return {"erro": bruto, "status": e.code}


class Mongo:
    """Chama o mongosh dentro do container. Nao e rapido, mas nada aqui e cronometrado."""

    def __init__(self, container="mongodb-container", banco="loja"):
        self.container = container
        self.banco = banco

    def eval(self, js):
        cmd = [
            "docker", "exec", self.container, "mongosh", "--quiet",
            "-u", "admin", "-p", "123456", "--authenticationDatabase", "admin",
            "--eval", f"db = db.getSiblingDB('{self.banco}');\n{js}",
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            raise RuntimeError(p.stderr.strip() or p.stdout.strip())
        return p.stdout.strip()

    def json(self, js):
        """Roda um comando que termina em EJSON.stringify e devolve o objeto."""
        saida = self.eval(js)
        linhas = [l for l in saida.split("\n") if l.strip().startswith(("{", "["))]
        if not linhas:
            raise RuntimeError("mongosh nao devolveu JSON: " + saida[:200])
        return json.loads(linhas[-1])
