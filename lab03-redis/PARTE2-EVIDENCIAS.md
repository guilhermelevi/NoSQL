# Lab 3 – Redis – Parte 2 – Evidências de execução

Executado em 29/09/2026 14:56 · Redis 8.2.10 · macOS/OrbStack

Cobre as Seções 12 a 23. Continuei no mesmo banco da Parte 1, então as chaves criadas lá ainda estão no banco e aparecem na limpeza da Seção 23.

## SEÇÃO 12 – Streams

Stream é um log append-only. Diferente do Pub/Sub da Seção 11, a mensagem fica guardada e dá para ler depois, quantas vezes precisar.

### 12.1 – Inserindo eventos

```
XADD stream:pedidos * pedido_id 1001 status novo cliente "Ana"
XADD stream:pedidos * pedido_id 1002 status pago cliente "Bruno"
```

**Saída:**

```
1790704577849-0
1790704577905-0
```

> O * deixa o Redis gerar o ID, no formato timestamp-sequência. O primeiro número é a hora da inserção em milissegundos e o segundo desempata eventos gravados no mesmo milissegundo.

### 12.2 – Lendo eventos

```
XRANGE stream:pedidos - +
```

**Saída:**

```
1790704577849-0
pedido_id
1001
status
novo
cliente
Ana
1790704577905-0
pedido_id
1002
status
pago
cliente
Bruno
```

```
XREAD COUNT 10 STREAMS stream:pedidos 0
```

**Saída:**

```
stream:pedidos
1790704577849-0
pedido_id
1001
status
novo
cliente
Ana
1790704577905-0
pedido_id
1002
status
pago
cliente
Bruno
```

> O 0 faz ler desde o começo. A leitura não consome: os eventos continuam no stream, diferente de uma list com RPOP.

```
XLEN stream:pedidos
```

**Saída:**

```
2
```

### 12.3 – Consumer group

```
XGROUP CREATE stream:pedidos grupo:processadores 0 MKSTREAM
```

**Saída:**

```
OK
```

> O 0 faz o grupo começar do início do stream. O MKSTREAM criaria o stream se ele não existisse, mas aqui já existia.

### 12.4 – Consumindo pelo grupo

```
XREADGROUP GROUP grupo:processadores consumidor:1 COUNT 10 STREAMS stream:pedidos >
```

**Saída:**

```
stream:pedidos
1790704577849-0
pedido_id
1001
status
novo
cliente
Ana
1790704577905-0
pedido_id
1002
status
pago
cliente
Bruno
```

> O > pede só as mensagens que o grupo nunca recebeu. Rodando de novo o retorno vem vazio, porque as duas já foram entregues.

```
XREADGROUP GROUP grupo:processadores consumidor:1 COUNT 10 STREAMS stream:pedidos >
```

**Saída:**

```

```

### Extra: entrega pendente e confirmação

Isso não está no roteiro, mas sem ver a pendência o consumer group não faz muito sentido. As mensagens entregues ficam pendentes até o XACK:

```
XPENDING stream:pedidos grupo:processadores
```

**Saída:**

```
2
1790704577849-0
1790704577905-0
consumidor:1
2
```

> Duas pendentes. Se o consumidor:1 morrer agora elas não somem, ficam na lista de pendências e outro consumidor pode assumir. É o que o Pub/Sub não faz.

Confirmando o processamento da primeira mensagem:

```
XACK stream:pedidos grupo:processadores 1790704577849-0
```

**Saída:**

```
1
```

```
XPENDING stream:pedidos grupo:processadores
```

**Saída:**

```
1
1790704577905-0
1790704577905-0
consumidor:1
1
```

> Sobrou uma pendente. Enquanto o XACK não vem, o Redis considera a mensagem em aberto.

## SEÇÃO 13 – Bitmaps

Bitmap é uma string manipulada bit a bit, usada para marcar flag booleana de muita gente ao mesmo tempo.

### 13.1 – Marcando presença

```
SETBIT presenca:2026-03-15 1001 1
SETBIT presenca:2026-03-15 1002 1
SETBIT presenca:2026-03-15 1003 0
GETBIT presenca:2026-03-15 1001
GETBIT presenca:2026-03-15 1003
BITCOUNT presenca:2026-03-15
```

**Saída:**

```
0
0
0
1
0
2
```

> O SETBIT devolve o valor anterior do bit, não o novo, por isso os três primeiros vieram 0. O BITCOUNT contou 2 bits ligados.

O tamanho ocupado explica por que vale a pena:

```
STRLEN presenca:2026-03-15
```

**Saída:**

```
126
```

> 126 bytes para 1.004 usuários. O bit 1003 obriga a string a ter ceil(1004/8) = 126 bytes, e nesse espaço cabem 1.008 flags. Guardando os IDs numa lista seria vários bytes por usuário.

```
GETBIT presenca:2026-03-15 9999
```

**Saída:**

```
0
```

## SEÇÃO 14 – HyperLogLog

O HyperLogLog estima quantos elementos distintos existem, com erro de cerca de 0,81% e memória fixa, sem guardar os elementos.

### 14.1 – Visitantes únicos aproximados

```
PFADD hll:visitantes "u1" "u2" "u3" "u1" "u2"
PFCOUNT hll:visitantes
```

**Saída:**

```
1
3
```

> Cinco inserções e contagem 3. As repetições de u1 e u2 não somaram.

### 14.2 – Mesclando contadores

```
PFADD hll:dia1 "u1" "u2" "u3"
PFADD hll:dia2 "u3" "u4" "u5"
PFMERGE hll:total hll:dia1 hll:dia2
PFCOUNT hll:total
```

**Saída:**

```
1
1
OK
5
```

> Deu 5 porque o u3 está nos dois dias e conta uma vez. Somando as contagens diárias daria 6, errado. O PFMERGE resolve isso quando preciso dos únicos da semana a partir dos contadores de cada dia.

O espaço ocupado:

```
STRLEN hll:total
```

**Saída:**

```
31
```

> O HyperLogLog para de crescer em torno de 12 KB, tendo 3 ou milhões de valores distintos. Aqui deu 31 bytes porque com poucos elementos ele usa codificação esparsa. Em compensação não dá para perguntar se um usuário específico está lá nem fazer interseção.

## SEÇÃO 15 – Geoespacial

Os comandos GEO são uma camada em cima do sorted set: a coordenada vira um geohash de 52 bits usado como score, e é a ordenação desse score que permite buscar por proximidade.

### 15.1 – Inserindo pontos

```
GEOADD cidades:df -47.8825 -15.7942 "Brasilia"
GEOADD cidades:df -48.0770 -15.6014 "Taguatinga"
GEOADD cidades:df -47.9292 -15.7801 "LagoSul"
```

**Saída:**

```
1
1
1
```

> A ordem é longitude e depois latitude, ao contrário de como se costuma escrever coordenada. Se inverter, o Redis aceita sem reclamar e o ponto vai parar em outro lugar do mundo.

### 15.2 – Consultando distância

```
GEODIST cidades:df "Brasilia" "Taguatinga" km
GEODIST cidades:df "Brasilia" "LagoSul" km
```

**Saída:**

```
29.8936
5.2389
```

### 15.3 – Buscando por raio

```
GEOSEARCH cidades:df FROMLONLAT -47.8825 -15.7942 BYRADIUS 30 km WITHDIST
```

**Saída:**

```
Brasilia
0.0003
LagoSul
5.2386
Taguatinga
29.8934
```

As três estão dentro de 30 km. Baixando o raio para 10 km, Taguatinga sai:

```
GEOSEARCH cidades:df FROMLONLAT -47.8825 -15.7942 BYRADIUS 10 km WITHDIST
```

**Saída:**

```
Brasilia
0.0003
LagoSul
5.2386
```

Conferindo que por baixo é mesmo um sorted set:

```
TYPE cidades:df
ZSCORE cidades:df "Brasilia"
```

**Saída:**

```
zset
965555706610042
```

> O TYPE devolveu zset. Os comandos GEO são uma camada em cima do sorted set: a coordenada vira um geohash de 52 bits que é usado como score.

## SEÇÃO 16 – Memória e eviction

### 16.1 – Consultar memória

```
INFO memory
```

**Saída (só os campos que interessam, o INFO completo traz dezenas de linhas):**

```
used_memory:3167480
used_memory_human:3.02M
used_memory_peak_human:3.02M
used_memory_dataset:2030040
maxmemory:0
maxmemory_human:0B
maxmemory_policy:noeviction
```

### 16.2 – Ver política de eviction

```
CONFIG GET maxmemory
CONFIG GET maxmemory-policy
```

**Saída:**

```
maxmemory
0
maxmemory-policy
noeviction
```

> maxmemory 0 é sem limite, o Redis usa memória até o sistema operacional recusar. A política padrão noeviction recusa escrita nova quando bate o limite, em vez de apagar chave.

### 16.3 – Configurar limites de memória em tempo real

```
CONFIG SET maxmemory 512mb
CONFIG SET maxmemory-policy allkeys-lru
CONFIG GET maxmemory
CONFIG GET maxmemory-policy
```

**Saída:**

```
OK
OK
maxmemory
536870912
maxmemory-policy
allkeys-lru
```

```
INFO memory
```

**Saída (só os campos que interessam, o INFO completo traz dezenas de linhas):**

```
maxmemory:536870912
maxmemory_human:512.00M
maxmemory_policy:allkeys-lru
```

> O roteiro diz que o CONFIG SET não persiste depois de reiniciar. A Seção 19 reinicia o contêiner, então aproveitei para conferir isso lá.

### 16.4 – Políticas de eviction

| Política | Comportamento ao atingir `maxmemory` |

|---|---|

| `noeviction` | Recusa novas escritas com erro. Leituras continuam funcionando. Padrão. |

| `allkeys-lru` | Descarta as chaves usadas há mais tempo, **com ou sem TTL**. Adequado para cache puro. |

| `volatile-lru` | Descarta por LRU, mas **apenas entre chaves com TTL**. Protege dados permanentes. |

| `allkeys-random` | Descarta qualquer chave ao acaso. Mais barato, menos eficaz. |

| `volatile-ttl` | Descarta primeiro as chaves cujo TTL está mais próximo de vencer. |

> Se a instância é só cache, allkeys-lru serve. Se ela mistura cache com dado que não pode sumir, o allkeys-lru apaga o dado permanente sem avisar, e aí o certo é volatile-lru com TTL em tudo que é descartável.

## SEÇÃO 17 – Transações com MULTI / EXEC

### 17.1 – Exemplo de transação

Os comandos precisam rodar na mesma conexão, porque a transação é da sessão e não do servidor:

```
MULTI
SET pedido:1 "aberto"
INCR pedidos:contador
LPUSH fila:pedidos "pedido:1"
EXEC
```

**Saída (uma única conexão):**

```
OK
QUEUED
QUEUED
QUEUED
OK
1
5
```

> Dentro do bloco cada comando responde QUEUED e nada roda ainda. O EXEC dispara todos e devolve um array com o resultado de cada um, na ordem.

### Por que a conexão importa

Mandando os mesmos comandos em conexões separadas, a transação não existe:

```
MULTI
INCR pedidos:contador
EXEC
```

**Saída:**

```
OK
2
ERR EXEC without MULTI
```

> O MULTI morreu junto com a conexão dele. O INCR executou solto e o EXEC caiu em outra conexão, que nunca abriu transação. Numa aplicação isso acontece quando o pool entrega conexões diferentes a cada comando.

### 17.2 – Transferência entre saldos

```
SET saldo:conta1 500
SET saldo:conta2 300
```

**Saída:**

```
OK
OK
```

```
MULTI
DECRBY saldo:conta1 100
INCRBY saldo:conta2 100
EXEC
```

**Saída (uma única conexão):**

```
OK
QUEUED
QUEUED
400
400
```

```
GET saldo:conta1
GET saldo:conta2
```

**Saída:**

```
400
400
```

> Débito e crédito saíram juntos, sem outro cliente ver o estado no meio, com o dinheiro fora de uma conta e ainda não na outra.

### 17.3 – Cancelando transação antes de executar

```
MULTI
SET teste:1 "x"
SET teste:2 "y"
DISCARD
```

**Saída (uma única conexão):**

```
OK
QUEUED
QUEUED
OK
```

```
EXISTS teste:1
EXISTS teste:2
```

**Saída:**

```
0
0
```

### 17.4 – Inspecionando resultado

```
GET pedido:1
GET pedidos:contador
LRANGE fila:pedidos 0 -1
```

**Saída:**

```
aberto
2
pedido:1
p1
p2
p3
p4
```

### O limite do MULTI/EXEC: não há rollback

Se um comando da fila falhar na hora de executar, os outros são aplicados mesmo assim:

```
SET nao:e:numero "texto"
```

**Saída:**

```
OK
```

```
MULTI
INCR nao:e:numero
SET marcador:pos:erro "fui gravado"
EXEC
```

**Saída (uma única conexão):**

```
OK
QUEUED
QUEUED
ERR value is not an integer or out of range

OK
```

```
GET marcador:pos:erro
GET nao:e:numero
```

**Saída:**

```
fui gravado
texto
```

> O INCR falhou dentro do EXEC porque a chave não é número, mas o SET seguinte foi aplicado assim mesmo e a chave marcador:pos:erro existe. Então o MULTI/EXEC garante que ninguém se intromete no meio, mas não desfaz nada. Num banco relacional o erro derrubaria a transação inteira.

## SEÇÃO 18 – Script Lua com EVAL

O script Lua roda no servidor como uma unidade só, sem nenhum outro comando entrar no meio.

### 18.1 – Rate limit atômico com INCR + EXPIRE

```
EVAL "local v = redis.call('INCR', KEYS[1]) if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end return v" 1 rl:ip:192.168.0.10 60
```

**Saída:**

```
1
```

Rodando várias vezes, como o roteiro pede:

```
EVAL "local v = redis.call('INCR', KEYS[1]) if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end return v" 1 rl:ip:192.168.0.10 60
EVAL "local v = redis.call('INCR', KEYS[1]) if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end return v" 1 rl:ip:192.168.0.10 60
TTL rl:ip:192.168.0.10
```

**Saída:**

```
2
3
60
```

> O contador sobe toda vez, mas o EXPIRE só roda quando v == 1, ou seja na primeira requisição da janela. O TTL não é renovado depois, então os 60 segundos contam do primeiro acesso.

Comparando com a Seção 10.3, que usava dois comandos separados:

| | Seção 10.3 (`INCR` + `EXPIRE`) | Seção 18 (script Lua) |

|---|---|---|

| Idas ao servidor | 2 | 1 |

| Atomicidade | Não, há um instante entre os dois comandos | Sim, o script é indivisível |

| Risco | Se o processo cair entre o INCR e o EXPIRE a chave fica sem TTL e o usuário nunca mais é liberado | Nenhum, ou executa tudo ou nada |

> O ganho não é economizar uma viagem de rede, é que o script roda inteiro no servidor e não existe mais o instante sem TTL que eu vi na Seção 10.3.

## SEÇÃO 19 – Persistência

### 19.1 – Verificar AOF

```
CONFIG GET appendonly
CONFIG GET appendfsync
CONFIG GET save
```

**Saída:**

```
appendonly
yes
appendfsync
everysec
save
3600 1 300 100 60 10000
```

> Liguei o AOF no docker-compose com --appendonly yes, porque a imagem oficial vem com ele desligado. Sem isso o CONFIG GET aqui devolveria no e o teste de persistência dependeria só do snapshot RDB. O save mostra que os gatilhos do RDB continuam ativos, os dois funcionam juntos.

### 19.2 – Criar dado para teste

```
SET persist:test "ok"
GET persist:test
DBSIZE
```

**Saída:**

```
OK
ok
47
```

### 19.3 – Reiniciar container

```bash
$ docker restart redis
```

**Saída:**

```
redis
```

### 19.4 – Validar persistência

```
PING
GET persist:test
DBSIZE
```

**Saída:**

```
PONG
ok
47
```

> O dado sobreviveu ao reinício. Com o AOF ligado o Redis reconstrói o estado relendo o log de escritas.

Aproveitei o reinício para conferir o que a Seção 16.3 diz sobre o CONFIG SET não persistir:

```
CONFIG GET maxmemory
CONFIG GET maxmemory-policy
```

**Saída:**

```
maxmemory
0
maxmemory-policy
noeviction
```

> Confirmado o que o roteiro diz na 16.3: o maxmemory voltou para 0 e a política para noeviction. Os 512 MB que eu tinha configurado sumiram, porque o CONFIG SET só mexe na memória do processo. Para valer depois do reinício tem que estar no redis.conf ou nos argumentos do contêiner, que é onde coloquei o --appendonly yes.

```
INFO persistence
```

**Saída (só os campos que interessam, o INFO completo traz dezenas de linhas):**

```
loading:0
rdb_last_bgsave_status:ok
aof_enabled:1
aof_last_bgrewrite_status:ok
aof_last_write_status:ok
```

### 19.5 – RDB e AOF lado a lado

| | RDB | AOF |

|---|---|---|

| O que grava | Snapshot binário do dataset inteiro | Cada comando de escrita, em sequência |

| Quando grava | Em intervalos (`save`) ou sob demanda | Continuamente, com `fsync` conforme `appendfsync` |

| Tamanho em disco | Menor, formato compacto | Maior, cresce até o rewrite |

| Recuperação | Rápida: carrega o arquivo de uma vez | Mais lenta: reexecuta o log |

| Perda possível | Tudo desde o último snapshot | Até 1 segundo com `appendfsync everysec` |

> Não precisa escolher um. Aqui os dois estão ligados: RDB como snapshot para cópia e AOF para durabilidade.

## SEÇÃO 20 – Exercício integrador

Cenário com uma estrutura diferente para cada necessidade.

### Uma colisão de tipo antes de começar

O primeiro comando do exercício integrador, rodando exatamente como o roteiro pede, falha:

```
HSET user:1001 nome "João" idade 40 cidade "Brasília"
```

**Saída:**

```
WRONGTYPE Operation against a key holding the wrong kind of value

```

```
TYPE user:1001
GET user:1001
```

**Saída:**

```
string
João Silva
```

> A Seção 5.1 da Parte 1 criou user:1001 como string, com SET e APPEND, e a Seção 20 tenta usar a mesma chave como hash. No Redis a chave tem tipo e comando de outro tipo é recusado, não converte nem sobrescreve. A lista de limpeza da Seção 23 também não apaga essa chave entre uma seção e outra.

Apaguei a chave para conseguir seguir. Esse DEL não está no roteiro:

```
DEL user:1001
EXISTS user:1001
```

**Saída:**

```
1
0
```

> O SET sobrescreve qualquer chave sem reclamar, mas HSET, LPUSH, SADD e ZADD exigem que a chave não exista ou já seja do tipo certo. Por isso não vale reaproveitar nome: user:1001 como string e como hash deveriam ser chaves diferentes.

### O cenário, agora executando

```
HSET user:1001 nome "João" idade 40 cidade "Brasília"
SET session:1001 "token-abc" EX 120
SET acessos:user:1001 0
INCR acessos:user:1001
LPUSH fila:cadastros "user:1001"
ZADD ranking:gamificacao 100 "joao"
PUBLISH canal:usuarios "Novo cadastro user:1001"
XADD stream:usuarios * evento cadastro usuario 1001
```

**Saída:**

```
3
OK
OK
1
1
1
1
1790704583360-0
```

**O assinante de canal:usuarios, que eu inscrevi antes de publicar, recebeu:**

```
subscribe
canal:usuarios
1
message
canal:usuarios
Novo cadastro user:1001
```

Estado final de cada estrutura:

```
HGETALL user:1001
GET session:1001
TTL session:1001
GET acessos:user:1001
LRANGE fila:cadastros 0 -1
ZREVRANGE ranking:gamificacao 0 -1 WITHSCORES
XRANGE stream:usuarios - +
```

**Saída:**

```
nome
João
idade
40
cidade
Brasília
token-abc
119
1
user:1001
joao
100
1790704583360-0
evento
cadastro
usuario
1001
```

### Respostas às perguntas do roteiro

**Qual estrutura foi usada em cada caso?**

| Caso | Estrutura |

|---|---|

| Usuário | hash |

| Sessão | string com TTL |

| Contador de acessos | string com INCR |

| Fila de cadastros | list |

| Ranking | sorted set |

| Notificação | Pub/Sub |

| Eventos | stream |

**Em quais situações o TTL é importante?** Em dado temporário, que pode sumir sem ser erro: cache, sessão, token, rate limit e lock. O TTL evita ter que escrever uma rotina para limpar o que venceu.

**Quando usar Pub/Sub e quando usar Streams?** Pub/Sub quando a mensagem só interessa a quem está conectado na hora e perder não é problema. Stream quando preciso de histórico, releitura ou confirmação de processamento. Na Seção 11 publiquei sem assinante e o retorno foi 0: a mensagem se perdeu.

**Quando uma list basta e quando um stream é melhor?** A list basta para fila simples, em que o item é consumido uma vez e some. O stream é melhor quando preciso saber o que passou pela fila, reprocessar, ou garantir que a mensagem não se perca se o consumidor morrer no meio, que é o que o XPENDING mostrou na Seção 12.

**Por que sorted set é adequado para ranking?** Porque ele mantém a ordem a cada escrita e responde tanto o topo, com ZREVRANGE, quanto a posição de um participante, com ZREVRANK, sem varrer a estrutura. Com list eu teria que reordenar a cada atualização.

## SEÇÃO 22 – Boas práticas

> O roteiro pula da Seção 20 para a 22, não existe Seção 21.

**1) Padronizar chaves com prefixos.** user:1001, session:abc123, cache:pagina:/home. O Redis não tem tabela nem coleção, o prefixo é a única organização que existe, e é com ele que o RedisInsight monta a árvore de chaves.

**2) Evitar KEYS * em produção.** Ele varre o keyspace inteiro e bloqueia o servidor. O SCAN faz o mesmo em fatias, devolvendo cursor, como na Seção 3.4.

**3) Usar TTL em dado temporário.** Cache, sessão, token e rate limit.

**4) Escolher a estrutura certa.** string para valor simples, hash para objeto, list para fila, set para unicidade, zset para ranking e stream para evento que precisa ficar guardado.

**5) Entender a persistência.** RDB para snapshot e AOF para durabilidade, comparados na Seção 19.

**6) Monitorar memória, TTL e crescimento de chaves.** INFO memory, DBSIZE e a política de eviction. Chave sem TTL que deveria ter é memória que só cresce.

**7) Para operação composta, usar MULTI/EXEC ou Lua.** Lembrando que o MULTI/EXEC não desfaz nada, como vi na Seção 17. Quando preciso ler um valor e decidir o que gravar, tem que ser Lua, porque o MULTI enfileira sem executar e não dá para ramificar.

## SEÇÃO 23 – Limpeza final do laboratório

Rodando a lista de DEL do roteiro:

```
DBSIZE
DEL visitas saldo codigo
DEL aluno:1 aluno:2 aluno:3
DEL fila:processamento fila:pedidos fila:etl fila:emails
DEL curso:BI curso:DS interesses:python interesses:redis
DEL ranking:pontos ranking:jogo ranking:turma ranking:gamificacao
DEL rl:user:42 rl:ip:192.168.0.10
DEL cache:home cache:pagina:/home cache:consulta:clientes
DEL session:abc123 session:user:1001 session:1001
DEL persist:test
DEL presenca:2026-03-15
DEL hll:visitantes hll:dia1 hll:dia2 hll:total
DEL stream:pedidos stream:usuarios
DEL cidades:df
DEL saldo:conta1 saldo:conta2
DBSIZE
```

**Saída:**

```
52
3
3
4
4
4
2
2
3
1
1
4
2
1
2
16
```

> Cada DEL diz quantas chaves apagou. Os zeros são chaves que já não existiam, como cache:pagina:/home, que eu apaguei na Seção 4.5.

Vendo o que sobrou depois da limpeza do roteiro:

```
KEYS *
```

**Saída:**

```
fila:cadastros
acessos:user:1001
user:2003
nao:e:numero
contador:login
session:user:2002
user:2002
user:2001
ranking:torneio
marcador:pos:erro
pedido:1
cache:pagina:/produtos
pedidos:contador
visitas:pagina:/produtos
user:1001
equipe:sorteio
```

> Sobraram 14 chaves. A maior parte é de seção do próprio roteiro que ficou fora da lista de DEL: user:2001 a user:2003 da 5.2, equipe:sorteio da 6.5, pedido:1 e pedidos:contador da 17.1, e user:1001, acessos:user:1001 e fila:cadastros da Seção 20. O resto é dos exercícios. Limpar por lista fixa não funciona bem, qualquer chave nova em outro ponto do roteiro já deixa a lista desatualizada.

Apaguei o resto por prefixo, usando SCAN em vez de KEYS:

```bash
$ docker exec redis sh -c "redis-cli --scan --pattern 'user:*' | xargs -r redis-cli DEL"
```

**Saída:**

```
4
```

```bash
$ docker exec redis sh -c "redis-cli --scan --pattern '*' | xargs -r redis-cli DEL"
```

**Saída:**

```
12
```

```
DBSIZE
KEYS *
```

**Saída:**

```
0

```

> Banco zerado. O --scan do redis-cli faz a iteração incremental sozinho, sem travar o servidor, então é assim que apago em massa.

---

Fim do laboratório. O ambiente continua no ar, para derrubar é docker compose down na pasta lab03-redis.
