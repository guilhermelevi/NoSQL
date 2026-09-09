# Bancos de Dados Não Relacionais — CEUB

Prof. Raul Carvalho de Souza · Aluno: Guilherme Levi

Todos os laboratórios foram executados no **macOS (Apple Silicon) com OrbStack**, em vez da VM Ubuntu/VirtualBox que os roteiros pedem. Isso dispensa `scp`, `sudo` e o redirecionamento de portas do VirtualBox — as portas dos containers já ficam acessíveis em `localhost`.

## Laboratórios

| Lab | Stack | Pasta | Entrega |
|---|---|---|---|
| 01 | MongoDB 8.2 | [`lab01-mongodb/`](lab01-mongodb/) | [GABARITO.md](lab01-mongodb/GABARITO.md) + [Playgrounds/](lab01-mongodb/Playgrounds/) |
| 02 | Elasticsearch 8.15 + Kibana + Logstash | [`lab02-elastic/`](lab02-elastic/) | [PARTE1-EVIDENCIAS.md](lab02-elastic/PARTE1-EVIDENCIAS.md) + [PARTE2-EVIDENCIAS.md](lab02-elastic/PARTE2-EVIDENCIAS.md) |

## Como subir

O Lab 2 sobe primeiro: o MongoDB do Lab 1 envia seus logs via GELF para o Logstash.

```bash
cd lab02-elastic && docker compose up -d    # Elasticsearch, Kibana, Logstash
cd ../lab01-mongodb && docker compose up -d # MongoDB
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

## Observações de ambiente

**Lab 1** — a imagem `mongo:4.4` do roteiro não sobe no OrbStack (bug SERVER-121912: incompatibilidade com kernel 6.19+; o OrbStack usa 7.0). Trocada por `mongo:8.2`, que já traz o `mongosh` embutido — por isso a Parte 2 (instalação via apt) não foi necessária. Detalhes em [NOTAS-AMBIENTE.md](lab01-mongodb/NOTAS-AMBIENTE.md).

**Lab 2** — o roteiro foi escrito para Elasticsearch 7.x. Aqui roda o 8.15, com `xpack.security.enabled=false` (o 8.x exige HTTPS e token por padrão, o que inviabilizaria o roteiro). Duas diferenças relevantes estão documentadas nas evidências: `dense_vector` já nasce com `index`/`similarity` e aceita a query `knn` nativa; e a afirmação da seção 12.3 de que `match "joao"` encontraria `"João"` não se confirma — o analyzer `standard` faz lowercase mas não remove acentos.

## Scripts

[`lab02-elastic/scripts/`](lab02-elastic/scripts/) reexecuta o Lab 2 inteiro contra um Elasticsearch limpo, gerando os arquivos de evidência:

```bash
cd lab02-elastic
./scripts/parte1-executar.sh saida-parte1.md   # Partes 1 a 11
./scripts/parte2-executar.sh saida-parte2.md   # Partes 12 a 14
```
