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
txt "Cobre as Seções 12 a 23. Continuei no mesmo banco da Parte 1, então as chaves criadas lá ainda estão no banco e aparecem na limpeza da Seção 23."

# ===================== SECAO 12 =====================
sec "SEÇÃO 12 – Streams"
txt "Stream é um log append-only. Diferente do Pub/Sub da Seção 11, a mensagem fica guardada e dá para ler depois, quantas vezes precisar."

sub "12.1 – Inserindo eventos"
cmds 'XADD stream:pedidos * pedido_id 1001 status novo cliente "Ana"' \
     'XADD stream:pedidos * pedido_id 1002 status pago cliente "Bruno"'
nota "O * deixa o Redis gerar o ID, no formato timestamp-sequência. O primeiro número é a hora da inserção em milissegundos e o segundo desempata eventos gravados no mesmo milissegundo."

sub "12.2 – Lendo eventos"
cmd 'XRANGE stream:pedidos - +'
cmd 'XREAD COUNT 10 STREAMS stream:pedidos 0'
nota "O 0 faz ler desde o começo. A leitura não consome: os eventos continuam no stream, diferente de uma list com RPOP."
cmd 'XLEN stream:pedidos'

sub "12.3 – Consumer group"
cmd 'XGROUP CREATE stream:pedidos grupo:processadores 0 MKSTREAM'
nota "O 0 faz o grupo começar do início do stream. O MKSTREAM criaria o stream se ele não existisse, mas aqui já existia."

sub "12.4 – Consumindo pelo grupo"
cmd 'XREADGROUP GROUP grupo:processadores consumidor:1 COUNT 10 STREAMS stream:pedidos >'
nota "O > pede só as mensagens que o grupo nunca recebeu. Rodando de novo o retorno vem vazio, porque as duas já foram entregues."
cmd 'XREADGROUP GROUP grupo:processadores consumidor:1 COUNT 10 STREAMS stream:pedidos >'

sub "Extra: entrega pendente e confirmação"
txt "Isso não está no roteiro, mas sem ver a pendência o consumer group não faz muito sentido. As mensagens entregues ficam pendentes até o XACK:"
cmd 'XPENDING stream:pedidos grupo:processadores'
nota "Duas pendentes. Se o consumidor:1 morrer agora elas não somem, ficam na lista de pendências e outro consumidor pode assumir. É o que o Pub/Sub não faz."
txt "Confirmando o processamento da primeira mensagem:"
PRIMEIRO_ID=$(echo 'XRANGE stream:pedidos - + COUNT 1' | $R | head -1 | tr -d '\r')
cmd "XACK stream:pedidos grupo:processadores $PRIMEIRO_ID"
cmd 'XPENDING stream:pedidos grupo:processadores'
nota "Sobrou uma pendente. Enquanto o XACK não vem, o Redis considera a mensagem em aberto."

# ===================== SECAO 13 =====================
sec "SEÇÃO 13 – Bitmaps"
txt "Bitmap é uma string manipulada bit a bit, usada para marcar flag booleana de muita gente ao mesmo tempo."

sub "13.1 – Marcando presença"
cmds 'SETBIT presenca:2026-03-15 1001 1' 'SETBIT presenca:2026-03-15 1002 1' \
     'SETBIT presenca:2026-03-15 1003 0' \
     'GETBIT presenca:2026-03-15 1001' 'GETBIT presenca:2026-03-15 1003' \
     'BITCOUNT presenca:2026-03-15'
nota "O SETBIT devolve o valor anterior do bit, não o novo, por isso os três primeiros vieram 0. O BITCOUNT contou 2 bits ligados."
txt "O tamanho ocupado explica por que vale a pena:"
cmd 'STRLEN presenca:2026-03-15'
nota "126 bytes para 1.004 usuários. O bit 1003 obriga a string a ter ceil(1004/8) = 126 bytes, e nesse espaço cabem 1.008 flags. Guardando os IDs numa lista seria vários bytes por usuário."
cmd 'GETBIT presenca:2026-03-15 9999'

# ===================== SECAO 14 =====================
sec "SEÇÃO 14 – HyperLogLog"
txt "O HyperLogLog estima quantos elementos distintos existem, com erro de cerca de 0,81% e memória fixa, sem guardar os elementos."

sub "14.1 – Visitantes únicos aproximados"
cmds 'PFADD hll:visitantes "u1" "u2" "u3" "u1" "u2"' 'PFCOUNT hll:visitantes'
nota "Cinco inserções e contagem 3. As repetições de u1 e u2 não somaram."

sub "14.2 – Mesclando contadores"
cmds 'PFADD hll:dia1 "u1" "u2" "u3"' 'PFADD hll:dia2 "u3" "u4" "u5"' \
     'PFMERGE hll:total hll:dia1 hll:dia2' 'PFCOUNT hll:total'
nota "Deu 5 porque o u3 está nos dois dias e conta uma vez. Somando as contagens diárias daria 6, errado. O PFMERGE resolve isso quando preciso dos únicos da semana a partir dos contadores de cada dia."
txt "O espaço ocupado:"
cmd 'STRLEN hll:total'
nota "O HyperLogLog para de crescer em torno de 12 KB, tendo 3 ou milhões de valores distintos. Aqui deu 31 bytes porque com poucos elementos ele usa codificação esparsa. Em compensação não dá para perguntar se um usuário específico está lá nem fazer interseção."

# ===================== SECAO 15 =====================
sec "SEÇÃO 15 – Geoespacial"
txt "Os comandos GEO são uma camada em cima do sorted set: a coordenada vira um geohash de 52 bits usado como score, e é a ordenação desse score que permite buscar por proximidade."

sub "15.1 – Inserindo pontos"
cmds 'GEOADD cidades:df -47.8825 -15.7942 "Brasilia"' \
     'GEOADD cidades:df -48.0770 -15.6014 "Taguatinga"' \
     'GEOADD cidades:df -47.9292 -15.7801 "LagoSul"'
nota "A ordem é longitude e depois latitude, ao contrário de como se costuma escrever coordenada. Se inverter, o Redis aceita sem reclamar e o ponto vai parar em outro lugar do mundo."

sub "15.2 – Consultando distância"
cmds 'GEODIST cidades:df "Brasilia" "Taguatinga" km' 'GEODIST cidades:df "Brasilia" "LagoSul" km'

sub "15.3 – Buscando por raio"
cmd 'GEOSEARCH cidades:df FROMLONLAT -47.8825 -15.7942 BYRADIUS 30 km WITHDIST'
txt "As três estão dentro de 30 km. Baixando o raio para 10 km, Taguatinga sai:"
cmd 'GEOSEARCH cidades:df FROMLONLAT -47.8825 -15.7942 BYRADIUS 10 km WITHDIST'
txt "Conferindo que por baixo é mesmo um sorted set:"
cmds 'TYPE cidades:df' 'ZSCORE cidades:df "Brasilia"'
nota "O TYPE devolveu zset. Os comandos GEO são uma camada em cima do sorted set: a coordenada vira um geohash de 52 bits que é usado como score."

# ===================== SECAO 16 =====================
sec "SEÇÃO 16 – Memória e eviction"

sub "16.1 – Consultar memória"
info "memory" "used_memory:|used_memory_human|used_memory_peak_human|used_memory_dataset:|maxmemory:|maxmemory_human|maxmemory_policy"

sub "16.2 – Ver política de eviction"
cmds 'CONFIG GET maxmemory' 'CONFIG GET maxmemory-policy'
nota "maxmemory 0 é sem limite, o Redis usa memória até o sistema operacional recusar. A política padrão noeviction recusa escrita nova quando bate o limite, em vez de apagar chave."

sub "16.3 – Configurar limites de memória em tempo real"
cmds 'CONFIG SET maxmemory 512mb' 'CONFIG SET maxmemory-policy allkeys-lru' \
     'CONFIG GET maxmemory' 'CONFIG GET maxmemory-policy'
info "memory" "maxmemory:|maxmemory_human|maxmemory_policy"
nota "O roteiro diz que o CONFIG SET não persiste depois de reiniciar. A Seção 19 reinicia o contêiner, então aproveitei para conferir isso lá."

sub "16.4 – Políticas de eviction"
txt "| Política | Comportamento ao atingir \`maxmemory\` |"
txt "|---|---|"
txt "| \`noeviction\` | Recusa novas escritas com erro. Leituras continuam funcionando. Padrão. |"
txt "| \`allkeys-lru\` | Descarta as chaves usadas há mais tempo, **com ou sem TTL**. Adequado para cache puro. |"
txt "| \`volatile-lru\` | Descarta por LRU, mas **apenas entre chaves com TTL**. Protege dados permanentes. |"
txt "| \`allkeys-random\` | Descarta qualquer chave ao acaso. Mais barato, menos eficaz. |"
txt "| \`volatile-ttl\` | Descarta primeiro as chaves cujo TTL está mais próximo de vencer. |"
nota "Se a instância é só cache, allkeys-lru serve. Se ela mistura cache com dado que não pode sumir, o allkeys-lru apaga o dado permanente sem avisar, e aí o certo é volatile-lru com TTL em tudo que é descartável."

# ===================== SECAO 17 =====================
sec "SEÇÃO 17 – Transações com MULTI / EXEC"

sub "17.1 – Exemplo de transação"
txt "Os comandos precisam rodar na mesma conexão, porque a transação é da sessão e não do servidor:"
sessao 'MULTI' 'SET pedido:1 "aberto"' 'INCR pedidos:contador' 'LPUSH fila:pedidos "pedido:1"' 'EXEC'
nota "Dentro do bloco cada comando responde QUEUED e nada roda ainda. O EXEC dispara todos e devolve um array com o resultado de cada um, na ordem."

sub "Por que a conexão importa"
txt "Mandando os mesmos comandos em conexões separadas, a transação não existe:"
cmds 'MULTI' 'INCR pedidos:contador' 'EXEC'
nota "O MULTI morreu junto com a conexão dele. O INCR executou solto e o EXEC caiu em outra conexão, que nunca abriu transação. Numa aplicação isso acontece quando o pool entrega conexões diferentes a cada comando."

sub "17.2 – Transferência entre saldos"
cmds 'SET saldo:conta1 500' 'SET saldo:conta2 300'
sessao 'MULTI' 'DECRBY saldo:conta1 100' 'INCRBY saldo:conta2 100' 'EXEC'
cmds 'GET saldo:conta1' 'GET saldo:conta2'
nota "Débito e crédito saíram juntos, sem outro cliente ver o estado no meio, com o dinheiro fora de uma conta e ainda não na outra."

sub "17.3 – Cancelando transação antes de executar"
sessao 'MULTI' 'SET teste:1 "x"' 'SET teste:2 "y"' 'DISCARD'
cmds 'EXISTS teste:1' 'EXISTS teste:2'

sub "17.4 – Inspecionando resultado"
cmds 'GET pedido:1' 'GET pedidos:contador' 'LRANGE fila:pedidos 0 -1'

sub "O limite do MULTI/EXEC: não há rollback"
txt "Se um comando da fila falhar na hora de executar, os outros são aplicados mesmo assim:"
cmds 'SET nao:e:numero "texto"'
sessao 'MULTI' 'INCR nao:e:numero' 'SET marcador:pos:erro "fui gravado"' 'EXEC'
cmds 'GET marcador:pos:erro' 'GET nao:e:numero'
nota "O INCR falhou dentro do EXEC porque a chave não é número, mas o SET seguinte foi aplicado assim mesmo e a chave marcador:pos:erro existe. Então o MULTI/EXEC garante que ninguém se intromete no meio, mas não desfaz nada. Num banco relacional o erro derrubaria a transação inteira."

# ===================== SECAO 18 =====================
sec "SEÇÃO 18 – Script Lua com EVAL"
txt "O script Lua roda no servidor como uma unidade só, sem nenhum outro comando entrar no meio."

sub "18.1 – Rate limit atômico com INCR + EXPIRE"
cmd "EVAL \"local v = redis.call('INCR', KEYS[1]) if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end return v\" 1 rl:ip:192.168.0.10 60"
txt "Rodando várias vezes, como o roteiro pede:"
cmds "EVAL \"local v = redis.call('INCR', KEYS[1]) if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end return v\" 1 rl:ip:192.168.0.10 60" \
     "EVAL \"local v = redis.call('INCR', KEYS[1]) if v == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end return v\" 1 rl:ip:192.168.0.10 60" \
     'TTL rl:ip:192.168.0.10'
nota "O contador sobe toda vez, mas o EXPIRE só roda quando v == 1, ou seja na primeira requisição da janela. O TTL não é renovado depois, então os 60 segundos contam do primeiro acesso."
txt "Comparando com a Seção 10.3, que usava dois comandos separados:"
txt "| | Seção 10.3 (\`INCR\` + \`EXPIRE\`) | Seção 18 (script Lua) |"
txt "|---|---|---|"
txt "| Idas ao servidor | 2 | 1 |"
txt "| Atomicidade | Não, há um instante entre os dois comandos | Sim, o script é indivisível |"
txt "| Risco | Se o processo cair entre o INCR e o EXPIRE a chave fica sem TTL e o usuário nunca mais é liberado | Nenhum, ou executa tudo ou nada |"
nota "O ganho não é economizar uma viagem de rede, é que o script roda inteiro no servidor e não existe mais o instante sem TTL que eu vi na Seção 10.3."

# ===================== SECAO 19 =====================
sec "SEÇÃO 19 – Persistência"

sub "19.1 – Verificar AOF"
cmds 'CONFIG GET appendonly' 'CONFIG GET appendfsync' 'CONFIG GET save'
nota "Liguei o AOF no docker-compose com --appendonly yes, porque a imagem oficial vem com ele desligado. Sem isso o CONFIG GET aqui devolveria no e o teste de persistência dependeria só do snapshot RDB. O save mostra que os gatilhos do RDB continuam ativos, os dois funcionam juntos."

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
nota "O dado sobreviveu ao reinício. Com o AOF ligado o Redis reconstrói o estado relendo o log de escritas."
txt "Aproveitei o reinício para conferir o que a Seção 16.3 diz sobre o CONFIG SET não persistir:"
cmds 'CONFIG GET maxmemory' 'CONFIG GET maxmemory-policy'
nota "Confirmado o que o roteiro diz na 16.3: o maxmemory voltou para 0 e a política para noeviction. Os 512 MB que eu tinha configurado sumiram, porque o CONFIG SET só mexe na memória do processo. Para valer depois do reinício tem que estar no redis.conf ou nos argumentos do contêiner, que é onde coloquei o --appendonly yes."
info "persistence" "^aof_enabled|^aof_last_bgrewrite_status|^aof_last_write_status|^rdb_last_bgsave_status|^loading:"

sub "19.5 – RDB e AOF lado a lado"
txt "| | RDB | AOF |"
txt "|---|---|---|"
txt "| O que grava | Snapshot binário do dataset inteiro | Cada comando de escrita, em sequência |"
txt "| Quando grava | Em intervalos (\`save\`) ou sob demanda | Continuamente, com \`fsync\` conforme \`appendfsync\` |"
txt "| Tamanho em disco | Menor, formato compacto | Maior, cresce até o rewrite |"
txt "| Recuperação | Rápida: carrega o arquivo de uma vez | Mais lenta: reexecuta o log |"
txt "| Perda possível | Tudo desde o último snapshot | Até 1 segundo com \`appendfsync everysec\` |"
nota "Não precisa escolher um. Aqui os dois estão ligados: RDB como snapshot para cópia e AOF para durabilidade."

# ===================== SECAO 20 =====================
sec "SEÇÃO 20 – Exercício integrador"
txt "Cenário com uma estrutura diferente para cada necessidade."

sub "Uma colisão de tipo antes de começar"
txt "O primeiro comando do exercício integrador, rodando exatamente como o roteiro pede, falha:"
cmd 'HSET user:1001 nome "João" idade 40 cidade "Brasília"'
cmds 'TYPE user:1001' 'GET user:1001'
nota "A Seção 5.1 da Parte 1 criou user:1001 como string, com SET e APPEND, e a Seção 20 tenta usar a mesma chave como hash. No Redis a chave tem tipo e comando de outro tipo é recusado, não converte nem sobrescreve. A lista de limpeza da Seção 23 também não apaga essa chave entre uma seção e outra."
txt "Apaguei a chave para conseguir seguir. Esse DEL não está no roteiro:"
cmds 'DEL user:1001' 'EXISTS user:1001'
nota "O SET sobrescreve qualquer chave sem reclamar, mas HSET, LPUSH, SADD e ZADD exigem que a chave não exista ou já seja do tipo certo. Por isso não vale reaproveitar nome: user:1001 como string e como hash deveriam ser chaves diferentes."

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
{ echo ""; echo "**O assinante de canal:usuarios, que eu inscrevi antes de publicar, recebeu:**"; echo ""; echo '```'
  cat "$SUBOUT"; echo '```'; } >> "$OUT"
rm -f "$SUBOUT"
txt "Estado final de cada estrutura:"
cmds 'HGETALL user:1001' 'GET session:1001' 'TTL session:1001' \
     'GET acessos:user:1001' 'LRANGE fila:cadastros 0 -1' \
     'ZREVRANGE ranking:gamificacao 0 -1 WITHSCORES' \
     'XRANGE stream:usuarios - +'

sub "Respostas às perguntas do roteiro"
txt "**Qual estrutura foi usada em cada caso?**"
txt "| Caso | Estrutura |"
txt "|---|---|"
txt "| Usuário | hash |"
txt "| Sessão | string com TTL |"
txt "| Contador de acessos | string com INCR |"
txt "| Fila de cadastros | list |"
txt "| Ranking | sorted set |"
txt "| Notificação | Pub/Sub |"
txt "| Eventos | stream |"
txt "**Em quais situações o TTL é importante?** Em dado temporário, que pode sumir sem ser erro: cache, sessão, token, rate limit e lock. O TTL evita ter que escrever uma rotina para limpar o que venceu."
txt "**Quando usar Pub/Sub e quando usar Streams?** Pub/Sub quando a mensagem só interessa a quem está conectado na hora e perder não é problema. Stream quando preciso de histórico, releitura ou confirmação de processamento. Na Seção 11 publiquei sem assinante e o retorno foi 0: a mensagem se perdeu."
txt "**Quando uma list basta e quando um stream é melhor?** A list basta para fila simples, em que o item é consumido uma vez e some. O stream é melhor quando preciso saber o que passou pela fila, reprocessar, ou garantir que a mensagem não se perca se o consumidor morrer no meio, que é o que o XPENDING mostrou na Seção 12."
txt "**Por que sorted set é adequado para ranking?** Porque ele mantém a ordem a cada escrita e responde tanto o topo, com ZREVRANGE, quanto a posição de um participante, com ZREVRANK, sem varrer a estrutura. Com list eu teria que reordenar a cada atualização."

# ===================== SECAO 22 =====================
sec "SEÇÃO 22 – Boas práticas"
nota "O roteiro pula da Seção 20 para a 22, não existe Seção 21."
txt "**1) Padronizar chaves com prefixos.** user:1001, session:abc123, cache:pagina:/home. O Redis não tem tabela nem coleção, o prefixo é a única organização que existe, e é com ele que o RedisInsight monta a árvore de chaves."
txt "**2) Evitar KEYS * em produção.** Ele varre o keyspace inteiro e bloqueia o servidor. O SCAN faz o mesmo em fatias, devolvendo cursor, como na Seção 3.4."
txt "**3) Usar TTL em dado temporário.** Cache, sessão, token e rate limit."
txt "**4) Escolher a estrutura certa.** string para valor simples, hash para objeto, list para fila, set para unicidade, zset para ranking e stream para evento que precisa ficar guardado."
txt "**5) Entender a persistência.** RDB para snapshot e AOF para durabilidade, comparados na Seção 19."
txt "**6) Monitorar memória, TTL e crescimento de chaves.** INFO memory, DBSIZE e a política de eviction. Chave sem TTL que deveria ter é memória que só cresce."
txt "**7) Para operação composta, usar MULTI/EXEC ou Lua.** Lembrando que o MULTI/EXEC não desfaz nada, como vi na Seção 17. Quando preciso ler um valor e decidir o que gravar, tem que ser Lua, porque o MULTI enfileira sem executar e não dá para ramificar."

# ===================== SECAO 23 =====================
sec "SEÇÃO 23 – Limpeza final do laboratório"
txt "Rodando a lista de DEL do roteiro:"
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
nota "Cada DEL diz quantas chaves apagou. Os zeros são chaves que já não existiam, como cache:pagina:/home, que eu apaguei na Seção 4.5."
txt "Vendo o que sobrou depois da limpeza do roteiro:"
cmd 'KEYS *'
nota "Sobraram 14 chaves. A maior parte é de seção do próprio roteiro que ficou fora da lista de DEL: user:2001 a user:2003 da 5.2, equipe:sorteio da 6.5, pedido:1 e pedidos:contador da 17.1, e user:1001, acessos:user:1001 e fila:cadastros da Seção 20. O resto é dos exercícios. Limpar por lista fixa não funciona bem, qualquer chave nova em outro ponto do roteiro já deixa a lista desatualizada."
txt "Apaguei o resto por prefixo, usando SCAN em vez de KEYS:"
shell "docker exec redis sh -c \"redis-cli --scan --pattern 'user:*' | xargs -r redis-cli DEL\""
shell "docker exec redis sh -c \"redis-cli --scan --pattern '*' | xargs -r redis-cli DEL\""
cmds 'DBSIZE' 'KEYS *'
nota "Banco zerado. O --scan do redis-cli faz a iteração incremental sozinho, sem travar o servidor, então é assim que apago em massa."

txt "---"
txt "Fim do laboratório. O ambiente continua no ar, para derrubar é docker compose down na pasta lab03-redis."
echo "PARTE 2 CONCLUIDA -> $OUT"
