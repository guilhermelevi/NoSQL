#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Anexos referentes ao Lab 3 (Redis): armadilhas, exercicios, quiz, decisao, glossario."""

ARMADILHAS = [
 {'titulo': 'A chave é tipada: o exercício integrador do roteiro não roda',
  'sistema': 'Redis',
  'sintoma': 'O primeiro comando da Seção 20 falha com `WRONGTYPE Operation against a key holding the '
             'wrong kind of value`, e o exercício integrador para antes de começar.',
  'causa_raiz': 'A Seção 5.1 já havia criado `user:1001` como string (`SET` seguido de `APPEND`). A Seção '
                '20 tenta usar o mesmo nome como hash. No Redis toda chave carrega um tipo e um comando '
                'de outro tipo é recusado — não há conversão nem sobrescrita. A lista de limpeza da '
                'Seção 23 também não apaga essa chave entre uma seção e outra.',
  'diagnostico': '`TYPE user:1001` devolve `string`, e `GET user:1001` mostra o valor deixado pela Seção 5.1.',
  'correcao': 'No laboratório, `DEL user:1001` antes do `HSET` — comando que não está no roteiro. Em '
              'código de verdade, não reaproveitar o nome: `user:nome:1001` para a string e `user:1001` '
              'para o hash.',
  'licao': 'O `SET` sobrescreve qualquer chave sem reclamar, o que passa a impressão de que o Redis é '
           'permissivo com tipos. Não é: `HSET`, `LPUSH`, `SADD` e `ZADD` exigem a chave inexistente ou '
           'já do tipo certo. O erro só aparece no ambiente onde a chave antiga existir — nunca no '
           'ambiente limpo em que o código foi testado.',
  'evidencia': 'HSET user:1001 nome "João" ... -> WRONGTYPE Operation against a key holding the wrong kind of value\n'
               'TYPE user:1001                 -> string\n'
               'GET  user:1001                 -> "João Silva"'},

 {'titulo': 'A fila que processa ao contrário',
  'sistema': 'Redis',
  'sintoma': 'Uma fila de trabalhos entrega os itens na ordem inversa. Nenhum erro, nenhum log — os '
             'trabalhos mais antigos simplesmente vão sendo empurrados para o fim e podem nunca ser '
             'processados se a fila nunca esvaziar.',
  'causa_raiz': 'Inserção e consumo pela mesma ponta. `RPUSH` com `RPOP` é uma pilha (LIFO), não uma '
                'fila. A list do Redis não tem semântica própria: FIFO ou LIFO nasce da combinação de '
                'comandos escolhida.',
  'diagnostico': 'Um `LRANGE chave 0 -1` antes e depois do consumo mostra de que ponta os itens estão '
                 'saindo.',
  'correcao': '`RPUSH` para enfileirar e `LPOP` para consumir — ou `LPUSH` com `RPOP`. O que importa é '
              'que as pontas sejam opostas.',
  'licao': 'Estruturas simétricas exigem convenção explícita. Vale fixar uma combinação em todo o '
           'projeto e documentá-la, porque metade dos comandos funciona e produz o comportamento errado '
           'em silêncio.',
  'evidencia': 'RPUSH fila:etl "extrair" "transformar" "validar" "carregar" "notificar"\n'
               'RPOP fila:etl  -> "job:notificar"     (saiu o ultimo, nao o primeiro)\n'
               'RPOP fila:etl  -> "job:carregar"'},

 {'titulo': 'MULTI/EXEC não faz rollback, e a transação vive na conexão',
  'sistema': 'Redis',
  'sintoma': 'Um comando falha no meio de uma transação e os demais são aplicados assim mesmo, deixando '
             'estado parcial. Em outro cenário, a transação simplesmente não existe e o `EXEC` responde '
             '`ERR EXEC without MULTI`.',
  'causa_raiz': 'Duas propriedades distintas do modelo. Primeira: o `EXEC` executa a fila inteira e '
                'devolve um array em que cada posição pode ser resultado ou erro — não há desfazimento. '
                'Segunda: o `MULTI` abre um contexto **naquela conexão**; com um pool que entrega '
                'conexões diferentes a cada chamada, os comandos se espalham e a transação se desfaz.',
  'diagnostico': 'Inspecionar o array devolvido pelo `EXEC` posição a posição, em vez de tratar a '
                 'resposta como sucesso único. Para o problema de conexão, verificar se a biblioteca '
                 'cliente expõe transação ou conexão reservada.',
  'correcao': 'Quando a operação exige ler um valor e decidir o que escrever, usar script Lua em vez de '
              'MULTI/EXEC — o script roda no servidor como unidade indivisível e pode ramificar.',
  'licao': 'MULTI/EXEC garante isolamento e atomicidade de execução, não atomicidade de efeito. Tratá-lo '
           'como o BEGIN/COMMIT de um banco relacional leva a supor uma garantia que não existe.',
  'evidencia': 'MULTI / INCR nao:e:numero / SET marcador:pos:erro "fui gravado" / EXEC\n'
               '  -> 1) ERR value is not an integer or out of range\n'
               '     2) OK\n'
               'GET marcador:pos:erro -> "fui gravado"   (aplicado apesar do erro anterior)'},

 {'titulo': 'CONFIG SET aplica agora e evapora no reinício',
  'sistema': 'Redis',
  'sintoma': 'Um ajuste de `maxmemory` feito durante um incidente resolve o problema — e o mesmo '
             'incidente reaparece no próximo reinício, possivelmente meses depois.',
  'causa_raiz': 'O `CONFIG SET` altera apenas a configuração do processo em execução. Ele não escreve no '
                'arquivo de configuração.',
  'diagnostico': 'Reiniciar e comparar. No laboratório, `maxmemory` fora posto em 512 MB e a política em '
                 '`allkeys-lru`; depois do `docker restart` voltaram a 0 e `noeviction`.',
  'correcao': 'Declarar a configuração onde ela persiste: `redis.conf`, argumentos do contêiner ou o '
              'compose — que foi onde este laboratório colocou o `--appendonly yes`. `CONFIG REWRITE` '
              'grava a configuração corrente no arquivo, quando existe um.',
  'licao': 'O mesmo reinício mostrou os dois lados: o dado sobreviveu porque o AOF estava declarado nos '
           'argumentos, e a configuração se perdeu porque fora ajustada em tempo de execução. O que está '
           'declarado sobrevive; o que foi ajustado a quente, não.',
  'evidencia': 'antes:  CONFIG SET maxmemory 512mb / maxmemory-policy allkeys-lru\n'
               'depois: GET persist:test           -> "ok"\n'
               '        CONFIG GET maxmemory       -> 0\n'
               '        CONFIG GET maxmemory-policy-> noeviction'},

 {'titulo': 'A imagem oficial do Redis não persiste por padrão',
  'sistema': 'Redis',
  'sintoma': 'A Seção 19.1 do roteiro manda verificar o AOF, e a resposta é `no`. O teste de '
             'persistência que vem depois não demonstra o que pretende.',
  'causa_raiz': 'A imagem `redis` do Docker Hub sobe com `appendonly no`. A durabilidade fica por conta '
                'apenas dos snapshots RDB, que gravam em intervalos e podem perder tudo desde o último.',
  'diagnostico': '`CONFIG GET appendonly` antes de confiar em qualquer teste de persistência.',
  'correcao': 'Ligar o AOF na subida do contêiner: `command: ["redis-server", "--appendonly", "yes"]`. '
              'Foi o que este laboratório fez — sem isso a Seção 19 não teria o que mostrar.',
  'licao': 'Imagens oficiais trazem padrões voltados a conveniência e desempenho, não a durabilidade. '
           'Antes de usar qualquer uma em algo que importe, vale ler o que ela liga e o que deixa '
           'desligado.',
  'evidencia': 'CONFIG GET appendonly   -> yes   (por causa do --appendonly yes no compose)\n'
               'CONFIG GET appendfsync  -> everysec\n'
               'CONFIG GET save         -> 3600 1 300 100 60 10000   (RDB segue ativo em paralelo)'},

 {'titulo': 'Limpar por lista fixa não escala',
  'sistema': 'Redis',
  'sintoma': 'Depois de executar toda a lista de `DEL` da Seção 23, o banco ainda tem 14 chaves.',
  'causa_raiz': 'A lista foi escrita à mão e não acompanhou as chaves criadas em outras seções. Nove das '
                'sobreviventes vêm de seções do próprio roteiro: `user:2001` a `user:2003` (5.2), '
                '`equipe:sorteio` (6.5), `pedido:1` e `pedidos:contador` (17.1), `user:1001`, '
                '`acessos:user:1001` e `fila:cadastros` (Seção 20).',
  'diagnostico': '`DBSIZE` e `KEYS *` depois da limpeza. Cada `DEL` também informa quantas chaves '
                 'realmente removeu — os zeros denunciam entradas obsoletas na lista.',
  'correcao': 'Apagar por prefixo com iteração incremental: `redis-cli --scan --pattern `cache:*` | '
              'xargs -r redis-cli DEL`. Melhor ainda, dar TTL a tudo que é descartável e não precisar '
              'limpar.',
  'licao': 'Qualquer inventário mantido à mão desatualiza silenciosamente. Em produção isso vira '
           'vazamento de memória: chaves órfãs que ninguém sabe de onde vieram e ninguém ousa apagar.',
  'evidencia': 'Após toda a lista de DEL da Seção 23:\n'
               'DBSIZE -> 14\n'
               'KEYS * -> ranking:torneio, equipe:sorteio, visitas:pagina:/produtos, acessos:user:1001,\n'
               '          pedido:1, user:1001, session:user:2002, fila:cadastros, user:2001,\n'
               '          pedidos:contador, user:2003, user:2002, ...'},
]

EXERCICIOS = [
 {'numero': 11, 'titulo': 'Escolher a estrutura a partir da operação', 'sistema': 'redis',
  'dificuldade': 'basico', 'tempo_min': 15,
  'enunciado': 'Para cada requisito abaixo, escolha a estrutura do Redis e escreva os comandos: '
    '(a) saber se um CPF já se cadastrou na promoção, sem permitir duplicata; '
    '(b) guardar o perfil de um usuário permitindo atualizar só o telefone; '
    '(c) manter os 10 produtos mais vendidos da semana; '
    '(d) guardar o resultado de um relatório caro por 15 minutos.',
  'esperado': 'A estrutura escolhida para cada caso, os comandos, e a justificativa da escolha pela '
    'operação que ela torna barata.',
  'solucao_codigo': '# (a) SET — unicidade, e o retorno ja responde se era duplicata\n'
    'SADD promo:cpfs "11122233344"      # 1 = entrou agora; 0 = ja existia\n'
    'SCARD promo:cpfs\n\n'
    '# (b) HASH — atualizacao parcial sem reler o documento\n'
    'HSET user:500 nome "Ana" telefone "61999990000" email "ana@ex.com"\n'
    'HSET user:500 telefone "61988887777"\n\n'
    '# (c) SORTED SET — ordenacao mantida a cada venda\n'
    'ZINCRBY vendas:semana 1 "produto:42"\n'
    'ZREVRANGE vendas:semana 0 9 WITHSCORES\n\n'
    '# (d) STRING com TTL — o prazo substitui a rotina de limpeza\n'
    'SETEX relatorio:vendas:2026-09 900 "{...json...}"',
  'solucao_comentario': 'O critério não é "que estrutura parece certa", é "que operação precisa ser '
    'barata". Em (a) a operação é testar e inserir ao mesmo tempo, e o retorno do `SADD` responde sem '
    'uma segunda consulta. Em (b) é atualizar um campo sem tocar nos outros — com JSON em string seria '
    'ler, alterar e regravar, com corrida entre a leitura e a escrita. Em (c) é manter a ordem a cada '
    'incremento, e o `ZINCRBY` reordena sozinho. Em (d) é esquecer sozinho.',
  'criterio_correcao': 'Cada escolha precisa vir com a operação que a justifica. Responder apenas o nome '
    'da estrutura não atende. Em (a), usar o retorno do `SADD` como resposta à pergunta é o ponto de '
    'maior valor.'},

 {'numero': 12, 'titulo': 'Consertar um rate limit que bloqueia para sempre', 'sistema': 'redis',
  'dificuldade': 'desafio', 'tempo_min': 20,
  'enunciado': 'Um rate limit implementado com `INCR` seguido de `EXPIRE` funciona há meses. Hoje alguns '
    'usuários relatam bloqueio permanente: por mais que esperem, continuam barrados. Explique a causa, '
    'mostre como diagnosticar e implemente a correção.',
  'esperado': 'O diagnóstico da janela entre os dois comandos, o comando que confirma a suspeita e uma '
    'implementação atômica.',
  'solucao_codigo': '# DIAGNOSTICO: a chave do usuario ficou sem TTL\n'
    'TTL rl:user:42        # -1 = existe e nunca expira  <-- a causa\n'
    '                      # -2 seria "nao existe"; qualquer positivo seria normal\n\n'
    '# CAUSA: entre estes dois comandos ha uma janela\n'
    'INCR rl:user:42       # se o processo morrer aqui...\n'
    'EXPIRE rl:user:42 60  # ...isto nunca roda, e a chave fica eterna\n\n'
    '# CORRECAO: um unico script, atomico e com ramificacao\n'
    'EVAL "local v = redis.call(\'INCR\', KEYS[1])\n'
    '      if v == 1 then redis.call(\'EXPIRE\', KEYS[1], ARGV[1]) end\n'
    '      return v" 1 rl:user:42 60\n\n'
    '# REMEDIACAO das chaves ja quebradas:\n'
    'redis-cli --scan --pattern "rl:*" | xargs -r redis-cli DEL',
  'solucao_comentario': 'O `TTL` devolvendo -1 é a assinatura do problema: a chave existe e nunca vai '
    'expirar, então o contador jamais volta a zero. A causa é que `INCR` e `EXPIRE` são duas viagens ao '
    'servidor, e nada garante que a segunda aconteça — basta o processo da aplicação morrer, ou a conexão '
    'cair, entre uma e outra. O script Lua elimina a janela porque roda inteiro dentro do servidor, e '
    'precisa ser Lua e não MULTI/EXEC porque há uma decisão no meio: só define o prazo se for a primeira '
    'requisição da janela, e MULTI/EXEC enfileira sem ver resultados intermediários. Repare que o '
    'problema é raro por requisição e inevitável em escala.',
  'criterio_correcao': 'Identificar o `TTL -1` como diagnóstico, explicar a janela entre os dois comandos '
    'e justificar por que Lua e não MULTI/EXEC. Propor apenas "juntar os comandos numa transação" não '
    'atende, porque MULTI/EXEC não permite a ramificação.'},

 {'numero': 13, 'titulo': 'Contar únicos com orçamento de memória', 'sistema': 'redis',
  'dificuldade': 'intermediario', 'tempo_min': 20,
  'enunciado': 'Você precisa reportar visitantes únicos por dia e também por mês, num site com 5 milhões '
    'de visitantes distintos mensais. Compare guardar os IDs em `SET` com usar `HyperLogLog`: estime a '
    'memória de cada opção, diga o que se perde e escolha. Depois responda: e se o time de marketing '
    'pedir a lista dos visitantes de uma campanha?',
  'esperado': 'A estimativa numérica, os comandos das duas opções e uma decisão justificada.',
  'solucao_codigo': '# OPCAO A — SET: guarda os elementos\n'
    'SADD visitantes:2026-09-27 "u:8412355"\n'
    'SCARD visitantes:2026-09-27\n'
    'SUNIONSTORE visitantes:2026-09 visitantes:2026-09-01 ... visitantes:2026-09-30\n'
    '#   ~16 bytes por ID + overhead  ->  5.000.000 x ~50 B  ~=  250 MB por mes\n\n'
    '# OPCAO B — HYPERLOGLOG: guarda um resumo estatistico\n'
    'PFADD hll:visitantes:2026-09-27 "u:8412355"\n'
    'PFCOUNT hll:visitantes:2026-09-27\n'
    'PFMERGE hll:visitantes:2026-09 hll:visitantes:2026-09-01 ... hll:visitantes:2026-09-30\n'
    'PFCOUNT hll:visitantes:2026-09\n'
    '#   ~12 KB por chave, independentemente do volume\n'
    '#   30 dias + 1 mensal  ->  ~372 KB',
  'solucao_comentario': 'A diferença é de cerca de três ordens de grandeza: centenas de megabytes contra '
    'centenas de kilobytes. O HyperLogLog paga isso com um erro de ~0,81% e com a perda de duas '
    'capacidades: não dá para perguntar se um usuário específico está lá, nem fazer interseção entre '
    'dois contadores. Para um número de relatório, 0,81% é ruído irrelevante — ninguém toma decisão '
    'diferente entre 4.960.000 e 5.000.000 de visitantes. O `PFMERGE` resolve o mensal corretamente, '
    'enquanto somar as contagens diárias contaria repetido quem voltou em dias diferentes. Quanto à '
    'pergunta final: se for preciso a lista de quem visitou, o HyperLogLog não serve de jeito nenhum e a '
    'resposta muda — nesse caso usa-se `SET` para a campanha específica, que é um recorte menor, e mantém-se '
    'o HLL para o número agregado.',
  'criterio_correcao': 'A estimativa precisa mostrar a ordem de grandeza e a resposta precisa nomear o '
    'que o HLL não faz. Reconhecer que a pergunta final **muda a escolha** é o ponto central: a estrutura '
    'é escolhida pela pergunta, e uma pergunta nova pode invalidá-la.'},

 {'numero': 14, 'titulo': 'Pub/Sub ou Stream: e-mails que somem', 'sistema': 'integrador',
  'dificuldade': 'desafio', 'tempo_min': 20,
  'enunciado': 'Um serviço publica em `canal:emails` e um worker inscrito envia os e-mails. Em produção, '
    'alguns e-mails nunca chegam — sempre em torno dos horários de deploy. Explique a causa, e reescreva '
    'a solução com a garantia necessária.',
  'esperado': 'O diagnóstico da perda durante a reinicialização do consumidor e uma implementação com '
    'Stream e consumer group.',
  'solucao_codigo': '# CAUSA: enquanto o worker reinicia, nao ha assinante.\n'
    '#        O PUBLISH devolve 0 e a mensagem deixa de existir.\n'
    'PUBLISH canal:emails "para=ana@ex.com"   -> 0     # ninguem ouvindo: perdida\n\n'
    '# CORRECAO: stream com consumer group\n'
    'XADD stream:emails * para "ana@ex.com" assunto "Bem-vinda"\n'
    'XGROUP CREATE stream:emails grupo:workers 0 MKSTREAM\n\n'
    '# o worker consome apenas o que nunca foi entregue ao grupo\n'
    'XREADGROUP GROUP grupo:workers worker:1 COUNT 10 BLOCK 5000 \\\n'
    '           STREAMS stream:emails >\n\n'
    '# so confirma DEPOIS de enviar de verdade\n'
    'XACK stream:emails grupo:workers 1790540869274-0\n\n'
    '# o que ficou sem confirmacao continua visivel\n'
    'XPENDING stream:emails grupo:workers',
  'solucao_comentario': 'O Pub/Sub entrega a quem está conectado naquele instante e não guarda nada — o '
    'retorno 0 do `PUBLISH` é a prova de que a mensagem foi descartada. Durante um deploy o worker fica '
    'segundos fora do ar, e tudo publicado nesse intervalo se perde. A Stream inverte isso: o evento é '
    'gravado num log e fica disponível mesmo sem consumidor algum no momento. Com consumer group, cada '
    'mensagem entregue fica pendente até o `XACK`, então confirmar **depois** do envio real garante que '
    'um worker morto no meio do processamento não leve a mensagem junto — ela continua no `XPENDING` e '
    'outro worker pode reivindicá-la com `XCLAIM`. O mesmo raciocínio vale para o GELF sobre UDP do Lab 2: '
    'ali a perda foi aceita conscientemente porque se trata de telemetria.',
  'criterio_correcao': 'Precisa identificar que a perda ocorre quando não há assinante, e que o `PUBLISH` '
    'retornando 0 é o sinal. A solução precisa confirmar com `XACK` após o envio, não antes — confirmar '
    'antes reintroduz exatamente a perda que se queria eliminar.'},
]

QUIZ = [
 {'numero': 11,
  'pergunta': 'Uma chave `produto:10` existe como string. O que acontece ao executar '
              '`LPUSH produto:10 "item"`?',
  'alternativas': [
    'A chave é convertida em list e o item é inserido.',
    'O comando falha com WRONGTYPE e a chave permanece como string.',
    'A chave é sobrescrita por uma list contendo apenas o item.',
    'O item é anexado ao fim da string, como um APPEND.'],
  'correta': 'B',
  'justificativa': 'A chave carrega um tipo e comandos de outro tipo são recusados. As alternativas A e C '
    'são tentadoras porque o `SET` realmente sobrescreve qualquer chave — mas ele é a exceção, não a '
    'regra. D confunde `LPUSH` com `APPEND`.'},

 {'numero': 12,
  'pergunta': 'Um `TTL minha:chave` devolve **-1**. O que isso significa?',
  'alternativas': [
    'A chave não existe.',
    'A chave existe e nunca vai expirar.',
    'A chave expirou há menos de um segundo.',
    'Houve erro ao consultar o TTL.'],
  'correta': 'B',
  'justificativa': '-1 é "existe, sem expiração"; -2 é "não existe". A alternativa A é a confusão mais '
    'comum, e ela importa: num rate limit, -1 significa contador eterno e usuário bloqueado para sempre, '
    'enquanto -2 significa que a janela já passou e o acesso deveria ser liberado.'},

 {'numero': 13,
  'pergunta': 'Uma transação `MULTI ... EXEC` tem três comandos e o segundo falha em tempo de execução. '
              'O que acontece?',
  'alternativas': [
    'Os três comandos são desfeitos e o estado volta ao anterior.',
    'A execução para no segundo comando e o terceiro não roda.',
    'O primeiro e o terceiro são aplicados; o EXEC devolve o erro na posição do segundo.',
    'O EXEC é recusado inteiro e nada é aplicado.'],
  'correta': 'C',
  'justificativa': 'Não há rollback: o `EXEC` devolve um array em que cada posição é um resultado ou um '
    'erro, e os comandos que funcionaram ficam aplicados. A alternativa A descreve um banco relacional. '
    'D descreve o que ocorre com erro de **sintaxe**, detectado no enfileiramento — distinção que a '
    'questão cobra.'},

 {'numero': 14,
  'pergunta': 'Você publica em um canal com `PUBLISH` e o retorno é 0. O que isso indica?',
  'alternativas': [
    'A mensagem foi enfileirada e será entregue quando houver um assinante.',
    'Houve erro na publicação.',
    'Nenhum assinante estava conectado e a mensagem foi descartada.',
    'O canal não existe e precisa ser criado antes.'],
  'correta': 'C',
  'justificativa': 'O retorno é a contagem de assinantes que receberam. Zero significa que ninguém ouvia '
    'e a mensagem deixou de existir — Pub/Sub não tem fila nem buffer. A alternativa A descreve uma '
    'Stream, que é justamente a estrutura a usar quando a perda é inaceitável. D é falsa: canais não '
    'precisam ser criados.'},
]

TABELA_DECISAO = [
 {'requisito': 'Leitura de um valor conhecido em microssegundos, tolerando perdê-lo',
  'sistema': 'Redis',
  'porque': 'Dados em memória e acesso por chave. MongoDB e Elasticsearch pagam disco e planejamento de consulta.'},
 {'requisito': 'Contador incrementado por muitos clientes ao mesmo tempo, sem perder contagem',
  'sistema': 'Redis',
  'porque': '`INCR` é atômico no servidor. Ler-somar-gravar na aplicação perde incrementos sob concorrência.'},
 {'requisito': 'Dado temporário que deve sumir sozinho: sessão, token, rate limit, lock',
  'sistema': 'Redis',
  'porque': 'TTL nativo por chave. Nos outros dois, expirar dado exige rotina própria ou política de ciclo de vida.'},
 {'requisito': 'Ranking consultado tanto pelo topo quanto pela posição de um participante',
  'sistema': 'Redis',
  'porque': 'Sorted set responde `ZREVRANGE` e `ZREVRANK` sem varrer. Ordenar por agregação a cada consulta não escala.'},
 {'requisito': 'Fila de trabalhos que não pode perder mensagem se o consumidor reiniciar',
  'sistema': 'Redis (Stream)',
  'porque': 'Consumer group mantém a mensagem pendente até o `XACK`. Pub/Sub e GELF/UDP descartam quando ninguém ouve.'},
 {'requisito': 'Contagem de elementos únicos em volume, com memória limitada',
  'sistema': 'Redis (HyperLogLog)',
  'porque': '~12 KB por contador com erro de ~0,81%. Um `SET` ou uma agregação `cardinality` crescem com o volume.'},
]

GLOSSARIO = [
 {'termo': 'Data structure server', 'definicao': 'Servidor em que o valor associado à chave é uma '
   'estrutura manipulável no próprio servidor, e não um blob opaco.'},
 {'termo': 'WRONGTYPE', 'definicao': 'Erro devolvido quando um comando é aplicado a uma chave de tipo '
   'incompatível; o Redis não converte tipos.'},
 {'termo': 'TTL', 'definicao': 'Tempo restante de vida de uma chave. Devolve -1 se ela é permanente e '
   '-2 se não existe.'},
 {'termo': 'SETEX', 'definicao': 'Grava valor e expiração numa única operação atômica, evitando o '
   'instante sem prazo do `SET` seguido de `EXPIRE`.'},
 {'termo': 'Sorted set', 'definicao': 'Coleção de membros com score numérico, mantida ordenada a cada '
   'escrita; empates são desempatados pelo membro.'},
 {'termo': 'Bitmap', 'definicao': 'String manipulada bit a bit, usada para representar um atributo '
   'booleano de muitas entidades em espaço mínimo.'},
 {'termo': 'HyperLogLog', 'definicao': 'Estrutura probabilística que estima cardinalidade com ~0,81% de '
   'erro e memória limitada a cerca de 12 KB.'},
 {'termo': 'PFMERGE', 'definicao': 'Une HyperLogLogs, permitindo obter únicos de um período a partir dos '
   'contadores de cada dia.'},
 {'termo': 'Stream', 'definicao': 'Log append-only com IDs crescentes, que preserva os eventos e permite '
   'releitura — ao contrário do Pub/Sub.'},
 {'termo': 'Consumer group', 'definicao': 'Mecanismo que distribui mensagens de uma Stream entre '
   'consumidores e mantém cada entrega pendente até o `XACK`.'},
 {'termo': 'XPENDING', 'definicao': 'Lista as mensagens entregues a um consumer group e ainda não '
   'confirmadas.'},
 {'termo': 'MULTI / EXEC', 'definicao': 'Enfileira comandos e os executa em bloco, sem intercalação de '
   'outros clientes — mas sem rollback.'},
 {'termo': 'EVAL', 'definicao': 'Executa um script Lua no servidor como unidade atômica, permitindo '
   'ramificar conforme resultados intermediários.'},
 {'termo': 'RDB', 'definicao': 'Persistência por snapshots periódicos do dataset; compacto e de '
   'recuperação rápida, perde o que veio depois do último.'},
 {'termo': 'AOF', 'definicao': 'Persistência por log de comandos de escrita; maior em disco, recuperação '
   'mais lenta, perda limitada a ~1 s com `everysec`.'},
 {'termo': 'Eviction', 'definicao': 'Política que decide quais chaves descartar ao atingir `maxmemory`; '
   '`noeviction` recusa escritas em vez de descartar.'},
 {'termo': 'SCAN', 'definicao': 'Iteração incremental sobre o keyspace, com cursor, que não bloqueia o '
   'servidor como o `KEYS`.'},
]

LEITURAS = [
 'Redis in Action (Josiah Carlson) — gratuito no site da Redis; a melhor introdução aos padrões de '
 'aplicação, com capítulos inteiros sobre filas, locks e contadores.',
 'Documentação oficial do Redis, seção Data types — cada tipo com a complexidade de cada comando, que é '
 'o que decide se ele serve ao seu volume.',
 'Artigo original do HyperLogLog (Flajolet et al., 2007) e o post de Salvatore Sanfilippo sobre a '
 'implementação no Redis — para entender de onde vem o erro de 0,81%.',
 'Documentação do Redis sobre Streams e consumer groups, incluindo `XCLAIM` e `XAUTOCLAIM`, que tratam '
 'o consumidor que morre sem confirmar.',
]
