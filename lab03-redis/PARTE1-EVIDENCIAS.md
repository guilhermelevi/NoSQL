# Lab 3 – Redis – Parte 1 – Evidências de execução

Executado em 29/09/2026 14:56 · Redis 8.2.10 · macOS/OrbStack

Cobre as Seções 1 a 11 e os Exercícios 1 a 8. Rodei todos os comandos no container `redis` e as saídas são as que apareceram.

## SEÇÃO 1 – Preparação do ambiente

O roteiro copia o ambiente para a VM com scp e usa sudo nos comandos. Fiz no macOS com OrbStack, então não precisei de nada disso: o docker-compose.yml fica no próprio projeto e as portas já respondem em localhost.

### 1.2 – Subir o ambiente

```bash
$ docker compose -f ../docker-compose.yml ps --format 'table {{.Name}}\t{{.State}}\t{{.Ports}}'
```

**Saída:**

```
NAME           STATE     PORTS
redis          running   0.0.0.0:6379->6379/tcp, [::]:6379->6379/tcp
redisinsight   running   0.0.0.0:5540->5540/tcp, [::]:5540->5540/tcp
```

### 1.3 e 1.4 – Acessar o redis-cli e testar a conexão

O roteiro dá duas opções, entrar no container ou instalar o redis-tools no host. Usei a primeira para não instalar nada:

```
PING
```

**Saída:**

```
PONG
```

### 1.5 – Informações básicas do servidor

```
INFO server
```

**Saída (só os campos que interessam, o INFO completo traz dezenas de linhas):**

```
redis_version:8.2.10
redis_mode:standalone
os:Linux 7.0.14-orbstack-00380-ga7e0a2dc9535 aarch64
arch_bits:64
process_id:1
tcp_port:6379
uptime_in_seconds:101
```

```
INFO memory
```

**Saída (só os campos que interessam, o INFO completo traz dezenas de linhas):**

```
used_memory:1645320
used_memory_human:1.57M
used_memory_peak_human:1.57M
maxmemory:0
maxmemory_human:0B
maxmemory_policy:noeviction
```

```
INFO keyspace
```

**Saída (só os campos que interessam, o INFO completo traz dezenas de linhas):**

```
# Keyspace
```

```
DBSIZE
```

**Saída:**

```
0
```

## SEÇÃO 2 – Acesso ao RedisInsight

O roteiro manda liberar a porta 5540 no VirtualBox. Com OrbStack ela já está publicada, é só abrir <http://localhost:5540>.

```bash
$ curl -s -o /dev/null -w 'RedisInsight responde: HTTP %{http_code}\n' http://localhost:5540
```

**Saída:**

```
RedisInsight responde: HTTP 200
```

> A URL é `redis://redis:6379` e não localhost. De dentro do contêiner do RedisInsight, localhost seria ele mesmo. O nome `redis` é o do serviço no compose.

O roteiro sugere navegar pela árvore de chaves e ver como os prefixos com : viram grupos. Dá para conferir isso a partir da Seção 5, quando já existem chaves como user:1001 e cache:pagina:/home.

## SEÇÃO 3 – Operações básicas com chaves

### 3.1 – Criando e consultando uma string

```
SET curso "NoSQL - Redis"
GET curso
TYPE curso
EXISTS curso
```

**Saída:**

```
OK
NoSQL - Redis
string
1
```

### 3.2 – Sobrescrevendo valor

```
SET curso "NoSQL - Redis Avançado"
GET curso
```

**Saída:**

```
OK
NoSQL - Redis Avançado
```

### 3.3 – Apagando chave

```
DEL curso
EXISTS curso
```

**Saída:**

```
1
0
```

### 3.4 – Inspeção de chaves

Criei algumas chaves antes:

```
MSET user:1 "a" user:2 "b" user:3 "c" outro:1 "x"
```

**Saída:**

```
OK
```

O roteiro diz para evitar em produção, porque o KEYS percorre o keyspace inteiro e bloqueia o servidor:

```
KEYS *
```

**Saída:**

```
user:2
user:1
outro:1
user:3
```

A alternativa é o SCAN, que é incremental e devolve um cursor:

```
SCAN 0 MATCH * COUNT 100
```

**Saída:**

```
0
user:2
outro:1
user:3
user:1
```

```
SCAN 0 MATCH user:* COUNT 100
```

**Saída:**

```
0
user:2
user:3
user:1
```

> O primeiro valor da resposta é o cursor. Voltou 0, então a varredura acabou numa passada só. Com muitas chaves ele viria diferente de zero e eu teria que chamar o SCAN de novo passando esse valor.

```
DEL user:1 user:2 user:3 outro:1
```

**Saída:**

```
4
```

### 3.5 – Descobrindo o tipo de uma chave

```
SET temp "abc"
TYPE temp
DEL temp
```

**Saída:**

```
OK
string
1
```

### 3.6 – Renomeando e movendo chaves

```
SET chave:original "valor"
RENAME chave:original chave:nova
GET chave:nova
```

**Saída:**

```
OK
OK
valor
```

O roteiro avisa que o RENAME falha se a chave original não existir. Conferindo:

```
RENAME chave:inexistente chave:qualquer
```

**Saída:**

```
ERR no such key

```

```
DEL chave:nova
```

**Saída:**

```
1
```

### 3.7 – Limpando o banco

Criei chaves para ver o efeito:

```
MSET a 1 b 2 c 3
DBSIZE
```

**Saída:**

```
OK
3
```

```
FLUSHDB
DBSIZE
```

**Saída:**

```
OK
0
```

> O FLUSHDB limpa só o banco atual. O FLUSHALL limpa os 16, por isso deixei comentado.

### 3.8 – Variantes de limpeza e seleção de banco

```
FLUSHDB ASYNC
```

**Saída:**

```
OK
```

> O ASYNC libera a memória em segundo plano, sem travar o servidor durante a limpeza.

O SELECT vale por conexão, então rodei os comandos abaixo na mesma sessão:

```
SELECT 1
SET apenas:no:db1 "valor"
DBSIZE
SELECT 0
DBSIZE
GET apenas:no:db1
```

**Saída (uma única conexão):**

```
OK
OK
1
OK
0

```

> A chave criada no banco 1 não aparece no banco 0. Os bancos são isolados, mas dividem o mesmo processo e a mesma memória, então o roteiro tem razão em dizer que em produção é melhor usar instâncias separadas.

```
SELECT 1
FLUSHDB
SELECT 0
```

**Saída (uma única conexão):**

```
OK
OK
OK
```

## SEÇÃO 4 – Expiração, TTL e cache

### 4.1 – TTL básico

```
SET cache:home "html-home"
TTL cache:home
```

**Saída:**

```
OK
-1
```

> O TTL tem três respostas: os segundos que faltam, -1 se a chave existe e não expira, e -2 se ela não existe. Confundir -1 com -2 dá problema em cache, porque uma coisa é estar guardado para sempre e outra é não estar guardado.

```
EXPIRE cache:home 30
TTL cache:home
```

**Saída:**

```
1
30
```

```
PERSIST cache:home
TTL cache:home
```

**Saída:**

```
1
-1
```

### 4.2 – Criando já com expiração

```
SET session:abc123 "payload" EX 60
GET session:abc123
TTL session:abc123
```

**Saída:**

```
OK
payload
60
```

### 4.3 – Comando SETEX

```
SETEX cache:pagina:/home 20 "<html>HOME</html>"
GET cache:pagina:/home
TTL cache:pagina:/home
```

**Saída:**

```
OK
<html>HOME</html>
20
```

> O SETEX faz o mesmo que SET com EX. Os dois são melhores que SET seguido de EXPIRE porque gravam o valor e o prazo juntos, sem deixar a chave um instante sem validade.

### 4.4 – Expirando em milissegundos

```
PSETEX cache:api:1 5000 "resultado-json"
PTTL cache:api:1
TTL cache:api:1
```

**Saída:**

```
OK
4966
5
```

### 4.5 – Invalidando cache manualmente

```
DEL cache:pagina:/home
EXISTS cache:pagina:/home
```

**Saída:**

```
1
0
```

### Exercício 1

1) Criar `cache:produto:10` com TTL de 120 s · 2) consultar o conteúdo · 3) consultar o TTL · 4) remover manualmente.

```
SET cache:produto:10 "{\"id\":10,\"nome\":\"Teclado\",\"preco\":250.00}" EX 120
GET cache:produto:10
TTL cache:produto:10
DEL cache:produto:10
EXISTS cache:produto:10
TTL cache:produto:10
```

**Saída:**

```
OK
{"id":10,"nome":"Teclado","preco":250.00}
120
1
0
-2
```

## SEÇÃO 5 – Strings

### 5.1 – Operações básicas

```
SET user:1001 "João"
GET user:1001
APPEND user:1001 " Silva"
GET user:1001
STRLEN user:1001
```

**Saída:**

```
OK
João
11
João Silva
11
```

> O STRLEN deu 11 e não 10 porque ele conta bytes, não caracteres. O ã ocupa 2 bytes em UTF-8. O APPEND devolve o mesmo número.

### 5.2 – Múltiplas chaves

```
MSET user:2001 "Ana" user:2002 "Bruno" user:2003 "Carlos"
MGET user:2001 user:2002 user:2003
```

**Saída:**

```
OK
Ana
Bruno
Carlos
```

> MSET e MGET resolvem tudo numa ida só ao servidor. O ganho é o mesmo do insertMany do MongoDB: economizar viagem de rede.

### 5.3 – Contadores

```
SET visitas 0
INCR visitas
INCRBY visitas 10
DECR visitas
DECRBY visitas 2
GET visitas
```

**Saída:**

```
OK
1
11
10
8
8
```

> O INCR é atômico. Se eu fizesse GET, somasse na aplicação e desse SET, dois clientes simultâneos poderiam ler o mesmo valor e um sobrescreveria a contagem do outro.

### 5.4 – Incremento em valor monetário ou decimal

```
SET saldo 10.5
INCRBYFLOAT saldo 2.75
GET saldo
```

**Saída:**

```
OK
13.25
13.25
```

> O INCRBYFLOAT usa ponto flutuante. Para dinheiro prefiro guardar centavos em inteiro e usar INCRBY, para não pegar erro de arredondamento.

### 5.5 – Recuperação parcial de string

```
SET codigo "ABCDEFGH123456"
GETRANGE codigo 0 3
GETRANGE codigo 4 7
GETRANGE codigo -6 -1
```

**Saída:**

```
OK
ABCD
EFGH
123456
```

### Exercício 2

1) Criar `contador:login` com 0 · 2) incrementar 5 vezes · 3) incrementar mais 10 de uma vez · 4) TTL de 60 s · 5) consultar valor e TTL.

```
SET contador:login 0
INCR contador:login
INCR contador:login
INCR contador:login
INCR contador:login
INCR contador:login
INCRBY contador:login 10
EXPIRE contador:login 60
GET contador:login
TTL contador:login
```

**Saída:**

```
OK
1
2
3
4
5
15
1
15
60
```

> Deu 15, que são os cinco INCR mais o INCRBY 10, e o TTL ficou em 60. Testando aqui, o INCR não renova o TTL: a chave continua expirando no prazo que foi definido, por mais que eu incremente.

## SEÇÃO 6 – Sets

### 6.1 – Inserção e consulta

```
SADD curso:BI "Ana" "Bruno" "Carlos"
SMEMBERS curso:BI
SCARD curso:BI
SISMEMBER curso:BI "Ana"
SISMEMBER curso:BI "Fernanda"
```

**Saída:**

```
3
Ana
Bruno
Carlos
3
1
0
```

Inserindo um membro que já está no conjunto:

```
SADD curso:BI "Ana"
```

**Saída:**

```
0
```

> Devolveu 0 porque a Ana já estava no conjunto. O SADD informa quantos entraram de fato, então dá para usar o retorno para saber se um valor é repetido.

### 6.2 – Remoção

```
SREM curso:BI "Bruno"
SMEMBERS curso:BI
```

**Saída:**

```
1
Ana
Carlos
```

### 6.3 – Criando outro conjunto

```
SADD curso:DS "Ana" "Fernanda" "Marcos"
SMEMBERS curso:DS
```

**Saída:**

```
3
Ana
Fernanda
Marcos
```

### 6.4 – Operações de conjuntos

```
SINTER curso:BI curso:DS
SUNION curso:BI curso:DS
SDIFF curso:DS curso:BI
SDIFF curso:BI curso:DS
```

**Saída:**

```
Ana
Fernanda
Carlos
Ana
Marcos
Fernanda
Marcos
Carlos
```

> O SDIFF não é comutativo. SDIFF A B traz o que está em A e não está em B, e invertendo a ordem o resultado muda, como aparece nas duas últimas saídas.

### 6.5 – Sorteio/remoção aleatória

```
SADD equipe:sorteio "A" "B" "C" "D"
SRANDMEMBER equipe:sorteio
SPOP equipe:sorteio
SMEMBERS equipe:sorteio
```

**Saída:**

```
4
D
D
A
B
C
```

> O SRANDMEMBER só lê, o SPOP lê e remove. Para sorteio sem repetir, é o SPOP.

### Exercício 3

Criar `interesses:python` e `interesses:redis` com nomes repetidos entre eles e mostrar interseção, união e diferença.

```
SADD interesses:python "Ana" "Bruno" "Carlos" "Diana"
SADD interesses:redis "Bruno" "Carlos" "Eduardo"
SINTER interesses:python interesses:redis
SUNION interesses:python interesses:redis
SDIFF interesses:python interesses:redis
SCARD interesses:python
SCARD interesses:redis
```

**Saída:**

```
4
3
Bruno
Carlos
Diana
Eduardo
Ana
Bruno
Carlos
Diana
Ana
4
3
```

> Interseção: Bruno e Carlos, que estão nos dois conjuntos. União: 5 nomes, mesmo eu tendo inserido 7 vezes, porque o set não repete. Diferença de python para redis: Ana e Diana.

## SEÇÃO 7 – Sorted Sets (ranking)

### 7.1 – Criando ranking

```
ZADD ranking:pontos 100 "joao" 150 "maria" 90 "carlos"
ZRANGE ranking:pontos 0 -1 WITHSCORES
ZREVRANGE ranking:pontos 0 -1 WITHSCORES
```

**Saída:**

```
3
carlos
90
joao
100
maria
150
maria
150
joao
100
carlos
90
```

> O ZRANGE vai do menor score para o maior e o ZREVRANGE inverte. Para ranking uso o ZREVRANGE, porque quem tem mais ponto tem que vir primeiro.

### 7.2 – Incrementando pontuação

```
ZINCRBY ranking:pontos 25 "carlos"
ZREVRANGE ranking:pontos 0 -1 WITHSCORES
```

**Saída:**

```
115
maria
150
carlos
115
joao
100
```

### 7.3 – Descobrindo posição

```
ZRANK ranking:pontos "carlos"
ZREVRANK ranking:pontos "carlos"
```

**Saída:**

```
1
1
```

> As posições começam em zero. O ZRANK conta a partir do menor score e o ZREVRANK a partir do maior, que é o que corresponde à colocação.

### 7.4 – Consultando score

```
ZSCORE ranking:pontos "maria"
ZCARD ranking:pontos
```

**Saída:**

```
150
3
```

### 7.5 – Top N

```
ZREVRANGE ranking:pontos 0 1 WITHSCORES
```

**Saída:**

```
maria
150
carlos
115
```

### 7.6 – Removendo participante

```
ZREM ranking:pontos "joao"
ZREVRANGE ranking:pontos 0 -1 WITHSCORES
```

**Saída:**

```
1
maria
150
carlos
115
```

### Exercício 4

1) Criar `ranking:turma` com 5 alunos · 2) incrementar a nota de dois · 3) mostrar o Top 3 · 4) mostrar a posição de um aluno.

```
ZADD ranking:turma 7.5 "Ana" 8.0 "Bruno" 6.5 "Carlos" 9.0 "Diana" 5.5 "Eduardo"
ZREVRANGE ranking:turma 0 -1 WITHSCORES
ZINCRBY ranking:turma 1.5 "Carlos"
ZINCRBY ranking:turma 0.5 "Eduardo"
ZREVRANGE ranking:turma 0 2 WITHSCORES
ZREVRANK ranking:turma "Carlos"
ZSCORE ranking:turma "Carlos"
```

**Saída:**

```
5
Diana
9
Bruno
8
Ana
7.5
Carlos
6.5
Eduardo
5.5
8
6
Diana
9
Carlos
8
Bruno
8
1
8
```

> Carlos foi para 8,0 e empatou com Bruno. No empate o Redis ordena pelo nome do membro, mas como o ZREVRANGE percorre ao contrário o empate também sai invertido, e o Carlos aparece antes do Bruno. Testei separado com Ana, Bruno e Carlos todos com 8: no ZRANGE saiu Ana, Bruno, Carlos e no ZREVRANGE saiu Carlos, Bruno, Ana. O ZREVRANK devolveu 1, que é segundo lugar.

## SEÇÃO 8 – Lists

### 8.1 – Inserção no início e no fim

```
LPUSH fila:processamento "job1"
LPUSH fila:processamento "job2"
RPUSH fila:processamento "job3"
LRANGE fila:processamento 0 -1
```

**Saída:**

```
1
2
3
job2
job1
job3
```

> O LPUSH insere no início e o RPUSH no fim. O job1 entrou primeiro pela esquerda e o job2 depois, por isso a ordem ficou job2, job1, job3.

### 8.2 – Consumo FIFO

```
RPOP fila:processamento
LRANGE fila:processamento 0 -1
```

**Saída:**

```
job3
job2
job1
```

> LPUSH com RPOP é FIFO: entra de um lado e sai do outro, então sai primeiro quem chegou primeiro.

### 8.3 – Consumo LIFO

```
LPOP fila:processamento
LRANGE fila:processamento 0 -1
```

**Saída:**

```
job2
job1
```

> LPUSH com LPOP é pilha: entra e sai pelo mesmo lado.

### 8.4 – Tamanho da lista

```
LLEN fila:processamento
```

**Saída:**

```
1
```

### 8.5 – Leitura por intervalo

```
RPUSH fila:pedidos "p1" "p2" "p3" "p4"
LRANGE fila:pedidos 0 -1
LRANGE fila:pedidos 0 1
LRANGE fila:pedidos -2 -1
```

**Saída:**

```
4
p1
p2
p3
p4
p1
p2
p3
p4
```

### Exercício 5

1) Criar 5 jobs em `fila:etl` · 2) listar · 3) consumir dois com `RPOP`.

```
RPUSH fila:etl "job:extrair" "job:transformar" "job:validar" "job:carregar" "job:notificar"
LLEN fila:etl
LRANGE fila:etl 0 -1
RPOP fila:etl
RPOP fila:etl
LRANGE fila:etl 0 -1
LLEN fila:etl
```

**Saída:**

```
5
5
job:extrair
job:transformar
job:validar
job:carregar
job:notificar
job:notificar
job:carregar
job:extrair
job:transformar
job:validar
3
```

> Saíram o job:notificar e o job:carregar, que eram os dois últimos. Entrei com RPUSH e consumi com RPOP, as duas pontas iguais, então virou pilha e não fila. Para ficar FIFO com RPUSH eu teria que consumir com LPOP.

## SEÇÃO 9 – Hashes

### 9.1 – Criando documento

```
HSET aluno:1 nome "Carlos Silva" idade 22 curso "Engenharia de Dados"
HGET aluno:1 nome
HGETALL aluno:1
HKEYS aluno:1
HVALS aluno:1
HLEN aluno:1
```

**Saída:**

```
3
Carlos Silva
nome
Carlos Silva
idade
22
curso
Engenharia de Dados
nome
idade
curso
Carlos Silva
22
Engenharia de Dados
3
```

> O hash guarda a entidade sem precisar serializar JSON, e dá para ler e escrever um campo de cada vez. Com JSON numa string eu teria que ler tudo, alterar na aplicação e gravar de volta.

### 9.2 – Consulta parcial de vários campos

```
HMGET aluno:1 nome curso
```

**Saída:**

```
Carlos Silva
Engenharia de Dados
```

### 9.3 – Atualização de um campo específico

```
HSET aluno:1 cidade "Brasília"
HGETALL aluno:1
```

**Saída:**

```
1
nome
Carlos Silva
idade
22
curso
Engenharia de Dados
cidade
Brasília
```

### 9.4 – Incremento numérico dentro do hash

```
HINCRBY aluno:1 idade 1
HGET aluno:1 idade
```

**Saída:**

```
23
23
```

> O HINCRBY incrementa o campo direto no servidor, mesmo os valores do hash sendo strings.

### 9.5 – Verificando existência de campo

```
HEXISTS aluno:1 cidade
HEXISTS aluno:1 email
```

**Saída:**

```
1
0
```

### 9.6 – Removendo campo

```
HDEL aluno:1 cidade
HGETALL aluno:1
```

**Saída:**

```
1
nome
Carlos Silva
idade
23
curso
Engenharia de Dados
```

> Quando apago o último campo, a chave some junto. No Redis não existe hash vazio.

### Exercício 6

1) Criar `aluno:2` e `aluno:3` · 2) consultar só o campo curso de cada um · 3) incrementar a idade de `aluno:2` · 4) listar todos os campos de `aluno:3`.

```
HSET aluno:2 nome "Ana Ribeiro" idade 20 curso "Ciência de Dados"
HSET aluno:3 nome "Bruno Tavares" idade 25 curso "Engenharia de Software"
HGET aluno:2 curso
HGET aluno:3 curso
HINCRBY aluno:2 idade 1
HGET aluno:2 idade
HGETALL aluno:3
```

**Saída:**

```
3
3
Ciência de Dados
Engenharia de Software
21
21
nome
Bruno Tavares
idade
25
curso
Engenharia de Software
```

## SEÇÃO 10 – Padrões de aplicação

### 10.1 – Cache com TTL

```
SETEX cache:consulta:clientes 30 "{resultado_json}"
GET cache:consulta:clientes
TTL cache:consulta:clientes
```

**Saída:**

```
OK
{resultado_json}
30
```

### 10.2 – Sessão de usuário

```
SET session:user:1001 "{token:'abc',perfil:'admin'}" EX 300
GET session:user:1001
TTL session:user:1001
```

**Saída:**

```
OK
{token:'abc',perfil:'admin'}
300
```

### 10.3 – Rate limit simples

```
INCR rl:user:42
EXPIRE rl:user:42 60
GET rl:user:42
TTL rl:user:42
```

**Saída:**

```
1
1
1
60
```

Mais requisições do mesmo usuário dentro da janela:

```
INCR rl:user:42
INCR rl:user:42
INCR rl:user:42
INCR rl:user:42
INCR rl:user:42
GET rl:user:42
TTL rl:user:42
```

**Saída:**

```
2
3
4
5
6
6
60
```

> A regra do roteiro é bloquear acima de 5. O TTL não foi renovado pelos INCR seguintes, então a janela conta a partir do primeiro acesso. Reparei que entre o INCR e o EXPIRE existe um instante em que a chave está sem prazo: se o processo morrer ali, o contador nunca expira e o usuário fica bloqueado para sempre.

### 10.4 – Fila simples

```
LPUSH fila:emails "email1"
LPUSH fila:emails "email2"
LRANGE fila:emails 0 -1
RPOP fila:emails
```

**Saída:**

```
1
2
email2
email1
email1
```

### 10.5 – Ranking

```
ZADD ranking:jogo 500 "ana" 900 "bruno" 700 "carla"
ZREVRANGE ranking:jogo 0 -1 WITHSCORES
```

**Saída:**

```
3
bruno
900
carla
700
ana
500
```

### Exercício 7

Cenário completo: cache de página, contador de visitas, sessão temporária e ranking com 3 jogadores.

```
SETEX cache:pagina:/produtos 60 "<html><body>Lista de produtos</body></html>"
SET visitas:pagina:/produtos 0
INCR visitas:pagina:/produtos
INCR visitas:pagina:/produtos
INCR visitas:pagina:/produtos
SET session:user:2002 "{token:def456,perfil:cliente}" EX 180
ZADD ranking:torneio 1200 "ana" 1450 "bruno" 980 "carla"
GET cache:pagina:/produtos
TTL cache:pagina:/produtos
GET visitas:pagina:/produtos
TTL session:user:2002
ZREVRANGE ranking:torneio 0 -1 WITHSCORES
```

**Saída:**

```
OK
OK
1
2
3
OK
3
<html><body>Lista de produtos</body></html>
60
3
180
bruno
1450
ana
1200
carla
980
```

> Usei string com TTL no cache e na sessão, string com INCR no contador e sorted set no ranking. Deixei o contador de visitas sem TTL de propósito, senão ele zeraria junto com o cache da página.

## SEÇÃO 11 – Pub/Sub

O roteiro pede dois terminais. Deixei o assinante rodando em segundo plano, gravando num arquivo, e publiquei em seguida por outra conexão.

### 11.1 – Publicação e inscrição

**Terminal 1, assinante:**

```
SUBSCRIBE canal:noticias
```

**Terminal 2, publicador:**

```
PUBLISH canal:noticias "Mensagem 1"
1
PUBLISH canal:noticias "Mensagem 2"
1
```

**O que o assinante recebeu:**

```
subscribe
canal:noticias
1
message
canal:noticias
Mensagem 1
message
canal:noticias
Mensagem 2
```

> O PUBLISH devolve quantos assinantes receberam, 1 nos dois casos. Sem ninguém inscrito ele devolveria 0 e a mensagem se perderia, porque o Pub/Sub não guarda nada.

### 11.2 – Pattern subscribe

**Terminal 1, assinante por padrão:**

```
PSUBSCRIBE canal:*
```

**Terminal 2, publicador:**

```
PUBLISH canal:noticias "Nova noticia"
2
PUBLISH canal:alertas "Alerta importante"
1
PUBLISH outro:canal "Nao deve chegar"
0
```

**O que o assinante recebeu:**

```
psubscribe
canal:*
1
pmessage
canal:*
canal:noticias
Nova noticia
pmessage
canal:*
canal:alertas
Alerta importante
```

> As duas primeiras casaram com canal:* e chegaram. A terceira foi para outro:canal, devolveu 0 assinantes e não chegou.

### Exercício 8

1) Criar `canal:alertas` · 2) inscrever um terminal · 3) publicar 3 mensagens de outro terminal.

**Publicador (3 mensagens, cada uma devolvendo o nº de assinantes):**

```
PUBLISH canal:alertas "Alerta 1: CPU acima de 90%"
2
PUBLISH canal:alertas "Alerta 2: disco em 85%"
2
PUBLISH canal:alertas "Alerta 3: servico reiniciado"
2
```

**Assinante:**

```
subscribe
canal:alertas
1
message
canal:alertas
Alerta 1: CPU acima de 90%
message
canal:alertas
Alerta 2: disco em 85%
message
canal:alertas
Alerta 3: servico reiniciado
```

---

Fim da Parte 1. As chaves continuam no banco e são usadas na Parte 2, a limpeza fica na Seção 23.

```bash
$ docker exec redis redis-cli DBSIZE
```

**Saída:**

```
32
```
