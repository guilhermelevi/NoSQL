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
txt "Cobre as Seções 1 a 11 e os Exercícios 1 a 8. Rodei todos os comandos no container \`redis\` e as saídas são as que apareceram."

# ===================== SECAO 1 =====================
sec "SEÇÃO 1 – Preparação do ambiente"
txt "O roteiro copia o ambiente para a VM com scp e usa sudo nos comandos. Fiz no macOS com OrbStack, então não precisei de nada disso: o docker-compose.yml fica no próprio projeto e as portas já respondem em localhost."

sub "1.2 – Subir o ambiente"
shell "docker compose -f ../docker-compose.yml ps --format 'table {{.Name}}\t{{.State}}\t{{.Ports}}'"

sub "1.3 e 1.4 – Acessar o redis-cli e testar a conexão"
txt "O roteiro dá duas opções, entrar no container ou instalar o redis-tools no host. Usei a primeira para não instalar nada:"
cmd "PING"

sub "1.5 – Informações básicas do servidor"
info "server" "redis_version|redis_mode|os:|arch_bits|process_id|tcp_port|uptime_in_seconds"
info "memory" "used_memory:|used_memory_human|used_memory_peak_human|maxmemory:|maxmemory_human|maxmemory_policy"
info "keyspace" "^#|^db"
cmd "DBSIZE"

# ===================== SECAO 2 =====================
sec "SEÇÃO 2 – Acesso ao RedisInsight"
txt "O roteiro manda liberar a porta 5540 no VirtualBox. Com OrbStack ela já está publicada, é só abrir <http://localhost:5540>."
shell "curl -s -o /dev/null -w 'RedisInsight responde: HTTP %{http_code}\\n' http://localhost:5540"
nota "A URL é \`redis://redis:6379\` e não localhost. De dentro do contêiner do RedisInsight, localhost seria ele mesmo. O nome \`redis\` é o do serviço no compose."
txt "O roteiro sugere navegar pela árvore de chaves e ver como os prefixos com : viram grupos. Dá para conferir isso a partir da Seção 5, quando já existem chaves como user:1001 e cache:pagina:/home."

# ===================== SECAO 3 =====================
sec "SEÇÃO 3 – Operações básicas com chaves"

sub "3.1 – Criando e consultando uma string"
cmds 'SET curso "NoSQL - Redis"' 'GET curso' 'TYPE curso' 'EXISTS curso'

sub "3.2 – Sobrescrevendo valor"
cmds 'SET curso "NoSQL - Redis Avançado"' 'GET curso'

sub "3.3 – Apagando chave"
cmds 'DEL curso' 'EXISTS curso'

sub "3.4 – Inspeção de chaves"
txt "Criei algumas chaves antes:"
cmds 'MSET user:1 "a" user:2 "b" user:3 "c" outro:1 "x"'
txt "O roteiro diz para evitar em produção, porque o KEYS percorre o keyspace inteiro e bloqueia o servidor:"
cmd "KEYS *"
txt "A alternativa é o SCAN, que é incremental e devolve um cursor:"
cmd "SCAN 0 MATCH * COUNT 100"
cmd "SCAN 0 MATCH user:* COUNT 100"
nota "O primeiro valor da resposta é o cursor. Voltou 0, então a varredura acabou numa passada só. Com muitas chaves ele viria diferente de zero e eu teria que chamar o SCAN de novo passando esse valor."
cmds 'DEL user:1 user:2 user:3 outro:1'

sub "3.5 – Descobrindo o tipo de uma chave"
cmds 'SET temp "abc"' 'TYPE temp' 'DEL temp'

sub "3.6 – Renomeando e movendo chaves"
cmds 'SET chave:original "valor"' 'RENAME chave:original chave:nova' 'GET chave:nova'
txt "O roteiro avisa que o RENAME falha se a chave original não existir. Conferindo:"
cmd "RENAME chave:inexistente chave:qualquer"
cmds 'DEL chave:nova'

sub "3.7 – Limpando o banco"
txt "Criei chaves para ver o efeito:"
cmds 'MSET a 1 b 2 c 3' 'DBSIZE'
cmds 'FLUSHDB' 'DBSIZE'
nota "O FLUSHDB limpa só o banco atual. O FLUSHALL limpa os 16, por isso deixei comentado."

sub "3.8 – Variantes de limpeza e seleção de banco"
cmd "FLUSHDB ASYNC"
nota "O ASYNC libera a memória em segundo plano, sem travar o servidor durante a limpeza."
txt "O SELECT vale por conexão, então rodei os comandos abaixo na mesma sessão:"
sessao 'SELECT 1' 'SET apenas:no:db1 "valor"' 'DBSIZE' 'SELECT 0' 'DBSIZE' 'GET apenas:no:db1'
nota "A chave criada no banco 1 não aparece no banco 0. Os bancos são isolados, mas dividem o mesmo processo e a mesma memória, então o roteiro tem razão em dizer que em produção é melhor usar instâncias separadas."
sessao 'SELECT 1' 'FLUSHDB' 'SELECT 0'

# ===================== SECAO 4 =====================
sec "SEÇÃO 4 – Expiração, TTL e cache"

sub "4.1 – TTL básico"
cmds 'SET cache:home "html-home"' 'TTL cache:home'
nota "O TTL tem três respostas: os segundos que faltam, -1 se a chave existe e não expira, e -2 se ela não existe. Confundir -1 com -2 dá problema em cache, porque uma coisa é estar guardado para sempre e outra é não estar guardado."
cmds 'EXPIRE cache:home 30' 'TTL cache:home'
cmds 'PERSIST cache:home' 'TTL cache:home'

sub "4.2 – Criando já com expiração"
cmds 'SET session:abc123 "payload" EX 60' 'GET session:abc123' 'TTL session:abc123'

sub "4.3 – Comando SETEX"
cmds 'SETEX cache:pagina:/home 20 "<html>HOME</html>"' 'GET cache:pagina:/home' 'TTL cache:pagina:/home'
nota "O SETEX faz o mesmo que SET com EX. Os dois são melhores que SET seguido de EXPIRE porque gravam o valor e o prazo juntos, sem deixar a chave um instante sem validade."

sub "4.4 – Expirando em milissegundos"
cmds 'PSETEX cache:api:1 5000 "resultado-json"' 'PTTL cache:api:1' 'TTL cache:api:1'

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

# ===================== SECAO 5 =====================
sec "SEÇÃO 5 – Strings"

sub "5.1 – Operações básicas"
cmds 'SET user:1001 "João"' 'GET user:1001' 'APPEND user:1001 " Silva"' 'GET user:1001' 'STRLEN user:1001'
nota "O STRLEN deu 11 e não 10 porque ele conta bytes, não caracteres. O ã ocupa 2 bytes em UTF-8. O APPEND devolve o mesmo número."

sub "5.2 – Múltiplas chaves"
cmds 'MSET user:2001 "Ana" user:2002 "Bruno" user:2003 "Carlos"' 'MGET user:2001 user:2002 user:2003'
nota "MSET e MGET resolvem tudo numa ida só ao servidor. O ganho é o mesmo do insertMany do MongoDB: economizar viagem de rede."

sub "5.3 – Contadores"
cmds 'SET visitas 0' 'INCR visitas' 'INCRBY visitas 10' 'DECR visitas' 'DECRBY visitas 2' 'GET visitas'
nota "O INCR é atômico. Se eu fizesse GET, somasse na aplicação e desse SET, dois clientes simultâneos poderiam ler o mesmo valor e um sobrescreveria a contagem do outro."

sub "5.4 – Incremento em valor monetário ou decimal"
cmds 'SET saldo 10.5' 'INCRBYFLOAT saldo 2.75' 'GET saldo'
nota "O INCRBYFLOAT usa ponto flutuante. Para dinheiro prefiro guardar centavos em inteiro e usar INCRBY, para não pegar erro de arredondamento."

sub "5.5 – Recuperação parcial de string"
cmds 'SET codigo "ABCDEFGH123456"' 'GETRANGE codigo 0 3' 'GETRANGE codigo 4 7' 'GETRANGE codigo -6 -1'

sub "Exercício 2"
txt "1) Criar \`contador:login\` com 0 · 2) incrementar 5 vezes · 3) incrementar mais 10 de uma vez · 4) TTL de 60 s · 5) consultar valor e TTL."
cmds 'SET contador:login 0' 'INCR contador:login' 'INCR contador:login' 'INCR contador:login' \
     'INCR contador:login' 'INCR contador:login' 'INCRBY contador:login 10' \
     'EXPIRE contador:login 60' 'GET contador:login' 'TTL contador:login'
nota "Deu 15, que são os cinco INCR mais o INCRBY 10, e o TTL ficou em 60. Testando aqui, o INCR não renova o TTL: a chave continua expirando no prazo que foi definido, por mais que eu incremente."

# ===================== SECAO 6 =====================
sec "SEÇÃO 6 – Sets"

sub "6.1 – Inserção e consulta"
cmds 'SADD curso:BI "Ana" "Bruno" "Carlos"' 'SMEMBERS curso:BI' 'SCARD curso:BI' \
     'SISMEMBER curso:BI "Ana"' 'SISMEMBER curso:BI "Fernanda"'
txt "Inserindo um membro que já está no conjunto:"
cmd 'SADD curso:BI "Ana"'
nota "Devolveu 0 porque a Ana já estava no conjunto. O SADD informa quantos entraram de fato, então dá para usar o retorno para saber se um valor é repetido."

sub "6.2 – Remoção"
cmds 'SREM curso:BI "Bruno"' 'SMEMBERS curso:BI'

sub "6.3 – Criando outro conjunto"
cmds 'SADD curso:DS "Ana" "Fernanda" "Marcos"' 'SMEMBERS curso:DS'

sub "6.4 – Operações de conjuntos"
cmds 'SINTER curso:BI curso:DS' 'SUNION curso:BI curso:DS' 'SDIFF curso:DS curso:BI' 'SDIFF curso:BI curso:DS'
nota "O SDIFF não é comutativo. SDIFF A B traz o que está em A e não está em B, e invertendo a ordem o resultado muda, como aparece nas duas últimas saídas."

sub "6.5 – Sorteio/remoção aleatória"
cmds 'SADD equipe:sorteio "A" "B" "C" "D"' 'SRANDMEMBER equipe:sorteio' 'SPOP equipe:sorteio' 'SMEMBERS equipe:sorteio'
nota "O SRANDMEMBER só lê, o SPOP lê e remove. Para sorteio sem repetir, é o SPOP."

sub "Exercício 3"
txt "Criar \`interesses:python\` e \`interesses:redis\` com nomes repetidos entre eles e mostrar interseção, união e diferença."
cmds 'SADD interesses:python "Ana" "Bruno" "Carlos" "Diana"' \
     'SADD interesses:redis "Bruno" "Carlos" "Eduardo"' \
     'SINTER interesses:python interesses:redis' \
     'SUNION interesses:python interesses:redis' \
     'SDIFF interesses:python interesses:redis' \
     'SCARD interesses:python' 'SCARD interesses:redis'
nota "Interseção: Bruno e Carlos, que estão nos dois conjuntos. União: 5 nomes, mesmo eu tendo inserido 7 vezes, porque o set não repete. Diferença de python para redis: Ana e Diana."

# ===================== SECAO 7 =====================
sec "SEÇÃO 7 – Sorted Sets (ranking)"

sub "7.1 – Criando ranking"
cmds 'ZADD ranking:pontos 100 "joao" 150 "maria" 90 "carlos"' \
     'ZRANGE ranking:pontos 0 -1 WITHSCORES' \
     'ZREVRANGE ranking:pontos 0 -1 WITHSCORES'
nota "O ZRANGE vai do menor score para o maior e o ZREVRANGE inverte. Para ranking uso o ZREVRANGE, porque quem tem mais ponto tem que vir primeiro."

sub "7.2 – Incrementando pontuação"
cmds 'ZINCRBY ranking:pontos 25 "carlos"' 'ZREVRANGE ranking:pontos 0 -1 WITHSCORES'

sub "7.3 – Descobrindo posição"
cmds 'ZRANK ranking:pontos "carlos"' 'ZREVRANK ranking:pontos "carlos"'
nota "As posições começam em zero. O ZRANK conta a partir do menor score e o ZREVRANK a partir do maior, que é o que corresponde à colocação."

sub "7.4 – Consultando score"
cmds 'ZSCORE ranking:pontos "maria"' 'ZCARD ranking:pontos'

sub "7.5 – Top N"
cmd 'ZREVRANGE ranking:pontos 0 1 WITHSCORES'

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
nota "Carlos foi para 8,0 e empatou com Bruno. No empate o Redis ordena pelo nome do membro, mas como o ZREVRANGE percorre ao contrário o empate também sai invertido, e o Carlos aparece antes do Bruno. Testei separado com Ana, Bruno e Carlos todos com 8: no ZRANGE saiu Ana, Bruno, Carlos e no ZREVRANGE saiu Carlos, Bruno, Ana. O ZREVRANK devolveu 1, que é segundo lugar."

# ===================== SECAO 8 =====================
sec "SEÇÃO 8 – Lists"

sub "8.1 – Inserção no início e no fim"
cmds 'LPUSH fila:processamento "job1"' 'LPUSH fila:processamento "job2"' \
     'RPUSH fila:processamento "job3"' 'LRANGE fila:processamento 0 -1'
nota "O LPUSH insere no início e o RPUSH no fim. O job1 entrou primeiro pela esquerda e o job2 depois, por isso a ordem ficou job2, job1, job3."

sub "8.2 – Consumo FIFO"
cmds 'RPOP fila:processamento' 'LRANGE fila:processamento 0 -1'
nota "LPUSH com RPOP é FIFO: entra de um lado e sai do outro, então sai primeiro quem chegou primeiro."

sub "8.3 – Consumo LIFO"
cmds 'LPOP fila:processamento' 'LRANGE fila:processamento 0 -1'
nota "LPUSH com LPOP é pilha: entra e sai pelo mesmo lado."

sub "8.4 – Tamanho da lista"
cmd 'LLEN fila:processamento'

sub "8.5 – Leitura por intervalo"
cmds 'RPUSH fila:pedidos "p1" "p2" "p3" "p4"' 'LRANGE fila:pedidos 0 -1' \
     'LRANGE fila:pedidos 0 1' 'LRANGE fila:pedidos -2 -1'

sub "Exercício 5"
txt "1) Criar 5 jobs em \`fila:etl\` · 2) listar · 3) consumir dois com \`RPOP\`."
cmds 'RPUSH fila:etl "job:extrair" "job:transformar" "job:validar" "job:carregar" "job:notificar"' \
     'LLEN fila:etl' 'LRANGE fila:etl 0 -1' \
     'RPOP fila:etl' 'RPOP fila:etl' \
     'LRANGE fila:etl 0 -1' 'LLEN fila:etl'
nota "Saíram o job:notificar e o job:carregar, que eram os dois últimos. Entrei com RPUSH e consumi com RPOP, as duas pontas iguais, então virou pilha e não fila. Para ficar FIFO com RPUSH eu teria que consumir com LPOP."

# ===================== SECAO 9 =====================
sec "SEÇÃO 9 – Hashes"

sub "9.1 – Criando documento"
cmds 'HSET aluno:1 nome "Carlos Silva" idade 22 curso "Engenharia de Dados"' \
     'HGET aluno:1 nome' 'HGETALL aluno:1' 'HKEYS aluno:1' 'HVALS aluno:1' 'HLEN aluno:1'
nota "O hash guarda a entidade sem precisar serializar JSON, e dá para ler e escrever um campo de cada vez. Com JSON numa string eu teria que ler tudo, alterar na aplicação e gravar de volta."

sub "9.2 – Consulta parcial de vários campos"
cmd 'HMGET aluno:1 nome curso'

sub "9.3 – Atualização de um campo específico"
cmds 'HSET aluno:1 cidade "Brasília"' 'HGETALL aluno:1'

sub "9.4 – Incremento numérico dentro do hash"
cmds 'HINCRBY aluno:1 idade 1' 'HGET aluno:1 idade'
nota "O HINCRBY incrementa o campo direto no servidor, mesmo os valores do hash sendo strings."

sub "9.5 – Verificando existência de campo"
cmds 'HEXISTS aluno:1 cidade' 'HEXISTS aluno:1 email'

sub "9.6 – Removendo campo"
cmds 'HDEL aluno:1 cidade' 'HGETALL aluno:1'
nota "Quando apago o último campo, a chave some junto. No Redis não existe hash vazio."

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

sub "10.3 – Rate limit simples"
cmds 'INCR rl:user:42' 'EXPIRE rl:user:42 60' 'GET rl:user:42' 'TTL rl:user:42'
txt "Mais requisições do mesmo usuário dentro da janela:"
cmds 'INCR rl:user:42' 'INCR rl:user:42' 'INCR rl:user:42' 'INCR rl:user:42' 'INCR rl:user:42' \
     'GET rl:user:42' 'TTL rl:user:42'
nota "A regra do roteiro é bloquear acima de 5. O TTL não foi renovado pelos INCR seguintes, então a janela conta a partir do primeiro acesso. Reparei que entre o INCR e o EXPIRE existe um instante em que a chave está sem prazo: se o processo morrer ali, o contador nunca expira e o usuário fica bloqueado para sempre."

sub "10.4 – Fila simples"
cmds 'LPUSH fila:emails "email1"' 'LPUSH fila:emails "email2"' 'LRANGE fila:emails 0 -1' 'RPOP fila:emails'

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
nota "Usei string com TTL no cache e na sessão, string com INCR no contador e sorted set no ranking. Deixei o contador de visitas sem TTL de propósito, senão ele zeraria junto com o cache da página."

# ===================== SECAO 11 =====================
sec "SEÇÃO 11 – Pub/Sub"
txt "O roteiro pede dois terminais. Deixei o assinante rodando em segundo plano, gravando num arquivo, e publiquei em seguida por outra conexão."

sub "11.1 – Publicação e inscrição"
SUBOUT=$(mktemp)
docker exec redis redis-cli SUBSCRIBE canal:noticias > "$SUBOUT" 2>&1 &
SUBPID=$!
sleep 2
P1=$(echo 'PUBLISH canal:noticias "Mensagem 1"' | $R)
P2=$(echo 'PUBLISH canal:noticias "Mensagem 2"' | $R)
sleep 1
kill $SUBPID 2>/dev/null; wait $SUBPID 2>/dev/null
{ echo ""; echo "**Terminal 1, assinante:**"; echo ""; echo '```'
  echo "SUBSCRIBE canal:noticias"; echo '```'; echo ""
  echo "**Terminal 2, publicador:**"; echo ""; echo '```'
  echo 'PUBLISH canal:noticias "Mensagem 1"'; echo "$P1"
  echo 'PUBLISH canal:noticias "Mensagem 2"'; echo "$P2"; echo '```'; echo ""
  echo "**O que o assinante recebeu:**"; echo ""; echo '```'
  cat "$SUBOUT"; echo '```'; } >> "$OUT"
rm -f "$SUBOUT"
nota "O PUBLISH devolve quantos assinantes receberam, 1 nos dois casos. Sem ninguém inscrito ele devolveria 0 e a mensagem se perderia, porque o Pub/Sub não guarda nada."
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
{ echo ""; echo "**Terminal 1, assinante por padrão:**"; echo ""; echo '```'
  echo "PSUBSCRIBE canal:*"; echo '```'; echo ""
  echo "**Terminal 2, publicador:**"; echo ""; echo '```'
  echo 'PUBLISH canal:noticias "Nova noticia"'; echo "$P1"
  echo 'PUBLISH canal:alertas "Alerta importante"'; echo "$P2"
  echo 'PUBLISH outro:canal "Nao deve chegar"'; echo "$P3"; echo '```'; echo ""
  echo "**O que o assinante recebeu:**"; echo ""; echo '```'
  cat "$SUBOUT"; echo '```'; } >> "$OUT"
rm -f "$SUBOUT"
nota "As duas primeiras casaram com canal:* e chegaram. A terceira foi para outro:canal, devolveu 0 assinantes e não chegou."
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
txt "Fim da Parte 1. As chaves continuam no banco e são usadas na Parte 2, a limpeza fica na Seção 23."
shell "docker exec redis redis-cli DBSIZE"
echo "PARTE 1 CONCLUIDA -> $OUT"
