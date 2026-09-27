#!/bin/bash
# Lab 3 - Redis - Parte 2 (Secoes 12 a 23)
# uso: ./parte2.sh ../PARTE2-EVIDENCIAS.md
set -u
cd "$(dirname "$0")"
export OUT="${1:-../PARTE2-EVIDENCIAS.md}"
: > "$OUT"
source ./lib.sh

echo "# Lab 3 – Redis – Parte 2 – Evidências de execução" >> "$OUT"
txt "Executado em $(date '+%d/%m/%Y %H:%M') · Redis $(echo 'INFO server' | $R | grep redis_version | tr -d '\r' | cut -d: -f2) · macOS/OrbStack"
txt "Cobre as Seções 12 a 23. Continua no mesmo banco da Parte 1 — as chaves criadas lá ainda estão presentes e são usadas na limpeza da Seção 23."

# ===================== SECAO 12 =====================
sec "SEÇÃO 12 – Streams"
txt "Streams são um log append-only persistente. Diferente do Pub/Sub da Seção 11, a mensagem fica guardada e pode ser lida depois, quantas vezes for preciso."

sub "12.1 – Inserindo eventos"
cmds 'XADD stream:pedidos * pedido_id 1001 status novo cliente "Ana"' \
     'XADD stream:pedidos * pedido_id 1002 status pago cliente "Bruno"'
nota "O \`*\` pede que o Redis gere o ID. O formato é \`<timestamp-em-ms>-<sequência>\`: o primeiro número é o instante da inserção, o segundo desempata eventos gravados no mesmo milissegundo. IDs sempre crescem, o que garante ordenação total."

sub "12.2 – Lendo eventos"
cmd 'XRANGE stream:pedidos - +'
nota "\`-\` e \`+\` significam o menor e o maior ID possíveis, ou seja, o stream inteiro."
cmd 'XREAD COUNT 10 STREAMS stream:pedidos 0'
nota "O \`0\` é o ponto de partida: devolve tudo a partir do começo. A leitura **não consome** — os eventos continuam lá, e é isso que separa um stream de uma fila com \`RPOP\`."
cmd 'XLEN stream:pedidos'

sub "12.3 – Consumer group"
cmd 'XGROUP CREATE stream:pedidos grupo:processadores 0 MKSTREAM'
nota "O \`0\` faz o grupo começar do início do stream. \`MKSTREAM\` cria o stream caso não exista — aqui ele já existia, então não teve efeito."

sub "12.4 – Consumindo pelo grupo"
cmd 'XREADGROUP GROUP grupo:processadores consumidor:1 COUNT 10 STREAMS stream:pedidos >'
nota "O \`>\` significa \"apenas mensagens nunca entregues a este grupo\". Repetindo o mesmo comando agora, o retorno é vazio — as duas mensagens já foram entregues:"
cmd 'XREADGROUP GROUP grupo:processadores consumidor:1 COUNT 10 STREAMS stream:pedidos >'

sub "Extra — por que o consumer group existe: entrega pendente e confirmação"
txt "Esta parte não está no roteiro, mas sem ela o consumer group não faz sentido. As mensagens entregues ficam **pendentes** até serem confirmadas com \`XACK\`:"
cmd 'XPENDING stream:pedidos grupo:processadores'
nota "Duas mensagens pendentes. Se o \`consumidor:1\` morrer agora, elas não se perdem: continuam na lista de pendências e outro consumidor pode reivindicá-las. É exatamente a garantia que o Pub/Sub não oferece."
txt "Confirmando o processamento da primeira mensagem:"
PRIMEIRO_ID=$(echo 'XRANGE stream:pedidos - + COUNT 1' | $R | head -1 | tr -d '\r')
cmd "XACK stream:pedidos grupo:processadores $PRIMEIRO_ID"
cmd 'XPENDING stream:pedidos grupo:processadores'
nota "Restou uma pendência. O \`XACK\` é o que diz \"terminei de processar\" — enquanto ele não vem, o Redis considera a mensagem em aberto."

# ===================== SECAO 13 =====================
sec "SEÇÃO 13 – Bitmaps"
txt "Bitmaps são strings manipuladas bit a bit. Servem para flags booleanas em escala."

sub "13.1 – Marcando presença"
cmds 'SETBIT presenca:2026-03-15 1001 1' 'SETBIT presenca:2026-03-15 1002 1' \
     'SETBIT presenca:2026-03-15 1003 0' \
     'GETBIT presenca:2026-03-15 1001' 'GETBIT presenca:2026-03-15 1003' \
     'BITCOUNT presenca:2026-03-15'
nota "O \`SETBIT\` devolve o valor **anterior** do bit, não o novo — por isso os três primeiros retornos são 0. O \`BITCOUNT\` conta os bits ligados: 2 presenças."
txt "O tamanho ocupado mostra por que o bitmap é interessante:"
cmd 'STRLEN presenca:2026-03-15'
nota "126 bytes para representar o estado de 1.004 usuários. O bit de índice 1003 força a string a ter ceil(1004/8) = 126 bytes, e nesse espaço cabem 1.008 flags. Uma lista de IDs presentes custaria vários bytes por usuário; o bitmap custa 1 bit."
cmd 'GETBIT presenca:2026-03-15 9999'
nota "Bit nunca escrito devolve 0, sem erro — o bitmap é conceitualmente infinito e só aloca até o maior índice usado."

# ===================== SECAO 14 =====================
sec "SEÇÃO 14 – HyperLogLog"
txt "HyperLogLog estima **cardinalidade** — quantos elementos distintos existem — com erro de cerca de 0,81% e memória fixa, sem guardar os elementos."

sub "14.1 – Visitantes únicos aproximados"
cmds 'PFADD hll:visitantes "u1" "u2" "u3" "u1" "u2"' 'PFCOUNT hll:visitantes'
nota "Cinco inserções, três valores distintos, contagem 3. As repetições de u1 e u2 não somaram."

sub "14.2 – Mesclando contadores"
cmds 'PFADD hll:dia1 "u1" "u2" "u3"' 'PFADD hll:dia2 "u3" "u4" "u5"' \
     'PFMERGE hll:total hll:dia1 hll:dia2' 'PFCOUNT hll:total'
nota "Cinco únicos: u3 aparece nos dois dias e é contado uma vez só. O \`PFMERGE\` permite somar janelas de tempo — visitantes únicos da semana a partir dos contadores diários — coisa que um \`SUM\` de contagens diárias não conseguiria fazer corretamente."
txt "O custo em memória é o argumento central desta estrutura:"
cmd 'STRLEN hll:total'
nota "Um HyperLogLog ocupa no máximo cerca de 12 KB, **independentemente** de conter 3 ou 300 milhões de elementos distintos. Com poucos elementos ele usa uma codificação esparsa e fica ainda menor, como se vê acima. Um \`SET\` com a mesma informação cresceria proporcionalmente ao número de usuários. A troca é clara: perde-se a capacidade de saber **quem** visitou e de fazer interseção, ganha-se memória constante."

# ===================== SECAO 15 =====================
sec "SEÇÃO 15 – Geoespacial"
txt "Os comandos GEO são açúcar sintático sobre um sorted set: a coordenada é convertida num geohash de 52 bits que vira o score, o que permite busca por proximidade usando a ordenação do zset."

sub "15.1 – Inserindo pontos"
cmds 'GEOADD cidades:df -47.8825 -15.7942 "Brasilia"' \
     'GEOADD cidades:df -48.0770 -15.6014 "Taguatinga"' \
     'GEOADD cidades:df -47.9292 -15.7801 "LagoSul"'
nota "A ordem dos argumentos é **longitude antes de latitude** — o inverso do que se costuma escrever ao citar coordenadas. Inverter os dois é o erro clássico e coloca o ponto em outro continente, sem erro algum do Redis."

sub "15.2 – Consultando distância"
cmds 'GEODIST cidades:df "Brasilia" "Taguatinga" km' 'GEODIST cidades:df "Brasilia" "LagoSul" km'

sub "15.3 – Buscando por raio"
cmd 'GEOSEARCH cidades:df FROMLONLAT -47.8825 -15.7942 BYRADIUS 30 km WITHDIST'
nota "As três cidades estão dentro de 30 km, com a distância de cada uma. Reduzindo o raio para 10 km, Taguatinga fica de fora:"
cmd 'GEOSEARCH cidades:df FROMLONLAT -47.8825 -15.7942 BYRADIUS 10 km WITHDIST'
txt "Confirmando que por baixo é mesmo um sorted set:"
cmds 'TYPE cidades:df' 'ZSCORE cidades:df "Brasilia"'
nota "O tipo é \`zset\` e o score é o geohash de 52 bits da coordenada."

# ===================== SECAO 16 =====================
sec "SEÇÃO 16 – Memória e eviction"

sub "16.1 – Consultar memória"
info "memory" "used_memory:|used_memory_human|used_memory_peak_human|used_memory_dataset:|maxmemory:|maxmemory_human|maxmemory_policy"

sub "16.2 – Ver política de eviction"
cmds 'CONFIG GET maxmemory' 'CONFIG GET maxmemory-policy'
nota "\`maxmemory 0\` significa sem limite: o Redis usa memória até o sistema operacional recusar. A política padrão \`noeviction\` faz o servidor **recusar escritas** com erro quando o limite é atingido, em vez de descartar chaves."

sub "16.3 – Configurar limites de memória em tempo real"
cmds 'CONFIG SET maxmemory 512mb' 'CONFIG SET maxmemory-policy allkeys-lru' \
     'CONFIG GET maxmemory' 'CONFIG GET maxmemory-policy'
info "memory" "maxmemory:|maxmemory_human|maxmemory_policy"
nota "O roteiro observa que \`CONFIG SET\` aplica imediatamente mas **não persiste** após reinicialização. A Seção 19 reinicia o contêiner — e aproveitamos para comprovar essa afirmação na prática."

sub "16.4 – Políticas de eviction"
txt "| Política | Comportamento ao atingir \`maxmemory\` |"
txt "|---|---|"
txt "| \`noeviction\` | Recusa novas escritas com erro. Leituras continuam funcionando. Padrão. |"
txt "| \`allkeys-lru\` | Descarta as chaves usadas há mais tempo, **com ou sem TTL**. Adequado para cache puro. |"
txt "| \`volatile-lru\` | Descarta por LRU, mas **apenas entre chaves com TTL**. Protege dados permanentes. |"
txt "| \`allkeys-random\` | Descarta qualquer chave ao acaso. Mais barato, menos eficaz. |"
txt "| \`volatile-ttl\` | Descarta primeiro as chaves cujo TTL está mais próximo de vencer. |"
nota "A escolha depende de o Redis ser cache puro ou guardar algo que não pode sumir. Se a instância mistura cache e dado permanente, \`allkeys-lru\` pode descartar o dado permanente sem avisar — nesse cenário \`volatile-lru\` é a escolha segura, desde que todo dado descartável realmente tenha TTL."

# ===================== SECAO 17 =====================
sec "SEÇÃO 17 – Transações com MULTI / EXEC"

sub "17.1 – Exemplo de transação"
txt "Os comandos precisam rodar **na mesma conexão** — é uma propriedade da sessão, não do servidor:"
sessao 'MULTI' 'SET pedido:1 "aberto"' 'INCR pedidos:contador' 'LPUSH fila:pedidos "pedido:1"' 'EXEC'
nota "Cada comando dentro do bloco responde \`QUEUED\` — nada foi executado ainda. O \`EXEC\` dispara todos de uma vez e devolve um array com o resultado de cada um, na ordem."

sub "Por que a conexão importa"
txt "Enviando os mesmos comandos em conexões separadas, a transação **não existe**:"
cmds 'MULTI' 'INCR pedidos:contador' 'EXEC'
nota "O \`MULTI\` abriu e morreu junto com sua conexão; o \`INCR\` executou solto, fora de qualquer transação, e o \`EXEC\` falhou com \`ERR EXEC without MULTI\`. Numa aplicação real, isso acontece quando os comandos saem de um pool que devolve conexões diferentes a cada chamada."

sub "17.2 – Transferência entre saldos"
cmds 'SET saldo:conta1 500' 'SET saldo:conta2 300'
sessao 'MULTI' 'DECRBY saldo:conta1 100' 'INCRBY saldo:conta2 100' 'EXEC'
cmds 'GET saldo:conta1' 'GET saldo:conta2'
nota "Caso clássico: débito e crédito ocorrem como unidade, sem que outro cliente veja o estado intermediário em que o dinheiro saiu de uma conta e ainda não entrou na outra."

sub "17.3 – Cancelando transação antes de executar"
sessao 'MULTI' 'SET teste:1 "x"' 'SET teste:2 "y"' 'DISCARD'
cmds 'EXISTS teste:1' 'EXISTS teste:2'
nota "O \`DISCARD\` descartou a fila inteira: nenhuma das duas chaves foi criada."

sub "17.4 – Inspecionando resultado"
cmds 'GET pedido:1' 'GET pedidos:contador' 'LRANGE fila:pedidos 0 -1'

sub "O limite do MULTI/EXEC: não há rollback"
txt "Se um comando enfileirado falhar **em tempo de execução**, os outros são aplicados assim mesmo:"
cmds 'SET nao:e:numero "texto"'
sessao 'MULTI' 'INCR nao:e:numero' 'SET marcador:pos:erro "fui gravado"' 'EXEC'
cmds 'GET marcador:pos:erro' 'GET nao:e:numero'
nota "O \`INCR\` sobre uma string não numérica falhou dentro do \`EXEC\`, mas o \`SET\` seguinte foi aplicado e a chave \`marcador:pos:erro\` existe. É a diferença central para um banco relacional: o \`MULTI/EXEC\` garante **isolamento e atomicidade de envio**, não rollback. Erros de sintaxe, ao contrário, são detectados no enfileiramento e aí sim abortam a transação inteira."

# ===================== SECAO 18 =====================
sec "SEÇÃO 18 – Script Lua com EVAL"
txt "Um script Lua roda no servidor como **uma única unidade atômica**: nenhum outro comando é intercalado durante a execução."

sub "18.1 – Rate limit atômico com INCR + EXPIRE"
cmd "EVAL \"local v = redis.call('INCR', KEYS[1]) if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end return v\" 1 rl:ip:192.168.0.10 60"
txt "Executando várias vezes, como o roteiro pede:"
cmds "EVAL \"local v = redis.call('INCR', KEYS[1]) if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end return v\" 1 rl:ip:192.168.0.10 60" \
     "EVAL \"local v = redis.call('INCR', KEYS[1]) if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end return v\" 1 rl:ip:192.168.0.10 60" \
     'TTL rl:ip:192.168.0.10'
nota "O contador sobe a cada chamada, mas o \`EXPIRE\` só é aplicado quando \`v == 1\` — isto é, na primeira requisição da janela. O TTL não é renovado nas chamadas seguintes, então a janela de 60 s conta a partir do primeiro acesso."
txt "Comparando com a versão da Seção 10.3, que usava dois comandos separados:"
txt "| | Seção 10.3 (\`INCR\` + \`EXPIRE\`) | Seção 18 (script Lua) |"
txt "|---|---|---|"
txt "| Idas ao servidor | 2 | 1 |"
txt "| Atomicidade | Não — há um instante entre os dois comandos | Sim — o script é indivisível |"
txt "| Risco | Se o processo cair entre o \`INCR\` e o \`EXPIRE\`, a chave fica **sem TTL** e o usuário é bloqueado para sempre | Nenhum: ou tudo executa, ou nada |"
nota "Esse é o motivo real de existir o script Lua aqui — não é economizar uma viagem de rede, é eliminar uma janela de falha que produz bloqueio permanente."

# ===================== SECAO 19 =====================
sec "SEÇÃO 19 – Persistência"

sub "19.1 – Verificar AOF"
cmds 'CONFIG GET appendonly' 'CONFIG GET appendfsync' 'CONFIG GET save'
nota "O AOF foi ligado no \`docker-compose.yml\` deste laboratório (\`--appendonly yes\`), porque a imagem oficial do Redis vem com ele desligado. Sem isso, a Seção 19.1 devolveria \`no\` e o teste de persistência dependeria apenas do snapshot RDB. O \`save\` mostra os gatilhos do RDB, que continuam ativos — as duas formas de persistência convivem."

sub "19.2 – Criar dado para teste"
cmds 'SET persist:test "ok"' 'GET persist:test' 'DBSIZE'

sub "19.3 – Reiniciar container"
shell "docker restart redis"
# espera o servico voltar antes de continuar
for i in $(seq 1 30); do
  docker exec redis redis-cli PING >/dev/null 2>&1 && break
  sleep 1
done

sub "19.4 – Validar persistência"
cmds 'PING' 'GET persist:test' 'DBSIZE'
nota "O dado sobreviveu ao reinício. Com AOF ligado, o Redis reconstrói o estado relendo o log de comandos de escrita."
txt "E aproveitando o reinício para comprovar a observação da Seção 16.3 — que o \`CONFIG SET\` não persiste:"
cmds 'CONFIG GET maxmemory' 'CONFIG GET maxmemory-policy'
nota "Confirmado: \`maxmemory\` voltou a 0 e a política a \`noeviction\`. Os 512 MB e o \`allkeys-lru\` configurados na Seção 16.3 desapareceram, porque o \`CONFIG SET\` altera apenas a memória do processo. Para valer após reinício, a configuração precisa estar no \`redis.conf\` ou nos argumentos do contêiner — que é onde este laboratório colocou o \`--appendonly yes\`."
info "persistence" "^aof_enabled|^aof_last_bgrewrite_status|^aof_last_write_status|^rdb_last_bgsave_status|^loading:"

sub "19.5 – RDB e AOF lado a lado"
txt "| | RDB | AOF |"
txt "|---|---|---|"
txt "| O que grava | Snapshot binário do dataset inteiro | Cada comando de escrita, em sequência |"
txt "| Quando grava | Em intervalos (\`save\`) ou sob demanda | Continuamente, com \`fsync\` conforme \`appendfsync\` |"
txt "| Tamanho em disco | Menor, formato compacto | Maior, cresce até o rewrite |"
txt "| Recuperação | Rápida: carrega o arquivo de uma vez | Mais lenta: reexecuta o log |"
txt "| Perda possível | Tudo desde o último snapshot | Até 1 segundo com \`appendfsync everysec\` |"
nota "Não é escolha excludente: muitos ambientes mantêm os dois, usando o RDB como backup compacto para cópia e o AOF como garantia de durabilidade. É a configuração deste laboratório."

# ===================== SECAO 20 =====================
sec "SEÇÃO 20 – Exercício integrador"
txt "Mini cenário de aplicação, com uma estrutura diferente para cada necessidade."

sub "Uma colisão de tipo antes de começar"
txt "O primeiro comando do exercício integrador, executado exatamente como o roteiro pede, **falha**:"
cmd 'HSET user:1001 nome "João" idade 40 cidade "Brasília"'
cmds 'TYPE user:1001' 'GET user:1001'
nota "A causa: a Seção 5.1 da Parte 1 já havia criado \`user:1001\` como **string** (\`SET user:1001 \"João\"\` seguido de \`APPEND \" Silva\"\`), e a Seção 20 tenta usar a mesma chave como **hash**. No Redis a chave carrega um tipo, e um comando do tipo errado é recusado com \`WRONGTYPE\` — não há conversão automática nem sobrescrita. O roteiro reaproveita o nome \`user:1001\` em duas seções com estruturas diferentes, e a lista de limpeza da Seção 23 não apaga essa chave entre uma e outra."
txt "Removendo a chave para que o exercício possa prosseguir — este \`DEL\` não está no roteiro:"
cmds 'DEL user:1001' 'EXISTS user:1001'
nota "Lição prática: \`SET\` sobrescreve qualquer chave sem reclamar, mas \`HSET\`, \`LPUSH\`, \`SADD\` e \`ZADD\` exigem que a chave não exista ou já seja do tipo certo. Por isso o prefixo padronizado importa — \`user:1001\` como string de nome e \`user:1001\` como hash de cadastro deveriam ter nomes distintos, por exemplo \`user:nome:1001\` e \`user:1001\`."

sub "O cenário, agora executando"
SUBOUT=$(mktemp)
docker exec redis redis-cli SUBSCRIBE canal:usuarios > "$SUBOUT" 2>&1 &
SUBPID=$!
sleep 2
cmds 'HSET user:1001 nome "João" idade 40 cidade "Brasília"' \
     'SET session:1001 "token-abc" EX 120' \
     'SET acessos:user:1001 0' 'INCR acessos:user:1001' \
     'LPUSH fila:cadastros "user:1001"' \
     'ZADD ranking:gamificacao 100 "joao"' \
     'PUBLISH canal:usuarios "Novo cadastro user:1001"' \
     'XADD stream:usuarios * evento cadastro usuario 1001'
sleep 1
kill $SUBPID 2>/dev/null; wait $SUBPID 2>/dev/null
{ echo ""; echo "**O assinante de \`canal:usuarios\`, inscrito antes da publicação, recebeu:**"; echo ""; echo '```'
  cat "$SUBOUT"; echo '```'; } >> "$OUT"
rm -f "$SUBOUT"
txt "Conferindo o estado final de cada estrutura:"
cmds 'HGETALL user:1001' 'GET session:1001' 'TTL session:1001' \
     'GET acessos:user:1001' 'LRANGE fila:cadastros 0 -1' \
     'ZREVRANGE ranking:gamificacao 0 -1 WITHSCORES' \
     'XRANGE stream:usuarios - +'

sub "Respostas às perguntas do roteiro"
txt "**Qual estrutura foi usada em cada caso?**"
txt "| Necessidade | Estrutura | Por quê |"
txt "|---|---|---|"
txt "| Usuário | \`hash\` | Entidade com campos nomeados, atualizáveis isoladamente |"
txt "| Sessão | \`string\` com TTL | Valor único que precisa expirar sozinho |"
txt "| Contador de acessos | \`string\` com \`INCR\` | Incremento atômico, sem ler-somar-gravar |"
txt "| Fila de processamento | \`list\` | Ordem de inserção, consumo por uma ponta |"
txt "| Ranking | \`sorted set\` | Ordenação automática por score |"
txt "| Notificação | Pub/Sub | Aviso efêmero para quem estiver ouvindo agora |"
txt "| Eventos | \`stream\` | Histórico persistente, com ID e confirmação |"
txt "**Em quais situações o TTL é importante?** Em todo dado cuja validade é temporária e cuja ausência não é erro: cache, sessão, token, rate limit, lock. O TTL substitui rotina de limpeza — sem ele, a memória cresce indefinidamente e alguém precisa escrever um job para apagar o que venceu."
txt "**Quando usar Pub/Sub e quando usar Streams?** Pub/Sub quando a mensagem só interessa a quem está conectado naquele instante e perdê-la é aceitável — atualização de tela, invalidação de cache. Stream quando é preciso histórico, releitura, confirmação de processamento ou vários consumidores dividindo a carga. A prova está na Seção 11: publicar sem assinante devolve 0 e a mensagem some."
txt "**Quando uma list basta e quando um stream é melhor?** A list basta para fila simples de trabalho, em que o item é consumido uma vez e some. O stream é melhor quando se quer saber o que passou pela fila, reprocessar, ou garantir que uma mensagem não se perca se o consumidor morrer no meio — o \`XPENDING\` da Seção 12 mostra isso."
txt "**Por que sorted set é adequado para ranking?** Porque mantém a ordenação a cada escrita, com custo logarítmico, e responde tanto \"quais são os cinco primeiros\" (\`ZREVRANGE 0 4\`) quanto \"em que posição está o jogador X\" (\`ZREVRANK\`) sem varrer a estrutura. Com uma list seria preciso reordenar a cada atualização."

# ===================== SECAO 22 =====================
sec "SEÇÃO 22 – Boas práticas"
nota "O roteiro salta da Seção 20 para a 22 — não há Seção 21."
txt "**1) Padronizar chaves com prefixos.** \`user:1001\`, \`session:abc123\`, \`cache:pagina:/home\`. O Redis não tem tabelas nem coleções: o prefixo é a única estrutura de organização que existe, e é o que o RedisInsight usa para montar a árvore de chaves."
txt "**2) Evitar \`KEYS *\` em produção.** Ele percorre todo o keyspace e bloqueia o servidor. \`SCAN\` faz a mesma coisa em fatias, devolvendo um cursor — como demonstrado na Seção 3.4."
txt "**3) Usar TTL em dados temporários.** Cache, sessão, token e rate limit. Sem TTL, a limpeza vira responsabilidade da aplicação."
txt "**4) Escolher a estrutura correta.** \`string\` para valor simples, \`hash\` para objeto, \`list\` para fila, \`set\` para unicidade, \`zset\` para ranking, \`stream\` para eventos persistentes."
txt "**5) Entender a persistência.** RDB para snapshot compacto, AOF para durabilidade — a Seção 19 comparou os dois."
txt "**6) Monitorar memória, TTL e crescimento de chaves.** \`INFO memory\`, \`DBSIZE\` e a política de eviction. Uma chave sem TTL que deveria ter é um vazamento de memória lento."
txt "**7) Para operações compostas, usar \`MULTI/EXEC\` ou Lua.** Lembrando o limite da Seção 17: \`MULTI/EXEC\` não faz rollback. Quando a lógica exige uma decisão no meio — ler um valor e decidir o que gravar —, o script Lua é a ferramenta certa, porque o \`MULTI\` enfileira sem executar e não permite ramificar."

# ===================== SECAO 23 =====================
sec "SEÇÃO 23 – Limpeza final do laboratório"
txt "Executando exatamente a lista de \`DEL\` do roteiro:"
cmds 'DBSIZE' \
     'DEL visitas saldo codigo' \
     'DEL aluno:1 aluno:2 aluno:3' \
     'DEL fila:processamento fila:pedidos fila:etl fila:emails' \
     'DEL curso:BI curso:DS interesses:python interesses:redis' \
     'DEL ranking:pontos ranking:jogo ranking:turma ranking:gamificacao' \
     'DEL rl:user:42 rl:ip:192.168.0.10' \
     'DEL cache:home cache:pagina:/home cache:consulta:clientes' \
     'DEL session:abc123 session:user:1001 session:1001' \
     'DEL persist:test' \
     'DEL presenca:2026-03-15' \
     'DEL hll:visitantes hll:dia1 hll:dia2 hll:total' \
     'DEL stream:pedidos stream:usuarios' \
     'DEL cidades:df' \
     'DEL saldo:conta1 saldo:conta2' \
     'DBSIZE'
nota "Cada \`DEL\` devolve quantas chaves foram realmente removidas — os zeros são chaves que já não existiam, como \`cache:pagina:/home\`, apagada na Seção 4.5."
txt "Verificando o que **sobrou** depois da limpeza do roteiro:"
cmd 'KEYS *'
nota "Sobraram 14 chaves. A maioria vem de seções do **próprio roteiro** que ficaram fora da lista de \`DEL\`: \`user:2001\`, \`user:2002\` e \`user:2003\` (Seção 5.2), \`equipe:sorteio\` (6.5), \`pedido:1\` e \`pedidos:contador\` (17.1), \`user:1001\`, \`acessos:user:1001\` e \`fila:cadastros\` (Seção 20). As demais são dos exercícios e das demonstrações extras desta parte. A lição não é que o roteiro errou — é que limpar por lista fixa não escala: basta alguém acrescentar uma chave em qualquer ponto do código para a lista ficar desatualizada, e nada avisa. Em produção o caminho é prefixo padronizado mais \`SCAN\`, ou TTL em tudo que é descartável."
txt "Removendo o restante por prefixo, com \`SCAN\` em vez de \`KEYS\`:"
shell "docker exec redis sh -c \"redis-cli --scan --pattern 'user:*' | xargs -r redis-cli DEL\""
shell "docker exec redis sh -c \"redis-cli --scan --pattern '*' | xargs -r redis-cli DEL\""
cmds 'DBSIZE' 'KEYS *'
nota "Banco zerado. O \`--scan\` do \`redis-cli\` faz a iteração incremental automaticamente, sem bloquear o servidor — é a forma correta de apagar em massa."

txt "---"
txt "Fim do laboratório. O ambiente continua no ar; para derrubá-lo, \`docker compose down\` na pasta \`lab03-redis/\`."
echo "PARTE 2 CONCLUIDA -> $OUT"
