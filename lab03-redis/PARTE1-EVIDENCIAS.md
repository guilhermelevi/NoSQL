# Lab 3 – Redis – Parte 1 – Evidências de execução

Executado em 27/09/2026 17:30 · Redis 8.2.10 · macOS/OrbStack

Cobre as Seções 1 a 11 e os Exercícios 1 a 8. Todo comando foi executado no container `redis`; as saídas são reais.

## SEÇÃO 1 – Preparação do ambiente

No roteiro original o ambiente é copiado para a VM com `scp -P 2229` e os comandos usam `sudo`. No macOS com OrbStack nada disso é necessário: o `docker-compose.yml` fica no próprio projeto e as portas já ficam acessíveis em `localhost`.

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

O roteiro oferece duas formas: entrar no container ou instalar o `redis-tools` no host. Aqui usamos a primeira, que dispensa instalar qualquer coisa:

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

**Saída (campos relevantes — o INFO completo traz dezenas de linhas):**

```
redis_version:8.2.10
redis_mode:standalone
os:Linux 7.0.14-orbstack-00380-ga7e0a2dc9535 aarch64
arch_bits:64
process_id:1
tcp_port:6379
uptime_in_seconds:55
```

```
INFO memory
```

**Saída (campos relevantes — o INFO completo traz dezenas de linhas):**

```
used_memory:1595944
used_memory_human:1.52M
used_memory_peak_human:1.52M
maxmemory:0
maxmemory_human:0B
maxmemory_policy:noeviction
```

```
INFO keyspace
```

**Saída (campos relevantes — o INFO completo traz dezenas de linhas):**

```
# Keyspace
```

> O `INFO keyspace` não lista nenhum banco quando não há chaves — bancos vazios simplesmente não aparecem.

```
DBSIZE
```

**Saída:**

```
0
```

## SEÇÃO 2 – Acesso ao RedisInsight

O roteiro pede para liberar a porta 5540 no VirtualBox. Com OrbStack a porta já está publicada — basta abrir <http://localhost:5540>.

```bash
$ curl -s -o /dev/null -w 'RedisInsight responde: HTTP %{http_code}\n' http://localhost:5540
```

**Saída:**

```
RedisInsight responde: HTTP 200
```

> Na tela **Connect existing database**, a URL de conexão é `redis://redis:6379` — `redis` é o nome do serviço na rede do Compose, que o RedisInsight resolve por DNS interno. De dentro do RedisInsight, `localhost` apontaria para o próprio contêiner dele, não para o Redis.

Sugestão didática do roteiro: navegar pela árvore de chaves e observar como prefixos com `:` viram grupos lógicos. Isso fica visível depois da Seção 5, quando existirem chaves como `user:1001` e `cache:pagina:/home`.

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

> O `SET` sobrescreve sem avisar e sem erro, independentemente do tipo anterior da chave.

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

> `DEL` devolve quantas chaves foram removidas; `EXISTS` devolve 0 quando a chave não existe mais.

### 3.4 – Inspeção de chaves

Preparando algumas chaves para a demonstração:

```
MSET user:1 "a" user:2 "b" user:3 "c" outro:1 "x"
```

**Saída:**

```
OK
```

**Evitar em produção** — `KEYS` percorre todo o keyspace e bloqueia o servidor durante a varredura:

```
KEYS *
```

**Saída:**

```
outro:1
user:3
user:2
user:1
```

**Preferir** — `SCAN` é incremental e devolve um cursor:

```
SCAN 0 MATCH * COUNT 100
```

**Saída:**

```
0
outro:1
user:3
user:2
user:1
```

```
SCAN 0 MATCH user:* COUNT 100
```

**Saída:**

```
0
user:3
user:2
user:1
```

> O primeiro valor da resposta é o cursor. Quando volta `0`, a varredura terminou. Com muitas chaves o cursor vem diferente de zero e é preciso chamar o `SCAN` de novo passando esse valor — é justamente isso que torna o comando incremental e não bloqueante.

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

O roteiro observa que o `RENAME` falha se a chave original não existir. Confirmando:

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

Criando chaves para comprovar o efeito:

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

> `FLUSHDB` apaga apenas o banco atual. `FLUSHALL` apaga todos os 16 bancos — é destrutivo e o roteiro corretamente o deixa comentado.

### 3.8 – Variantes de limpeza e seleção de banco

```
FLUSHDB ASYNC
```

**Saída:**

```
OK
```

> `ASYNC` libera a memória numa thread em segundo plano, sem bloquear o servidor. Em bancos com milhões de chaves a diferença entre bloquear e não bloquear é o que decide se a aplicação sofre timeout durante a limpeza.

O `SELECT` vale **por conexão**, então os comandos abaixo precisam rodar na mesma sessão:

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

> No banco 1 o `DBSIZE` é 1; de volta ao banco 0 é 0, e a chave criada no banco 1 não é visível — `GET` devolve vazio. Os bancos são espaços de nomes isolados dentro da mesma instância. O roteiro alerta: em produção prefira instâncias separadas, porque os bancos numerados compartilham CPU, memória e o mesmo processo de persistência.

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

> `TTL` devolve **-1** quando a chave existe mas não tem expiração, e **-2** quando a chave não existe. São respostas diferentes para situações diferentes — confundi-las é fonte comum de bug em camada de cache.

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

> O `PERSIST` removeu a expiração e o TTL voltou a -1: a chave virou permanente.

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

> `SETEX` é equivalente a `SET ... EX`. A vantagem de qualquer um dos dois sobre `SET` seguido de `EXPIRE` é a atomicidade: não existe instante em que a chave esteja gravada sem prazo de validade.

### 4.4 – Expirando em milissegundos

```
PSETEX cache:api:1 5000 "resultado-json"
PTTL cache:api:1
TTL cache:api:1
```

**Saída:**

```
OK
4969
5
```

> `PTTL` responde em milissegundos e `TTL` em segundos (arredondado para cima).

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

> Depois do `DEL`, o `TTL` passa a devolver -2 (chave inexistente), e não -1.

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

> Atenção ao `STRLEN`: ele conta **bytes**, não caracteres. "João Silva" tem 10 caracteres, mas o `ã` ocupa 2 bytes em UTF-8, então o resultado é 11. O `APPEND` devolve o novo comprimento, também em bytes.

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

> `MSET`/`MGET` resolvem várias chaves numa única ida ao servidor. O ganho não está no Redis processar mais rápido, está em eliminar o custo de rede por chave — o mesmo raciocínio do `_bulk` do Elasticsearch e do `insertMany` do MongoDB.

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

> Cada operação é atômica: mil clientes incrementando ao mesmo tempo não perdem contagem. É a razão de existir o `INCR` em vez de `GET`, somar na aplicação e `SET` — esse trio produz condição de corrida.

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

> `INCRBYFLOAT` usa ponto flutuante. Para dinheiro, a prática segura é guardar centavos como inteiro e usar `INCRBY`, evitando erro de arredondamento binário.

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

> Os índices são inclusivos nas duas pontas e aceitam valores negativos contando do fim.

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

> Valor final 15 — cinco `INCR` mais um `INCRBY 10`. Detalhe importante: o `INCR` **não** renova o TTL. Uma chave de contador com expiração continua expirando no prazo original por mais que seja incrementada, e é exatamente disso que depende o rate limit da Seção 10.3.

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

Tentando inserir um membro que já existe:

```
SADD curso:BI "Ana"
```

**Saída:**

```
0
```

> Devolve 0: nenhum elemento novo foi adicionado. O `SADD` informa quantos membros realmente entraram, o que permite usar o set como teste de unicidade — por exemplo, para saber se um voto ou um clique já foi computado.

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
Ana
Fernanda
Carlos
Marcos
Fernanda
Marcos
Carlos
```

> `SDIFF` não é comutativo: `SDIFF A B` devolve o que está em A e não em B. Trocar a ordem dos argumentos muda o resultado, como as duas últimas saídas mostram.

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
C
D
A
B
C
```

> `SRANDMEMBER` apenas lê; `SPOP` lê **e remove**. Para um sorteio sem repetição, `SPOP` é o comando correto — é a diferença entre espiar uma carta e tirá-la do baralho.

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
Ana
Diana
Eduardo
Bruno
Carlos
Ana
Diana
4
3
```

> Interseção = quem tem os dois interesses (Bruno e Carlos). União = 5 pessoas distintas, apesar de 7 inserções — a unicidade do set eliminou as duplicatas. Diferença = só Python.

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

> `ZRANGE` ordena do menor para o maior score; `ZREVRANGE` inverte. Para ranking o natural é o `ZREVRANGE`, porque quem tem mais pontos deve aparecer primeiro.

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

> Carlos saiu de 90 para 115 e ultrapassou João (100) — a reordenação é automática. O sorted set mantém a ordem a cada escrita, sem que ninguém precise reordenar nada.

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

> As posições são baseadas em zero. `ZRANK` conta do menor score; `ZREVRANK` do maior — este é o que corresponde à colocação no ranking.

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

> Top 2. O intervalo `0 1` é inclusivo nas duas pontas, então devolve dois elementos, não um.

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

> Carlos subiu de 6,5 para 8,0 e empatou com Bruno. Em caso de empate o Redis ordena pelo **membro**, em ordem lexicográfica — mas como o `ZREVRANGE` percorre a estrutura ao contrário, o empate também sai invertido e "Carlos" aparece antes de "Bruno". Verificado à parte: com Ana, Bruno e Carlos todos com score 8, `ZRANGE` devolve Ana → Bruno → Carlos e `ZREVRANGE` devolve Carlos → Bruno → Ana. O `ZREVRANK` devolve a colocação começando em zero, então o 1 aqui significa **segundo lugar**.

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

> `LPUSH` insere à esquerda (início) e `RPUSH` à direita (fim). Como job1 entrou primeiro pela esquerda e job2 depois, a ordem final é job2, job1, job3.

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

> `LPUSH` + `RPOP` = FIFO: entra pela esquerda, sai pela direita, e quem chegou primeiro sai primeiro.

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

> `LPUSH` + `LPOP` = LIFO (pilha): entra e sai pelo mesmo lado.

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

> Índices negativos contam do fim: `-1` é o último elemento e `-2 -1` devolve os dois últimos. `LRANGE` apenas lê, não remove.

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

> Como os jobs entraram com `RPUSH` (pela direita) e saem com `RPOP` (também pela direita), o consumo é LIFO: saíram os dois **últimos** da fila. Para FIFO com `RPUSH`, o consumo correto é `LPOP`. Essa inversão é o erro mais comum com listas no Redis.

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

> O hash representa uma entidade sem precisar serializar JSON: cada campo é lido e escrito isoladamente. Com uma string JSON, atualizar a idade exigiria ler o documento inteiro, alterar na aplicação e regravar — três operações e uma janela de condição de corrida.

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

> O `HSET` devolve 1 quando o campo é novo e 0 quando apenas atualiza um campo existente.

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

> Os valores de um hash são sempre strings, mas o `HINCRBY` interpreta como inteiro e incrementa atomicamente — sem ler-somar-gravar na aplicação.

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

> Removendo o último campo de um hash, a chave inteira deixa de existir — no Redis não há coleção vazia.

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

> A sessão expirar sozinha é o ponto: não existe rotina de limpeza, nem job noturno varrendo sessões mortas. O Redis remove a chave no vencimento.

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

Simulando mais requisições do mesmo usuário dentro da janela:

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

> Regra didática do roteiro: acima de 5, bloquear. Repare que o TTL **não** foi renovado pelos `INCR` seguintes — a janela continua contando a partir do primeiro acesso, que é o comportamento desejado. Há porém uma falha de concorrência aqui: entre o `INCR` e o `EXPIRE` existe um instante em que a chave não tem prazo, e se o processo morrer nesse intervalo o contador fica eterno e bloqueia o usuário para sempre. A Seção 18 (script Lua) resolve exatamente isso.

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

> Aqui a combinação está correta: `LPUSH` + `RPOP` é FIFO, então saiu o email1, que foi o primeiro a entrar.

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

> Quatro estruturas para quatro necessidades: string com TTL para o cache, string com `INCR` para o contador, string com TTL para a sessão e sorted set para o ranking. Repare que o contador de visitas **não** tem TTL — ele precisa sobreviver à expiração do cache da página.

## SEÇÃO 11 – Pub/Sub

O roteiro pede dois terminais. Aqui o assinante foi posto em segundo plano, gravando num arquivo, e a publicação feita em seguida por outra conexão.

### 11.1 – Publicação e inscrição

**Terminal 1 — assinante:**

```
SUBSCRIBE canal:noticias
```

**Terminal 2 — publicador:**

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

> O `PUBLISH` devolve **quantos assinantes receberam** a mensagem — 1 nos dois casos. Se ninguém estivesse inscrito, devolveria 0 e a mensagem seria descartada: o Pub/Sub não guarda nada. Essa é a diferença central para as Streams da Seção 12.

### 11.2 – Pattern subscribe

**Terminal 1 — assinante por padrão:**

```
PSUBSCRIBE canal:*
```

**Terminal 2 — publicador:**

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

> As duas primeiras mensagens casaram com o padrão `canal:*` e chegaram. A terceira, publicada em `outro:canal`, devolveu **0 assinantes** e não foi entregue — comprovando que o padrão filtra de verdade.

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

Fim da Parte 1. As chaves criadas aqui permanecem no banco e são usadas pela Parte 2; a limpeza está na Seção 23.

```bash
$ docker exec redis redis-cli DBSIZE
```

**Saída:**

```
32
```
