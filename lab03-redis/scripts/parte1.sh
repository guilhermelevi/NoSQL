#!/bin/bash
# Lab 3 - Redis - Parte 1 (Secoes 1 a 11 + Exercicios 1 a 8)
# uso: ./parte1.sh ../PARTE1-EVIDENCIAS.md
set -u
cd "$(dirname "$0")"
export OUT="${1:-../PARTE1-EVIDENCIAS.md}"
: > "$OUT"
source ./lib.sh

echo "# Lab 3 – Redis – Parte 1 – Evidências de execução" >> "$OUT"
txt "Executado em $(date '+%d/%m/%Y %H:%M') · Redis $(echo 'INFO server' | $R | grep redis_version | tr -d '\r' | cut -d: -f2) · macOS/OrbStack"
txt "Cobre as Seções 1 a 11 e os Exercícios 1 a 8. Todo comando foi executado no container \`redis\`; as saídas são reais."

# ===================== SECAO 1 =====================
sec "SEÇÃO 1 – Preparação do ambiente"
txt "No roteiro original o ambiente é copiado para a VM com \`scp -P 2229\` e os comandos usam \`sudo\`. No macOS com OrbStack nada disso é necessário: o \`docker-compose.yml\` fica no próprio projeto e as portas já ficam acessíveis em \`localhost\`."

sub "1.2 – Subir o ambiente"
shell "docker compose -f ../docker-compose.yml ps --format 'table {{.Name}}\t{{.State}}\t{{.Ports}}'"

sub "1.3 e 1.4 – Acessar o redis-cli e testar a conexão"
txt "O roteiro oferece duas formas: entrar no container ou instalar o \`redis-tools\` no host. Aqui usamos a primeira, que dispensa instalar qualquer coisa:"
cmd "PING"

sub "1.5 – Informações básicas do servidor"
info "server" "redis_version|redis_mode|os:|arch_bits|process_id|tcp_port|uptime_in_seconds"
info "memory" "used_memory:|used_memory_human|used_memory_peak_human|maxmemory:|maxmemory_human|maxmemory_policy"
info "keyspace" "^#|^db"
nota "O \`INFO keyspace\` não lista nenhum banco quando não há chaves — bancos vazios simplesmente não aparecem."
cmd "DBSIZE"

# ===================== SECAO 2 =====================
sec "SEÇÃO 2 – Acesso ao RedisInsight"
txt "O roteiro pede para liberar a porta 5540 no VirtualBox. Com OrbStack a porta já está publicada — basta abrir <http://localhost:5540>."
shell "curl -s -o /dev/null -w 'RedisInsight responde: HTTP %{http_code}\\n' http://localhost:5540"
nota "Na tela **Connect existing database**, a URL de conexão é \`redis://redis:6379\` — \`redis\` é o nome do serviço na rede do Compose, que o RedisInsight resolve por DNS interno. De dentro do RedisInsight, \`localhost\` apontaria para o próprio contêiner dele, não para o Redis."
txt "Sugestão didática do roteiro: navegar pela árvore de chaves e observar como prefixos com \`:\` viram grupos lógicos. Isso fica visível depois da Seção 5, quando existirem chaves como \`user:1001\` e \`cache:pagina:/home\`."

# ===================== SECAO 3 =====================
sec "SEÇÃO 3 – Operações básicas com chaves"

sub "3.1 – Criando e consultando uma string"
cmds 'SET curso "NoSQL - Redis"' 'GET curso' 'TYPE curso' 'EXISTS curso'

sub "3.2 – Sobrescrevendo valor"
cmds 'SET curso "NoSQL - Redis Avançado"' 'GET curso'
nota "O \`SET\` sobrescreve sem avisar e sem erro, independentemente do tipo anterior da chave."

sub "3.3 – Apagando chave"
cmds 'DEL curso' 'EXISTS curso'
nota "\`DEL\` devolve quantas chaves foram removidas; \`EXISTS\` devolve 0 quando a chave não existe mais."

sub "3.4 – Inspeção de chaves"
txt "Preparando algumas chaves para a demonstração:"
cmds 'MSET user:1 "a" user:2 "b" user:3 "c" outro:1 "x"'
txt "**Evitar em produção** — \`KEYS\` percorre todo o keyspace e bloqueia o servidor durante a varredura:"
cmd "KEYS *"
txt "**Preferir** — \`SCAN\` é incremental e devolve um cursor:"
cmd "SCAN 0 MATCH * COUNT 100"
cmd "SCAN 0 MATCH user:* COUNT 100"
nota "O primeiro valor da resposta é o cursor. Quando volta \`0\`, a varredura terminou. Com muitas chaves o cursor vem diferente de zero e é preciso chamar o \`SCAN\` de novo passando esse valor — é justamente isso que torna o comando incremental e não bloqueante."
cmds 'DEL user:1 user:2 user:3 outro:1'

sub "3.5 – Descobrindo o tipo de uma chave"
cmds 'SET temp "abc"' 'TYPE temp' 'DEL temp'

sub "3.6 – Renomeando e movendo chaves"
cmds 'SET chave:original "valor"' 'RENAME chave:original chave:nova' 'GET chave:nova'
txt "O roteiro observa que o \`RENAME\` falha se a chave original não existir. Confirmando:"
cmd "RENAME chave:inexistente chave:qualquer"
cmds 'DEL chave:nova'

sub "3.7 – Limpando o banco"
txt "Criando chaves para comprovar o efeito:"
cmds 'MSET a 1 b 2 c 3' 'DBSIZE'
cmds 'FLUSHDB' 'DBSIZE'
nota "\`FLUSHDB\` apaga apenas o banco atual. \`FLUSHALL\` apaga todos os 16 bancos — é destrutivo e o roteiro corretamente o deixa comentado."

sub "3.8 – Variantes de limpeza e seleção de banco"
cmd "FLUSHDB ASYNC"
nota "\`ASYNC\` libera a memória numa thread em segundo plano, sem bloquear o servidor. Em bancos com milhões de chaves a diferença entre bloquear e não bloquear é o que decide se a aplicação sofre timeout durante a limpeza."
txt "O \`SELECT\` vale **por conexão**, então os comandos abaixo precisam rodar na mesma sessão:"
sessao 'SELECT 1' 'SET apenas:no:db1 "valor"' 'DBSIZE' 'SELECT 0' 'DBSIZE' 'GET apenas:no:db1'
nota "No banco 1 o \`DBSIZE\` é 1; de volta ao banco 0 é 0, e a chave criada no banco 1 não é visível — \`GET\` devolve vazio. Os bancos são espaços de nomes isolados dentro da mesma instância. O roteiro alerta: em produção prefira instâncias separadas, porque os bancos numerados compartilham CPU, memória e o mesmo processo de persistência."
sessao 'SELECT 1' 'FLUSHDB' 'SELECT 0'

# ===================== SECAO 4 =====================
sec "SEÇÃO 4 – Expiração, TTL e cache"

sub "4.1 – TTL básico"
cmds 'SET cache:home "html-home"' 'TTL cache:home'
nota "\`TTL\` devolve **-1** quando a chave existe mas não tem expiração, e **-2** quando a chave não existe. São respostas diferentes para situações diferentes — confundi-las é fonte comum de bug em camada de cache."
cmds 'EXPIRE cache:home 30' 'TTL cache:home'
cmds 'PERSIST cache:home' 'TTL cache:home'
nota "O \`PERSIST\` removeu a expiração e o TTL voltou a -1: a chave virou permanente."

sub "4.2 – Criando já com expiração"
cmds 'SET session:abc123 "payload" EX 60' 'GET session:abc123' 'TTL session:abc123'

sub "4.3 – Comando SETEX"
cmds 'SETEX cache:pagina:/home 20 "<html>HOME</html>"' 'GET cache:pagina:/home' 'TTL cache:pagina:/home'
nota "\`SETEX\` é equivalente a \`SET ... EX\`. A vantagem de qualquer um dos dois sobre \`SET\` seguido de \`EXPIRE\` é a atomicidade: não existe instante em que a chave esteja gravada sem prazo de validade."

sub "4.4 – Expirando em milissegundos"
cmds 'PSETEX cache:api:1 5000 "resultado-json"' 'PTTL cache:api:1' 'TTL cache:api:1'
nota "\`PTTL\` responde em milissegundos e \`TTL\` em segundos (arredondado para cima)."

sub "4.5 – Invalidando cache manualmente"
cmds 'DEL cache:pagina:/home' 'EXISTS cache:pagina:/home'

sub "Exercício 1"
txt "1) Criar \`cache:produto:10\` com TTL de 120 s · 2) consultar o conteúdo · 3) consultar o TTL · 4) remover manualmente."
cmds 'SET cache:produto:10 "{\"id\":10,\"nome\":\"Teclado\",\"preco\":250.00}" EX 120' \
     'GET cache:produto:10' \
     'TTL cache:produto:10' \
     'DEL cache:produto:10' \
     'EXISTS cache:produto:10' \
     'TTL cache:produto:10'
nota "Depois do \`DEL\`, o \`TTL\` passa a devolver -2 (chave inexistente), e não -1."

# ===================== SECAO 5 =====================
sec "SEÇÃO 5 – Strings"

sub "5.1 – Operações básicas"
cmds 'SET user:1001 "João"' 'GET user:1001' 'APPEND user:1001 " Silva"' 'GET user:1001' 'STRLEN user:1001'
nota "Atenção ao \`STRLEN\`: ele conta **bytes**, não caracteres. \"João Silva\" tem 10 caracteres, mas o \`ã\` ocupa 2 bytes em UTF-8, então o resultado é 11. O \`APPEND\` devolve o novo comprimento, também em bytes."

sub "5.2 – Múltiplas chaves"
cmds 'MSET user:2001 "Ana" user:2002 "Bruno" user:2003 "Carlos"' 'MGET user:2001 user:2002 user:2003'
nota "\`MSET\`/\`MGET\` resolvem várias chaves numa única ida ao servidor. O ganho não está no Redis processar mais rápido, está em eliminar o custo de rede por chave — o mesmo raciocínio do \`_bulk\` do Elasticsearch e do \`insertMany\` do MongoDB."

sub "5.3 – Contadores"
cmds 'SET visitas 0' 'INCR visitas' 'INCRBY visitas 10' 'DECR visitas' 'DECRBY visitas 2' 'GET visitas'
nota "Cada operação é atômica: mil clientes incrementando ao mesmo tempo não perdem contagem. É a razão de existir o \`INCR\` em vez de \`GET\`, somar na aplicação e \`SET\` — esse trio produz condição de corrida."

sub "5.4 – Incremento em valor monetário ou decimal"
cmds 'SET saldo 10.5' 'INCRBYFLOAT saldo 2.75' 'GET saldo'
nota "\`INCRBYFLOAT\` usa ponto flutuante. Para dinheiro, a prática segura é guardar centavos como inteiro e usar \`INCRBY\`, evitando erro de arredondamento binário."

sub "5.5 – Recuperação parcial de string"
cmds 'SET codigo "ABCDEFGH123456"' 'GETRANGE codigo 0 3' 'GETRANGE codigo 4 7' 'GETRANGE codigo -6 -1'
nota "Os índices são inclusivos nas duas pontas e aceitam valores negativos contando do fim."

sub "Exercício 2"
txt "1) Criar \`contador:login\` com 0 · 2) incrementar 5 vezes · 3) incrementar mais 10 de uma vez · 4) TTL de 60 s · 5) consultar valor e TTL."
cmds 'SET contador:login 0' 'INCR contador:login' 'INCR contador:login' 'INCR contador:login' \
     'INCR contador:login' 'INCR contador:login' 'INCRBY contador:login 10' \
     'EXPIRE contador:login 60' 'GET contador:login' 'TTL contador:login'
nota "Valor final 15 — cinco \`INCR\` mais um \`INCRBY 10\`. Detalhe importante: o \`INCR\` **não** renova o TTL. Uma chave de contador com expiração continua expirando no prazo original por mais que seja incrementada, e é exatamente disso que depende o rate limit da Seção 10.3."

# ===================== SECAO 6 =====================
sec "SEÇÃO 6 – Sets"

sub "6.1 – Inserção e consulta"
cmds 'SADD curso:BI "Ana" "Bruno" "Carlos"' 'SMEMBERS curso:BI' 'SCARD curso:BI' \
     'SISMEMBER curso:BI "Ana"' 'SISMEMBER curso:BI "Fernanda"'
txt "Tentando inserir um membro que já existe:"
cmd 'SADD curso:BI "Ana"'
nota "Devolve 0: nenhum elemento novo foi adicionado. O \`SADD\` informa quantos membros realmente entraram, o que permite usar o set como teste de unicidade — por exemplo, para saber se um voto ou um clique já foi computado."

sub "6.2 – Remoção"
cmds 'SREM curso:BI "Bruno"' 'SMEMBERS curso:BI'

sub "6.3 – Criando outro conjunto"
cmds 'SADD curso:DS "Ana" "Fernanda" "Marcos"' 'SMEMBERS curso:DS'

sub "6.4 – Operações de conjuntos"
cmds 'SINTER curso:BI curso:DS' 'SUNION curso:BI curso:DS' 'SDIFF curso:DS curso:BI' 'SDIFF curso:BI curso:DS'
nota "\`SDIFF\` não é comutativo: \`SDIFF A B\` devolve o que está em A e não em B. Trocar a ordem dos argumentos muda o resultado, como as duas últimas saídas mostram."

sub "6.5 – Sorteio/remoção aleatória"
cmds 'SADD equipe:sorteio "A" "B" "C" "D"' 'SRANDMEMBER equipe:sorteio' 'SPOP equipe:sorteio' 'SMEMBERS equipe:sorteio'
nota "\`SRANDMEMBER\` apenas lê; \`SPOP\` lê **e remove**. Para um sorteio sem repetição, \`SPOP\` é o comando correto — é a diferença entre espiar uma carta e tirá-la do baralho."

sub "Exercício 3"
txt "Criar \`interesses:python\` e \`interesses:redis\` com nomes repetidos entre eles e mostrar interseção, união e diferença."
cmds 'SADD interesses:python "Ana" "Bruno" "Carlos" "Diana"' \
     'SADD interesses:redis "Bruno" "Carlos" "Eduardo"' \
     'SINTER interesses:python interesses:redis' \
     'SUNION interesses:python interesses:redis' \
     'SDIFF interesses:python interesses:redis' \
     'SCARD interesses:python' 'SCARD interesses:redis'
nota "Interseção = quem tem os dois interesses (Bruno e Carlos). União = 5 pessoas distintas, apesar de 7 inserções — a unicidade do set eliminou as duplicatas. Diferença = só Python."

# ===================== SECAO 7 =====================
sec "SEÇÃO 7 – Sorted Sets (ranking)"

sub "7.1 – Criando ranking"
cmds 'ZADD ranking:pontos 100 "joao" 150 "maria" 90 "carlos"' \
     'ZRANGE ranking:pontos 0 -1 WITHSCORES' \
     'ZREVRANGE ranking:pontos 0 -1 WITHSCORES'
nota "\`ZRANGE\` ordena do menor para o maior score; \`ZREVRANGE\` inverte. Para ranking o natural é o \`ZREVRANGE\`, porque quem tem mais pontos deve aparecer primeiro."

sub "7.2 – Incrementando pontuação"
cmds 'ZINCRBY ranking:pontos 25 "carlos"' 'ZREVRANGE ranking:pontos 0 -1 WITHSCORES'
nota "Carlos saiu de 90 para 115 e ultrapassou João (100) — a reordenação é automática. O sorted set mantém a ordem a cada escrita, sem que ninguém precise reordenar nada."

sub "7.3 – Descobrindo posição"
cmds 'ZRANK ranking:pontos "carlos"' 'ZREVRANK ranking:pontos "carlos"'
nota "As posições são baseadas em zero. \`ZRANK\` conta do menor score; \`ZREVRANK\` do maior — este é o que corresponde à colocação no ranking."

sub "7.4 – Consultando score"
cmds 'ZSCORE ranking:pontos "maria"' 'ZCARD ranking:pontos'

sub "7.5 – Top N"
cmd 'ZREVRANGE ranking:pontos 0 1 WITHSCORES'
nota "Top 2. O intervalo \`0 1\` é inclusivo nas duas pontas, então devolve dois elementos, não um."

sub "7.6 – Removendo participante"
cmds 'ZREM ranking:pontos "joao"' 'ZREVRANGE ranking:pontos 0 -1 WITHSCORES'

sub "Exercício 4"
txt "1) Criar \`ranking:turma\` com 5 alunos · 2) incrementar a nota de dois · 3) mostrar o Top 3 · 4) mostrar a posição de um aluno."
cmds 'ZADD ranking:turma 7.5 "Ana" 8.0 "Bruno" 6.5 "Carlos" 9.0 "Diana" 5.5 "Eduardo"' \
     'ZREVRANGE ranking:turma 0 -1 WITHSCORES' \
     'ZINCRBY ranking:turma 1.5 "Carlos"' \
     'ZINCRBY ranking:turma 0.5 "Eduardo"' \
     'ZREVRANGE ranking:turma 0 2 WITHSCORES' \
     'ZREVRANK ranking:turma "Carlos"' \
     'ZSCORE ranking:turma "Carlos"'
nota "Carlos subiu de 6,5 para 8,0 e empatou com Bruno. Em caso de empate o Redis ordena pelo **membro**, em ordem lexicográfica — mas como o \`ZREVRANGE\` percorre a estrutura ao contrário, o empate também sai invertido e \"Carlos\" aparece antes de \"Bruno\". Verificado à parte: com Ana, Bruno e Carlos todos com score 8, \`ZRANGE\` devolve Ana → Bruno → Carlos e \`ZREVRANGE\` devolve Carlos → Bruno → Ana. O \`ZREVRANK\` devolve a colocação começando em zero, então o 1 aqui significa **segundo lugar**."

# ===================== SECAO 8 =====================
sec "SEÇÃO 8 – Lists"

sub "8.1 – Inserção no início e no fim"
cmds 'LPUSH fila:processamento "job1"' 'LPUSH fila:processamento "job2"' \
     'RPUSH fila:processamento "job3"' 'LRANGE fila:processamento 0 -1'
nota "\`LPUSH\` insere à esquerda (início) e \`RPUSH\` à direita (fim). Como job1 entrou primeiro pela esquerda e job2 depois, a ordem final é job2, job1, job3."

sub "8.2 – Consumo FIFO"
cmds 'RPOP fila:processamento' 'LRANGE fila:processamento 0 -1'
nota "\`LPUSH\` + \`RPOP\` = FIFO: entra pela esquerda, sai pela direita, e quem chegou primeiro sai primeiro."

sub "8.3 – Consumo LIFO"
cmds 'LPOP fila:processamento' 'LRANGE fila:processamento 0 -1'
nota "\`LPUSH\` + \`LPOP\` = LIFO (pilha): entra e sai pelo mesmo lado."

sub "8.4 – Tamanho da lista"
cmd 'LLEN fila:processamento'

sub "8.5 – Leitura por intervalo"
cmds 'RPUSH fila:pedidos "p1" "p2" "p3" "p4"' 'LRANGE fila:pedidos 0 -1' \
     'LRANGE fila:pedidos 0 1' 'LRANGE fila:pedidos -2 -1'
nota "Índices negativos contam do fim: \`-1\` é o último elemento e \`-2 -1\` devolve os dois últimos. \`LRANGE\` apenas lê, não remove."

sub "Exercício 5"
txt "1) Criar 5 jobs em \`fila:etl\` · 2) listar · 3) consumir dois com \`RPOP\`."
cmds 'RPUSH fila:etl "job:extrair" "job:transformar" "job:validar" "job:carregar" "job:notificar"' \
     'LLEN fila:etl' 'LRANGE fila:etl 0 -1' \
     'RPOP fila:etl' 'RPOP fila:etl' \
     'LRANGE fila:etl 0 -1' 'LLEN fila:etl'
nota "Como os jobs entraram com \`RPUSH\` (pela direita) e saem com \`RPOP\` (também pela direita), o consumo é LIFO: saíram os dois **últimos** da fila. Para FIFO com \`RPUSH\`, o consumo correto é \`LPOP\`. Essa inversão é o erro mais comum com listas no Redis."

# ===================== SECAO 9 =====================
sec "SEÇÃO 9 – Hashes"

sub "9.1 – Criando documento"
cmds 'HSET aluno:1 nome "Carlos Silva" idade 22 curso "Engenharia de Dados"' \
     'HGET aluno:1 nome' 'HGETALL aluno:1' 'HKEYS aluno:1' 'HVALS aluno:1' 'HLEN aluno:1'
nota "O hash representa uma entidade sem precisar serializar JSON: cada campo é lido e escrito isoladamente. Com uma string JSON, atualizar a idade exigiria ler o documento inteiro, alterar na aplicação e regravar — três operações e uma janela de condição de corrida."

sub "9.2 – Consulta parcial de vários campos"
cmd 'HMGET aluno:1 nome curso'

sub "9.3 – Atualização de um campo específico"
cmds 'HSET aluno:1 cidade "Brasília"' 'HGETALL aluno:1'
nota "O \`HSET\` devolve 1 quando o campo é novo e 0 quando apenas atualiza um campo existente."

sub "9.4 – Incremento numérico dentro do hash"
cmds 'HINCRBY aluno:1 idade 1' 'HGET aluno:1 idade'
nota "Os valores de um hash são sempre strings, mas o \`HINCRBY\` interpreta como inteiro e incrementa atomicamente — sem ler-somar-gravar na aplicação."

sub "9.5 – Verificando existência de campo"
cmds 'HEXISTS aluno:1 cidade' 'HEXISTS aluno:1 email'

sub "9.6 – Removendo campo"
cmds 'HDEL aluno:1 cidade' 'HGETALL aluno:1'
nota "Removendo o último campo de um hash, a chave inteira deixa de existir — no Redis não há coleção vazia."

sub "Exercício 6"
txt "1) Criar \`aluno:2\` e \`aluno:3\` · 2) consultar só o campo curso de cada um · 3) incrementar a idade de \`aluno:2\` · 4) listar todos os campos de \`aluno:3\`."
cmds 'HSET aluno:2 nome "Ana Ribeiro" idade 20 curso "Ciência de Dados"' \
     'HSET aluno:3 nome "Bruno Tavares" idade 25 curso "Engenharia de Software"' \
     'HGET aluno:2 curso' 'HGET aluno:3 curso' \
     'HINCRBY aluno:2 idade 1' 'HGET aluno:2 idade' \
     'HGETALL aluno:3'

# ===================== SECAO 10 =====================
sec "SEÇÃO 10 – Padrões de aplicação"

sub "10.1 – Cache com TTL"
cmds 'SETEX cache:consulta:clientes 30 "{resultado_json}"' 'GET cache:consulta:clientes' 'TTL cache:consulta:clientes'

sub "10.2 – Sessão de usuário"
cmds "SET session:user:1001 \"{token:'abc',perfil:'admin'}\" EX 300" 'GET session:user:1001' 'TTL session:user:1001'
nota "A sessão expirar sozinha é o ponto: não existe rotina de limpeza, nem job noturno varrendo sessões mortas. O Redis remove a chave no vencimento."

sub "10.3 – Rate limit simples"
cmds 'INCR rl:user:42' 'EXPIRE rl:user:42 60' 'GET rl:user:42' 'TTL rl:user:42'
txt "Simulando mais requisições do mesmo usuário dentro da janela:"
cmds 'INCR rl:user:42' 'INCR rl:user:42' 'INCR rl:user:42' 'INCR rl:user:42' 'INCR rl:user:42' \
     'GET rl:user:42' 'TTL rl:user:42'
nota "Regra didática do roteiro: acima de 5, bloquear. Repare que o TTL **não** foi renovado pelos \`INCR\` seguintes — a janela continua contando a partir do primeiro acesso, que é o comportamento desejado. Há porém uma falha de concorrência aqui: entre o \`INCR\` e o \`EXPIRE\` existe um instante em que a chave não tem prazo, e se o processo morrer nesse intervalo o contador fica eterno e bloqueia o usuário para sempre. A Seção 18 (script Lua) resolve exatamente isso."

sub "10.4 – Fila simples"
cmds 'LPUSH fila:emails "email1"' 'LPUSH fila:emails "email2"' 'LRANGE fila:emails 0 -1' 'RPOP fila:emails'
nota "Aqui a combinação está correta: \`LPUSH\` + \`RPOP\` é FIFO, então saiu o email1, que foi o primeiro a entrar."

sub "10.5 – Ranking"
cmds 'ZADD ranking:jogo 500 "ana" 900 "bruno" 700 "carla"' 'ZREVRANGE ranking:jogo 0 -1 WITHSCORES'

sub "Exercício 7"
txt "Cenário completo: cache de página, contador de visitas, sessão temporária e ranking com 3 jogadores."
cmds 'SETEX cache:pagina:/produtos 60 "<html><body>Lista de produtos</body></html>"' \
     'SET visitas:pagina:/produtos 0' 'INCR visitas:pagina:/produtos' 'INCR visitas:pagina:/produtos' \
     'INCR visitas:pagina:/produtos' \
     'SET session:user:2002 "{token:def456,perfil:cliente}" EX 180' \
     'ZADD ranking:torneio 1200 "ana" 1450 "bruno" 980 "carla"' \
     'GET cache:pagina:/produtos' 'TTL cache:pagina:/produtos' \
     'GET visitas:pagina:/produtos' \
     'TTL session:user:2002' \
     'ZREVRANGE ranking:torneio 0 -1 WITHSCORES'
nota "Quatro estruturas para quatro necessidades: string com TTL para o cache, string com \`INCR\` para o contador, string com TTL para a sessão e sorted set para o ranking. Repare que o contador de visitas **não** tem TTL — ele precisa sobreviver à expiração do cache da página."

# ===================== SECAO 11 =====================
sec "SEÇÃO 11 – Pub/Sub"
txt "O roteiro pede dois terminais. Aqui o assinante foi posto em segundo plano, gravando num arquivo, e a publicação feita em seguida por outra conexão."

sub "11.1 – Publicação e inscrição"
SUBOUT=$(mktemp)
docker exec redis redis-cli SUBSCRIBE canal:noticias > "$SUBOUT" 2>&1 &
SUBPID=$!
sleep 2
P1=$(echo 'PUBLISH canal:noticias "Mensagem 1"' | $R)
P2=$(echo 'PUBLISH canal:noticias "Mensagem 2"' | $R)
sleep 1
kill $SUBPID 2>/dev/null; wait $SUBPID 2>/dev/null
{ echo ""; echo "**Terminal 1 — assinante:**"; echo ""; echo '```'
  echo "SUBSCRIBE canal:noticias"; echo '```'; echo ""
  echo "**Terminal 2 — publicador:**"; echo ""; echo '```'
  echo 'PUBLISH canal:noticias "Mensagem 1"'; echo "$P1"
  echo 'PUBLISH canal:noticias "Mensagem 2"'; echo "$P2"; echo '```'; echo ""
  echo "**O que o assinante recebeu:**"; echo ""; echo '```'
  cat "$SUBOUT"; echo '```'; } >> "$OUT"
rm -f "$SUBOUT"
nota "O \`PUBLISH\` devolve **quantos assinantes receberam** a mensagem — 1 nos dois casos. Se ninguém estivesse inscrito, devolveria 0 e a mensagem seria descartada: o Pub/Sub não guarda nada. Essa é a diferença central para as Streams da Seção 12."
echo "  . pub/sub simples"

sub "11.2 – Pattern subscribe"
SUBOUT=$(mktemp)
docker exec redis redis-cli PSUBSCRIBE 'canal:*' > "$SUBOUT" 2>&1 &
SUBPID=$!
sleep 2
P1=$(echo 'PUBLISH canal:noticias "Nova noticia"' | $R)
P2=$(echo 'PUBLISH canal:alertas "Alerta importante"' | $R)
P3=$(echo 'PUBLISH outro:canal "Nao deve chegar"' | $R)
sleep 1
kill $SUBPID 2>/dev/null; wait $SUBPID 2>/dev/null
{ echo ""; echo "**Terminal 1 — assinante por padrão:**"; echo ""; echo '```'
  echo "PSUBSCRIBE canal:*"; echo '```'; echo ""
  echo "**Terminal 2 — publicador:**"; echo ""; echo '```'
  echo 'PUBLISH canal:noticias "Nova noticia"'; echo "$P1"
  echo 'PUBLISH canal:alertas "Alerta importante"'; echo "$P2"
  echo 'PUBLISH outro:canal "Nao deve chegar"'; echo "$P3"; echo '```'; echo ""
  echo "**O que o assinante recebeu:**"; echo ""; echo '```'
  cat "$SUBOUT"; echo '```'; } >> "$OUT"
rm -f "$SUBOUT"
nota "As duas primeiras mensagens casaram com o padrão \`canal:*\` e chegaram. A terceira, publicada em \`outro:canal\`, devolveu **0 assinantes** e não foi entregue — comprovando que o padrão filtra de verdade."
echo "  . pattern subscribe"

sub "Exercício 8"
txt "1) Criar \`canal:alertas\` · 2) inscrever um terminal · 3) publicar 3 mensagens de outro terminal."
SUBOUT=$(mktemp)
docker exec redis redis-cli SUBSCRIBE canal:alertas > "$SUBOUT" 2>&1 &
SUBPID=$!
sleep 2
A1=$(echo 'PUBLISH canal:alertas "Alerta 1: CPU acima de 90%"' | $R)
A2=$(echo 'PUBLISH canal:alertas "Alerta 2: disco em 85%"' | $R)
A3=$(echo 'PUBLISH canal:alertas "Alerta 3: servico reiniciado"' | $R)
sleep 1
kill $SUBPID 2>/dev/null; wait $SUBPID 2>/dev/null
{ echo ""; echo "**Publicador (3 mensagens, cada uma devolvendo o nº de assinantes):**"; echo ""; echo '```'
  echo 'PUBLISH canal:alertas "Alerta 1: CPU acima de 90%"'; echo "$A1"
  echo 'PUBLISH canal:alertas "Alerta 2: disco em 85%"'; echo "$A2"
  echo 'PUBLISH canal:alertas "Alerta 3: servico reiniciado"'; echo "$A3"; echo '```'; echo ""
  echo "**Assinante:**"; echo ""; echo '```'
  cat "$SUBOUT"; echo '```'; } >> "$OUT"
rm -f "$SUBOUT"
echo "  . exercicio 8"

txt "---"
txt "Fim da Parte 1. As chaves criadas aqui permanecem no banco e são usadas pela Parte 2; a limpeza está na Seção 23."
shell "docker exec redis redis-cli DBSIZE"
echo "PARTE 1 CONCLUIDA -> $OUT"
