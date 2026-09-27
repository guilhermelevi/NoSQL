#!/bin/bash
# Reexecuta o laboratorio 3 inteiro e regera os dois arquivos de evidencia.
# A Parte 2 depende do estado deixado pela Parte 1, entao a ordem importa.
set -e
cd "$(dirname "$0")"
docker compose -f ../docker-compose.yml up -d
until docker exec redis redis-cli PING >/dev/null 2>&1; do sleep 1; done
docker exec redis redis-cli FLUSHDB >/dev/null
./parte1.sh ../PARTE1-EVIDENCIAS.md
./parte2.sh ../PARTE2-EVIDENCIAS.md
echo "--- pronto ---"
wc -l ../PARTE1-EVIDENCIAS.md ../PARTE2-EVIDENCIAS.md
