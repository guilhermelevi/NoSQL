# Bancos de Dados Não Relacionais — CEUB

Prof. Raul Carvalho de Souza · Aluno: Guilherme Levi

Todos os laboratórios foram executados no **macOS (Apple Silicon) com OrbStack**, em vez da VM Ubuntu/VirtualBox que os roteiros pedem. Isso dispensa `scp`, `sudo` e o redirecionamento de portas do VirtualBox — as portas dos containers já ficam acessíveis em `localhost`.

## Aula

[**AULA-NoSQL.pdf**](aula/AULA-NoSQL.pdf) — 80 páginas consolidando os três laboratórios: 11 módulos (430 min), 14 armadilhas reais de ambiente, 14 exercícios com solução comentada, 14 questões de avaliação, tabela de decisão e glossário de 42 termos. Todo comando e toda saída citados foram executados nos labs ou verificados contra os bancos no ar. Regenerável com `aula/fonte/gerar.sh`.

## Laboratórios

| Lab | Stack | Pasta | Entrega |
|---|---|---|---|
| 01 | MongoDB 8.2 | [`lab01-mongodb/`](lab01-mongodb/) | [GABARITO.md](lab01-mongodb/GABARITO.md) + [Playgrounds/](lab01-mongodb/Playgrounds/) |
| 02 | Elasticsearch 8.15 + Kibana + Logstash | [`lab02-elastic/`](lab02-elastic/) | [PARTE1-EVIDENCIAS.md](lab02-elastic/PARTE1-EVIDENCIAS.md) + [PARTE2-EVIDENCIAS.md](lab02-elastic/PARTE2-EVIDENCIAS.md) |
| 03 | Redis 8.2 + RedisInsight | [`lab03-redis/`](lab03-redis/) | [PARTE1-EVIDENCIAS.md](lab03-redis/PARTE1-EVIDENCIAS.md) + [PARTE2-EVIDENCIAS.md](lab03-redis/PARTE2-EVIDENCIAS.md) |
| 04 | Integração dos três | [`lab04-integracao/`](lab04-integracao/) | [README.md](lab04-integracao/README.md) + `integrar.py` |

## Subir tudo

```bash
./subir.sh      # sobe os tres labs integrados e deixa pronto para demonstrar
./demo.sh       # grava no Mongo e acompanha chegar no Elasticsearch
```

O `subir.sh` liga o OrbStack se preciso, sobe os composes na ordem certa, espera cada serviço, cria a data view no Kibana, registra o Redis no RedisInsight e testa o caminho do log antes de dizer que está pronto.

## Como subir

O Lab 2 sobe primeiro: o MongoDB do Lab 1 envia seus logs via GELF para o Logstash.

```bash
cd lab02-elastic && docker compose up -d    # Elasticsearch, Kibana, Logstash
cd ../lab01-mongodb && docker compose up -d # MongoDB
cd ../lab03-redis && docker compose up -d   # Redis e RedisInsight (independente dos demais)
```

Se o Logstash não estiver no ar, o MongoDB sobe do mesmo jeito — o GELF usa UDP e não bloqueia a inicialização. Você só não verá os logs no Kibana.

Para derrubar, `docker compose down` em cada pasta.

## Portas

| Serviço | URL |
|---|---|
| Kibana | http://localhost:5601 |
| Elasticsearch | http://localhost:9200 |
| MongoDB | `localhost:27017` (admin / 123456) |
| Logstash (GELF) | `localhost:12201/udp` |
| Redis | `localhost:6379` |
| RedisInsight | http://localhost:5540 |

## Observações de ambiente

**Lab 1** — a imagem `mongo:4.4` do roteiro não sobe no OrbStack (bug SERVER-121912: incompatibilidade com kernel 6.19+; o OrbStack usa 7.0). Trocada por `mongo:8.2`, que já traz o `mongosh` embutido — por isso a Parte 2 (instalação via apt) não foi necessária. Detalhes em [NOTAS-AMBIENTE.md](lab01-mongodb/NOTAS-AMBIENTE.md).

**Lab 2** — o roteiro foi escrito para Elasticsearch 7.x. Aqui roda o 8.15, com `xpack.security.enabled=false` (o 8.x exige HTTPS e token por padrão, o que inviabilizaria o roteiro). Duas diferenças relevantes estão documentadas nas evidências: `dense_vector` já nasce com `index`/`similarity` e aceita a query `knn` nativa; e a afirmação da seção 12.3 de que `match "joao"` encontraria `"João"` não se confirma — o analyzer `standard` faz lowercase mas não remove acentos.

**Lab 3** — o roteiro pede `scp` para a VM e `sudo docker`; aqui nada disso é necessário. O AOF foi ligado no compose (`--appendonly yes`), porque a imagem oficial vem com ele desligado e sem isso a Seção 19 não demonstraria persistência. Duas divergências do roteiro estão registradas nas evidências: a Seção 20 colide com a 5.1 ao usar `user:1001` como hash depois de a chave já existir como string (`WRONGTYPE`), e a lista de limpeza da Seção 23 deixa 14 chaves para trás.

## Scripts

[`lab02-elastic/scripts/`](lab02-elastic/scripts/) reexecuta o Lab 2 inteiro contra um Elasticsearch limpo, gerando os arquivos de evidência:

```bash
cd lab02-elastic
./scripts/parte1-executar.sh saida-parte1.md   # Partes 1 a 11
./scripts/parte2-executar.sh saida-parte2.md   # Partes 12 a 14
```

[`lab03-redis/scripts/`](lab03-redis/scripts/) faz o mesmo para o Lab 3. A Parte 2 depende do estado deixado pela Parte 1, então use o `gerar.sh`, que roda as duas na ordem:

```bash
./lab03-redis/scripts/gerar.sh
```
