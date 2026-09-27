#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modulos de Redis (Lab 3). Entram entre os modulos de Elasticsearch e a sintese."""

MODULOS = []

# =====================================================================
MODULOS.append({
 'tema': 'redis',
 'titulo': 'Redis: o servidor de estruturas de dados',
 'duracao_min': 45,
 'abertura': 'Chamar o Redis de "banco chave-valor" é verdade e é insuficiente. A chave aponta para um '
             'valor, sim — mas esse valor é uma estrutura que o servidor sabe manipular. A diferença '
             'entre guardar um JSON e guardar um hash é a diferença entre trazer o dado para a aplicação '
             'e mandar a operação até o dado.',
 'objetivos': [
   'Explicar por que o Redis é um servidor de estruturas de dados e não apenas um cache de strings.',
   'Prever o resultado de um comando aplicado a uma chave do tipo errado.',
   'Escolher entre string, hash, list, set e sorted set a partir da operação pretendida.',
   'Usar TTL corretamente, distinguindo os três estados que o comando reporta.',
   'Combinar corretamente as pontas de inserção e consumo de uma list para obter FIFO ou LIFO.',
 ],
 'conceitos': [
   {'nome': 'Data structure server: a operação vai até o dado',
    'explicacao': 'Num cache comum, incrementar um contador exige ler o valor, somar na aplicação e '
      'gravar de volta — três passos, duas viagens de rede e uma janela em que dois clientes podem ler o '
      'mesmo valor e gravar por cima um do outro. No Redis isso é um `INCR`, executado dentro do '
      'servidor, de forma atômica. O mesmo vale para acrescentar a uma lista, somar um ponto num ranking '
      'ou incrementar um campo de hash. É por isso que a estrutura importa: ela define que operações '
      'podem ser empurradas para o servidor.',
    'analogia': 'A diferença entre pedir o extrato inteiro ao banco para calcular seu saldo em casa e '
      'pedir ao banco o saldo. No segundo caso a conta é feita onde o dado mora.'},

   {'nome': 'A chave é tipada, e o tipo não se converte',
    'explicacao': 'Toda chave no Redis carrega um tipo, definido no momento em que ela nasce. Um comando '
      'de outro tipo sobre ela é recusado com `WRONGTYPE`, sem conversão e sem sobrescrita. A exceção '
      'é o `SET`, que substitui a chave inteira, qualquer que fosse o tipo anterior — o que engana, '
      'porque dá a impressão de que o Redis é permissivo com tipos quando na verdade é estrito.',
    'erro_comum': 'Reaproveitar um nome de chave para outra estrutura. Se `user:1001` já existe como '
      'string, um `HSET user:1001` falha — e falha em tempo de execução, no ambiente onde a chave '
      'antiga existir, não no ambiente limpo onde o código foi testado.'},

   {'nome': 'Strings guardam bytes, não caracteres',
    'explicacao': 'A string do Redis é uma sequência de bytes, e comandos como `STRLEN`, `APPEND` '
      'e `GETRANGE` operam em bytes. Em texto ASCII byte e caractere coincidem e a distinção passa '
      'despercebida; em português, não. Isso também significa que uma string do Redis pode guardar '
      'qualquer coisa — JSON, um protobuf, uma imagem — até 512 MB.',
    'erro_comum': 'Usar `GETRANGE` para cortar texto com acento e partir um caractere ao meio, '
      'produzindo bytes inválidos em UTF-8.'},

   {'nome': 'TTL tem três respostas, não duas',
    'explicacao': 'O `TTL` devolve o número de segundos restantes quando há expiração, **-1** quando '
      'a chave existe mas é permanente, e **-2** quando a chave não existe. Tratar -1 e -2 como o mesmo '
      '"sem TTL" apaga a distinção entre "está no cache para sempre" e "não está no cache" — que são '
      'situações opostas. Outro ponto decisivo: escrever numa chave com `INCR` ou `APPEND` **não '
      'renova** o TTL, enquanto um `SET` sem cláusula de expiração o remove por completo.',
    'erro_comum': 'Atualizar uma sessão com `SET` sem repetir o `EX`. O TTL é descartado e a '
      'sessão passa a viver para sempre — um vazamento de memória que só aparece semanas depois.'},

   {'nome': 'Hash: atualização parcial sem serializar',
    'explicacao': 'Guardar uma entidade como string JSON obriga a ler o documento inteiro, alterar na '
      'aplicação e regravar para mudar um campo — três operações e uma condição de corrida entre a '
      'leitura e a escrita. O hash resolve isso: cada campo é lido e escrito isoladamente, e o '
      '`HINCRBY` incrementa um campo numérico atomicamente. O custo é perder a capacidade de guardar '
      'estrutura aninhada, já que os valores do hash são escalares.',
    'analogia': 'JSON numa string é um formulário plastificado: para mudar um campo, imprime-se outro '
      'inteiro. O hash é o formulário com campos editáveis.'},

   {'nome': 'List: a ponta de entrada decide a semântica',
    'explicacao': 'A list é uma lista duplamente ligada com inserção e remoção nas duas pontas. Não '
      'existe "list FIFO" ou "list LIFO" — o comportamento nasce da combinação escolhida. `LPUSH` com '
      '`RPOP` (ou `RPUSH` com `LPOP`) dá FIFO, uma fila: quem entra primeiro sai primeiro. '
      'Empurrar e consumir pela mesma ponta dá LIFO, uma pilha. O `LRANGE` apenas lê, sem consumir.',
    'erro_comum': 'Usar `RPUSH` para enfileirar e `RPOP` para consumir. É o erro mais comum com '
      'listas: o código parece uma fila, roda sem erro, e processa os trabalhos na ordem inversa. Com '
      'carga baixa ninguém nota; sob fila cheia, os itens mais antigos nunca são processados.'},

   {'nome': 'Set: unicidade como resposta, não só como propriedade',
    'explicacao': 'O set garante elementos únicos, mas o detalhe útil é que o `SADD` devolve quantos '
      'membros **realmente entraram**. Um retorno 0 significa "já estava lá". Isso transforma o set num '
      'teste de duplicidade atômico: registrar um voto, um clique ou o processamento de uma mensagem e '
      'saber, na mesma operação, se aquilo já havia acontecido. Os comandos de conjunto — `SINTER`, '
      '`SUNION`, `SDIFF` — rodam no servidor.',
    'erro_comum': 'Supor que `SDIFF` é comutativo. `SDIFF A B` devolve o que está em A e não em '
      'B; trocar a ordem dá outro resultado.'},

   {'nome': 'Sorted set: ordenação mantida a cada escrita',
    'explicacao': 'O sorted set associa um score numérico a cada membro e mantém a ordem continuamente, '
      'com custo logarítmico por operação. Ele responde tanto "quais são os cinco primeiros" quanto "em '
      'que posição está o jogador X" sem varrer a estrutura — a segunda pergunta é a que nenhuma outra '
      'estrutura responde bem. Empates em score são desempatados pelo membro, em ordem lexicográfica.',
    'erro_comum': 'Assumir que o desempate aparece igual nos dois sentidos. Como o `ZREVRANGE` '
      'percorre a estrutura ao contrário, o empate também sai invertido — detalhe que aparece quando dois '
      'competidores têm a mesma pontuação e a ordem exibida surpreende.'},
 ],
 'demos': [
   {'titulo': 'A chave é tipada — e o roteiro do laboratório tropeça nisso',
    'linguagem': 'bash',
    'codigo': '# Seção 5.1 do lab criou user:1001 como string:\n'
              'SET user:1001 "João"\n'
              'APPEND user:1001 " Silva"\n\n'
              '# Seção 20 tenta usar a MESMA chave como hash:\n'
              'HSET user:1001 nome "João" idade 40 cidade "Brasília"',
    'saida': 'WRONGTYPE Operation against a key holding the wrong kind of value\n\n'
             'TYPE user:1001  ->  string\n'
             'GET  user:1001  ->  "João Silva"',
    'explicacao': 'O exercício integrador do roteiro não roda como está: a chave já existe com outro '
      'tipo. O diagnóstico é imediato com `TYPE`. A correção é remover a chave ou — melhor — não '
      'reaproveitar o nome, usando `user:nome:1001` para a string e `user:1001` para o hash.',
    'fonte': 'Lab 3, PARTE2-EVIDENCIAS.md, Seção 20'},

   {'titulo': 'STRLEN conta bytes',
    'linguagem': 'bash',
    'codigo': 'SET user:1001 "João"\n'
              'APPEND user:1001 " Silva"\n'
              'STRLEN user:1001',
    'saida': 'SET     -> OK\n'
             'APPEND  -> 11\n'
             'STRLEN  -> 11',
    'explicacao': '"João Silva" tem 10 caracteres, mas 11 bytes: o "ã" ocupa 2 em UTF-8. O `APPEND` '
      'também devolve o comprimento em bytes. Em qualquer operação de recorte, é o byte que conta.',
    'fonte': 'Lab 3, PARTE1-EVIDENCIAS.md, Seção 5.1'},

   {'titulo': 'Os três estados do TTL',
    'linguagem': 'bash',
    'codigo': 'SET cache:home "html-home"\n'
              'TTL cache:home          # existe, sem expiração\n'
              'EXPIRE cache:home 30\n'
              'TTL cache:home          # existe, com expiração\n'
              'PERSIST cache:home\n'
              'TTL cache:home          # voltou a ser permanente\n'
              'DEL cache:home\n'
              'TTL cache:home          # não existe mais',
    'saida': '-1\n30\n-1\n-2',
    'explicacao': 'Três situações, três respostas. O `PERSIST` remove a expiração e devolve a chave ao '
      'estado permanente. Uma camada de cache que trate -1 e -2 como iguais confunde "guardado para '
      'sempre" com "não guardado".',
    'fonte': 'Lab 3, PARTE1-EVIDENCIAS.md, Seções 4.1 e 4.5'},

   {'titulo': 'O erro clássico da list: a fila que anda ao contrário',
    'linguagem': 'bash',
    'codigo': 'RPUSH fila:etl "job:extrair" "job:transformar" "job:validar" \\\n'
              '               "job:carregar" "job:notificar"\n'
              'RPOP fila:etl\n'
              'RPOP fila:etl\n'
              'LRANGE fila:etl 0 -1',
    'saida': 'RPOP   -> "job:notificar"\n'
             'RPOP   -> "job:carregar"\n'
             'LRANGE -> "job:extrair", "job:transformar", "job:validar"',
    'explicacao': 'Enfileirou pela direita e consumiu pela direita: saíram os dois **últimos**, não os '
      'dois primeiros. O código não dá erro, a fila funciona, e os trabalhos mais antigos vão sendo '
      'empurrados para o fim da vida. Com `RPUSH` o consumo correto é `LPOP`.',
    'fonte': 'Lab 3, PARTE1-EVIDENCIAS.md, Exercício 5'},

   {'titulo': 'Empate em sorted set aparece invertido no ZREVRANGE',
    'linguagem': 'bash',
    'codigo': 'ZADD t:empate 8 "Bruno" 8 "Carlos" 8 "Ana"\n'
              'ZRANGE    t:empate 0 -1 WITHSCORES\n'
              'ZREVRANGE t:empate 0 -1 WITHSCORES',
    'saida': 'ZRANGE    -> Ana 8, Bruno 8, Carlos 8\n'
             'ZREVRANGE -> Carlos 8, Bruno 8, Ana 8',
    'explicacao': 'Com scores iguais, o desempate é lexicográfico pelo membro. Como o `ZREVRANGE` '
      'percorre ao contrário, o empate também inverte. Num ranking de verdade isso significa que, entre '
      'empatados, quem tem nome mais ao fim do alfabeto aparece na frente — critério arbitrário que '
      'convém substituir por um score composto, por exemplo somando um desempate temporal.',
    'fonte': 'Lab 3, verificação isolada durante a execução'},
 ],
 'fechamento': 'O Redis não substitui os dois sistemas anteriores: ele responde a uma terceira pergunta, '
   'que é "qual o estado agora, no menor tempo possível". Escolher a estrutura certa é quase toda a '
   'decisão de projeto — e o preço de escolher errado aparece como comportamento estranho, não como erro. '
   'O próximo módulo mostra como essas estruturas viram padrões de aplicação.',
 'perguntas': [
   'Por que o SET aceita sobrescrever uma chave de qualquer tipo, mas o HSET não?',
   'Sua sessão tem TTL de 30 minutos e é atualizada a cada requisição com SET. O que acontece com a expiração?',
   'Você precisa saber se um e-mail já foi enviado para um usuário hoje. Que estrutura usa, e por quê?',
   'Um ranking tem dois jogadores com 1500 pontos. Que critério o Redis usa para ordená-los, e isso é aceitável no seu caso?',
 ],
})

# =====================================================================
MODULOS.append({
 'tema': 'redis',
 'titulo': 'Redis: padrões de aplicação e atomicidade',
 'duracao_min': 40,
 'abertura': 'Cache, sessão, contador, rate limit, fila e ranking são seis problemas diferentes que o '
             'Redis resolve com as mesmas estruturas do módulo anterior. O que muda é a combinação — e, '
             'em dois deles, a diferença entre funcionar e falhar está na atomicidade.',
 'objetivos': [
   'Implementar cache, sessão, contador, rate limit, fila e ranking com a estrutura adequada a cada um.',
   'Identificar a janela de falha do rate limit implementado com dois comandos separados.',
   'Explicar o que MULTI/EXEC garante e o que ele não garante.',
   'Justificar quando um script Lua é necessário em vez de uma transação.',
 ],
 'conceitos': [
   {'nome': 'Cache e sessão: o TTL substitui a rotina de limpeza',
    'explicacao': 'Cache de página, sessão de usuário e token são todos o mesmo padrão: uma string com '
      'prazo. O ganho não é só de desempenho — é operacional. Sem TTL, alguém precisa escrever e manter '
      'um processo que varre o armazenamento apagando o que venceu; com TTL, o próprio Redis remove. '
      'Usar `SET ... EX` ou `SETEX` em vez de `SET` seguido de `EXPIRE` importa porque '
      'garante que não existe instante em que a chave esteja gravada sem prazo.',
    'erro_comum': 'Guardar no cache o resultado de uma consulta que pode ser inválida antes do TTL '
      'vencer. TTL controla idade, não correção: se o dado de origem mudar, o cache continua servindo o '
      'valor velho até expirar. Quando isso não é aceitável, é preciso invalidar explicitamente com '
      '`DEL` no momento da escrita.'},

   {'nome': 'Contador: a razão de existir o INCR',
    'explicacao': 'Ler, somar e gravar é a implementação intuitiva de um contador e está errada sob '
      'concorrência: dois clientes leem 10, ambos gravam 11, e uma contagem se perde. O `INCR` '
      'executa a leitura e a escrita como uma operação indivisível dentro do servidor. Nenhum cliente '
      'consegue se intercalar. É o exemplo mais simples do princípio que organiza todo este módulo: '
      'empurrar a operação para onde o dado está elimina a corrida.',
    'analogia': 'É a diferença entre dois caixas anotando o total num papel compartilhado e uma catraca '
      'que conta sozinha. A catraca não erra porque não há intervalo entre ler e escrever.'},

   {'nome': 'Rate limit: a janela de falha que a Seção 10.3 não conta',
    'explicacao': 'O padrão do roteiro é `INCR` seguido de `EXPIRE`: na primeira requisição o '
      'contador vai a 1 e ganha prazo de 60 segundos; nas seguintes apenas incrementa, e o TTL não é '
      'renovado, de modo que a janela conta a partir do primeiro acesso. Correto em regime normal. O '
      'problema está entre os dois comandos: se o processo da aplicação morrer ali, a chave fica sem TTL. '
      'Como o `INCR` nunca expira nada, aquele contador fica eterno — e o usuário passa a ser '
      'bloqueado para sempre, sem que nada no sistema indique a causa.',
    'erro_comum': 'Considerar o cenário improvável demais para tratar. Ele é raro por requisição e '
      'inevitável em escala: a um milhão de requisições por dia, uma janela de microssegundos acontece.'},

   {'nome': 'MULTI/EXEC: enfileira, isola, mas não desfaz',
    'explicacao': 'Entre o `MULTI` e o `EXEC`, os comandos não são executados — são enfileirados, '
      'cada um respondendo `QUEUED`. O `EXEC` dispara todos em sequência, sem que nenhum comando '
      'de outro cliente se intercale. Isso dá isolamento e atomicidade de execução. O que **não** dá é '
      'rollback: se um comando falhar em tempo de execução, os demais são aplicados assim mesmo e não há '
      'como voltar atrás. Erros de sintaxe são diferentes — esses são detectados no enfileiramento e '
      'abortam a transação inteira.',
    'erro_comum': 'Tratar MULTI/EXEC como o BEGIN/COMMIT de um banco relacional e presumir que um erro '
      'no meio desfaz o resto. Não desfaz, e o estado fica parcialmente aplicado.'},

   {'nome': 'A transação é uma propriedade da conexão',
    'explicacao': 'O `MULTI` abre um contexto naquela conexão específica. Enviar `MULTI` por uma '
      'conexão e `EXEC` por outra não forma transação alguma: o `EXEC` falha com `ERR EXEC '
      'without MULTI` e os comandos do meio já executaram soltos. Numa aplicação com pool de conexões, '
      'isso acontece sem que ninguém escreva nada de errado — basta o pool entregar conexões diferentes a '
      'cada chamada.',
    'erro_comum': 'Emitir os comandos de uma transação por meio de uma camada de abstração que não '
      'garante a mesma conexão. A biblioteca cliente precisa expor explicitamente o conceito de '
      'transação ou de conexão reservada.'},

   {'nome': 'Lua: quando a lógica precisa decidir no meio',
    'explicacao': 'Um script Lua roda inteiro no servidor como unidade indivisível, e pode **ramificar**: '
      'ler um valor, decidir e escrever conforme o resultado. É exatamente o que o MULTI/EXEC não '
      'consegue, porque ele enfileira sem executar e portanto não tem acesso a nenhum resultado '
      'intermediário. O rate limit correto é essa ramificação: incrementa, e **se** for a primeira '
      'requisição da janela, define a expiração.',
    'analogia': 'MULTI/EXEC é entregar uma lista pronta de compras; o script Lua é mandar alguém ao '
      'mercado com autorização para decidir na hora.'},
 ],
 'demos': [
   {'titulo': 'Rate limit: dois comandos contra um script',
    'linguagem': 'bash',
    'codigo': '# Seção 10.3 — dois comandos, com janela de falha entre eles\n'
              'INCR rl:user:42\n'
              'EXPIRE rl:user:42 60\n\n'
              '# Seção 18 — um script, atômico\n'
              'EVAL "local v = redis.call(\'INCR\', KEYS[1])\n'
              '      if v == 1 then redis.call(\'EXPIRE\', KEYS[1], ARGV[1]) end\n'
              '      return v" 1 rl:ip:192.168.0.10 60',
    'saida': 'chamadas sucessivas do script -> 1, 2, 3\n'
             'TTL rl:ip:192.168.0.10        -> 60  (definido só na primeira)',
    'explicacao': 'O contador sobe a cada chamada; o `EXPIRE` só roda quando v == 1. O TTL não é '
      'renovado depois, então a janela conta do primeiro acesso. A diferença para a versão de dois '
      'comandos não é a viagem de rede economizada — é que desaparece o estado em que a chave existe '
      'sem prazo.',
    'fonte': 'Lab 3, PARTE1 Seção 10.3 e PARTE2 Seção 18'},

   {'titulo': 'MULTI/EXEC não faz rollback',
    'linguagem': 'bash',
    'codigo': 'SET nao:e:numero "texto"\n\n'
              'MULTI\n'
              'INCR nao:e:numero              # vai falhar: não é número\n'
              'SET  marcador:pos:erro "fui gravado"\n'
              'EXEC\n\n'
              'GET marcador:pos:erro',
    'saida': 'MULTI  -> OK\n'
             'INCR   -> QUEUED\n'
             'SET    -> QUEUED\n'
             'EXEC   -> 1) ERR value is not an integer or out of range\n'
             '          2) OK\n\n'
             'GET marcador:pos:erro -> "fui gravado"',
    'explicacao': 'O `INCR` falhou dentro do `EXEC` e o `SET` seguinte foi aplicado. O estado ficou '
      'parcial. Em um banco relacional o erro abortaria a transação inteira; aqui, o `EXEC` devolve um '
      'array em que cada posição pode ser um resultado ou um erro, e cabe à aplicação inspecionar.',
    'fonte': 'Lab 3, PARTE2-EVIDENCIAS.md, Seção 17'},

   {'titulo': 'A mesma transação, em conexões diferentes',
    'linguagem': 'bash',
    'codigo': '# cada linha enviada por uma conexão distinta\n'
              'MULTI\n'
              'INCR pedidos:contador\n'
              'EXEC',
    'saida': 'MULTI -> OK\n'
             'INCR  -> 5        (executou solto, fora de transação)\n'
             'EXEC  -> ERR EXEC without MULTI',
    'explicacao': 'O `MULTI` morreu junto com sua conexão. O `INCR` não foi enfileirado: executou na '
      'hora e alterou o estado. O `EXEC` chegou a uma conexão que nunca abriu transação. Nenhum desses '
      'três comandos está errado isoladamente — o erro é de infraestrutura, e é por isso que ele escapa '
      'em revisão de código.',
    'fonte': 'Lab 3, PARTE2-EVIDENCIAS.md, Seção 17'},
 ],
 'fechamento': 'Os padrões deste módulo cobrem a maior parte do uso real do Redis. O fio que os liga é a '
   'atomicidade: sempre que uma operação lógica precisa de mais de um passo, é preciso decidir '
   'conscientemente se o passo intermediário pode ser observado ou interrompido. O próximo módulo sai do '
   'chave-valor e mostra o que mais cabe num servidor de estruturas.',
 'perguntas': [
   'Por que SETEX é preferível a SET seguido de EXPIRE, se o resultado final é o mesmo?',
   'Seu rate limit usa INCR + EXPIRE há dois anos sem problema. Isso prova que a janela de falha não existe?',
   'Quando MULTI/EXEC não serve e só um script Lua resolve?',
   'Um usuário reclama que está bloqueado há dias pelo rate limit. Como você investiga?',
 ],
})

# =====================================================================
MODULOS.append({
 'tema': 'redis',
 'titulo': 'Redis além do chave-valor: probabilísticos, streams e durabilidade',
 'duracao_min': 40,
 'abertura': 'Bitmap, HyperLogLog e geoespacial parecem recursos exóticos até se perceber o que têm em '
             'comum: cada um troca uma garantia por ordens de grandeza de memória. E as Streams resolvem '
             'o problema que o Pub/Sub deixa em aberto desde que foi apresentado.',
 'objetivos': [
   'Estimar o custo de memória de um bitmap e de um HyperLogLog e dizer o que cada um perde.',
   'Reconhecer que os comandos geoespaciais são um sorted set com outra interface.',
   'Escolher entre Pub/Sub e Streams a partir da garantia de entrega exigida.',
   'Comparar RDB e AOF e prever o que sobrevive a um reinício.',
   'Relacionar política de eviction com a presença ou ausência de TTL nas chaves.',
 ],
 'conceitos': [
   {'nome': 'Bitmap: um bit por entidade',
    'explicacao': 'O bitmap não é um tipo próprio — é uma string manipulada bit a bit por `SETBIT`, '
      '`GETBIT` e `BITCOUNT`. Usando o identificador do usuário como índice do bit, representa-se '
      'um atributo booleano de toda a base num espaço minúsculo: presença no dia, usuário ativo, '
      'participação numa campanha. O tamanho é determinado pelo maior índice usado, e bits nunca '
      'escritos valem 0 sem erro.',
    'erro_comum': 'Esquecer que o `SETBIT` devolve o valor **anterior** do bit, não o novo. Quem lê o '
      'retorno como confirmação interpreta 0 como falha.'},

   {'nome': 'HyperLogLog: cardinalidade sem guardar os elementos',
    'explicacao': 'O HyperLogLog responde "quantos distintos" com erro em torno de 0,81% e memória '
      'limitada a cerca de 12 KB, independentemente de conter três ou trezentos milhões de valores. Ele '
      'não guarda os elementos — guarda um resumo estatístico. Por isso não é possível perguntar se um '
      'usuário específico está lá, nem fazer interseção entre dois HLLs. O que é possível, e muito útil, '
      'é o `PFMERGE`: unir contadores diários para obter os únicos da semana, algo que somar as '
      'contagens diárias jamais daria certo, porque contaria repetido quem voltou.',
    'analogia': 'É a diferença entre a lista de presença e o contador da catraca. A lista diz quem '
      'entrou; a catraca diz quantos, ocupa quase nada e não permite conferir um nome.'},

   {'nome': 'Geoespacial é um sorted set disfarçado',
    'explicacao': 'Os comandos `GEOADD`, `GEODIST` e `GEOSEARCH` não criam um tipo novo. A '
      'coordenada é convertida num geohash de 52 bits que vira o score de um sorted set comum — e é a '
      'ordenação desse score que torna a busca por proximidade eficiente, porque pontos geograficamente '
      'próximos recebem geohashes numericamente próximos. Dá para confirmar rodando `TYPE` sobre a '
      'chave: o resultado é `zset`.',
    'erro_comum': 'Inverter longitude e latitude no `GEOADD`. A ordem é longitude primeiro, ao '
      'contrário de como se costuma escrever coordenadas. O Redis aceita sem reclamar e o ponto vai '
      'parar em outro continente.'},

   {'nome': 'Pub/Sub entrega a quem está ouvindo; Stream guarda',
    'explicacao': 'O `PUBLISH` devolve quantos assinantes receberam a mensagem. Se for zero, a '
      'mensagem simplesmente deixou de existir — não há fila, buffer ou repetição. A Stream é o oposto: '
      'um log append-only, com ID crescente por evento, que permite reler o histórico a qualquer momento. '
      'Com consumer groups, cada mensagem entregue fica **pendente** até ser confirmada com `XACK`; '
      'se o consumidor morrer antes de confirmar, a mensagem continua na lista de pendências e outro '
      'consumidor pode assumi-la.',
    'erro_comum': 'Usar Pub/Sub para algo que não pode ser perdido — disparo de e-mail, baixa de estoque, '
      'notificação de pagamento. Funciona em teste, com o consumidor ligado, e perde mensagens em '
      'produção toda vez que o consumidor reinicia.'},

   {'nome': 'RDB e AOF respondem a perguntas diferentes',
    'explicacao': 'O RDB grava snapshots binários do dataset inteiro em intervalos configurados: arquivo '
      'compacto, recuperação rápida, e perda de tudo que foi escrito desde o último snapshot. O AOF '
      'registra cada comando de escrita num log: arquivo maior, recuperação mais lenta porque reexecuta o '
      'log, e perda limitada a cerca de um segundo com `appendfsync everysec`. Não são excludentes — '
      'é comum manter os dois, o RDB como backup para copiar e o AOF como garantia de durabilidade.',
    'erro_comum': 'Supor que o Redis persiste por padrão na imagem oficial. O AOF vem desligado; sem '
      'habilitá-lo, a durabilidade depende apenas dos snapshots RDB.'},

   {'nome': 'CONFIG SET aplica agora e esquece depois',
    'explicacao': 'O `CONFIG SET` altera a configuração do processo em execução, imediatamente. Ele '
      'não escreve no arquivo de configuração: ao reiniciar, tudo volta ao que estava declarado no '
      '`redis.conf` ou nos argumentos de inicialização. Isso é ótimo para experimentar e péssimo como '
      'forma de configurar em definitivo.',
    'erro_comum': 'Resolver um incidente ajustando `maxmemory` com `CONFIG SET`, não registrar a '
      'mudança na configuração persistente, e ver o mesmo incidente voltar no próximo reinício — meses '
      'depois, quando ninguém lembra do ajuste.'},

   {'nome': 'Eviction: o que o Redis faz quando a memória acaba',
    'explicacao': 'Atingido o `maxmemory`, a política decide o destino. `noeviction`, o padrão, '
      'recusa novas escritas com erro e mantém as leituras — seguro para dado que não pode sumir, '
      'catastrófico para um cache, que para de aceitar itens. `allkeys-lru` descarta as chaves usadas '
      'há mais tempo, com ou sem TTL. `volatile-lru` faz o mesmo apenas entre as chaves que têm TTL, '
      'protegendo o que é permanente. A escolha depende de a instância ser cache puro ou misturar cache e '
      'dado durável.',
    'erro_comum': 'Usar `allkeys-lru` numa instância que mistura cache e dado permanente. O Redis '
      'descartará o dado permanente sem qualquer aviso quando a memória apertar.'},
 ],
 'demos': [
   {'titulo': 'Bitmap: 1.004 usuários em 126 bytes',
    'linguagem': 'bash',
    'codigo': 'SETBIT presenca:2026-03-15 1001 1\n'
              'SETBIT presenca:2026-03-15 1002 1\n'
              'SETBIT presenca:2026-03-15 1003 0\n'
              'BITCOUNT presenca:2026-03-15\n'
              'STRLEN   presenca:2026-03-15\n'
              'GETBIT   presenca:2026-03-15 9999',
    'saida': 'SETBIT   -> 0, 0, 0    (valor anterior de cada bit)\n'
             'BITCOUNT -> 2\n'
             'STRLEN   -> 126\n'
             'GETBIT   -> 0',
    'explicacao': 'O bit de índice 1003 força a string a ter ceil(1004/8) = 126 bytes, e nesse espaço '
      'cabem 1.008 flags. Uma lista dos IDs presentes custaria vários bytes por usuário. O bit de índice '
      '9999, nunca escrito, devolve 0 sem erro — o bitmap só aloca até o maior índice usado.',
    'fonte': 'Lab 3, PARTE2-EVIDENCIAS.md, Seção 13'},

   {'titulo': 'HyperLogLog: unindo janelas de tempo',
    'linguagem': 'bash',
    'codigo': 'PFADD hll:dia1 "u1" "u2" "u3"\n'
              'PFADD hll:dia2 "u3" "u4" "u5"\n'
              'PFMERGE hll:total hll:dia1 hll:dia2\n'
              'PFCOUNT hll:total\n'
              'STRLEN  hll:total',
    'saida': 'PFCOUNT -> 5\n'
             'STRLEN  -> 31',
    'explicacao': 'Seis inserções, cinco únicos — u3 aparece nos dois dias e conta uma vez. Somar as '
      'contagens diárias daria 6, errado. Com poucos elementos o Redis usa codificação esparsa e o '
      'contador ocupa 31 bytes; ele cresce até um teto de cerca de 12 KB e para de crescer, não importa '
      'quantos milhões de valores distintos entrem depois.',
    'fonte': 'Lab 3, PARTE2-EVIDENCIAS.md, Seção 14'},

   {'titulo': 'Geo é zset: a prova',
    'linguagem': 'bash',
    'codigo': 'GEOADD cidades:df -47.8825 -15.7942 "Brasilia"\n'
              'GEOADD cidades:df -48.0770 -15.6014 "Taguatinga"\n'
              'GEODIST cidades:df "Brasilia" "Taguatinga" km\n'
              'GEOSEARCH cidades:df FROMLONLAT -47.8825 -15.7942 BYRADIUS 10 km WITHDIST\n\n'
              'TYPE   cidades:df\n'
              'ZSCORE cidades:df "Brasilia"',
    'saida': 'GEODIST   -> 29.8936\n'
             'GEOSEARCH -> Brasilia 0.0003, LagoSul 5.2386   (Taguatinga ficou fora do raio)\n'
             'TYPE      -> zset\n'
             'ZSCORE    -> 965555706610042',
    'explicacao': 'Quase 30 km entre Brasília e Taguatinga, e com raio de 10 km Taguatinga sai do '
      'resultado. O `TYPE` revela o que há por baixo: um sorted set cujo score é o geohash de 52 bits '
      'da coordenada. Todo comando GEO é açúcar sintático sobre operações de zset.',
    'fonte': 'Lab 3, PARTE2-EVIDENCIAS.md, Seção 15'},

   {'titulo': 'Stream: a mensagem fica pendente até ser confirmada',
    'linguagem': 'bash',
    'codigo': 'XGROUP CREATE stream:pedidos grupo:processadores 0 MKSTREAM\n'
              'XREADGROUP GROUP grupo:processadores consumidor:1 COUNT 10 \\\n'
              '           STREAMS stream:pedidos >\n'
              'XPENDING stream:pedidos grupo:processadores\n\n'
              'XACK stream:pedidos grupo:processadores 1790540869274-0\n'
              'XPENDING stream:pedidos grupo:processadores',
    'saida': 'XPENDING antes -> 2 mensagens pendentes\n'
             'XACK           -> 1\n'
             'XPENDING depois-> 1 mensagem pendente',
    'explicacao': 'O `>` pede apenas mensagens nunca entregues ao grupo — repetir o comando devolve '
      'vazio. As entregues ficam pendentes até o `XACK`. Se o consumidor morrer agora, a mensagem '
      'restante não se perde: outro consumidor pode reivindicá-la. É precisamente a garantia que o '
      'Pub/Sub não tem, onde publicar sem assinante devolve 0 e a mensagem desaparece.',
    'fonte': 'Lab 3, PARTE2-EVIDENCIAS.md, Seção 12'},

   {'titulo': 'O reinício que prova duas coisas de uma vez',
    'linguagem': 'bash',
    'codigo': '# antes do reinício\n'
              'CONFIG SET maxmemory 512mb\n'
              'CONFIG SET maxmemory-policy allkeys-lru\n'
              'SET persist:test "ok"\n\n'
              '$ docker restart redis\n\n'
              '# depois\n'
              'GET persist:test\n'
              'CONFIG GET maxmemory\n'
              'CONFIG GET maxmemory-policy',
    'saida': 'GET persist:test      -> "ok"           (o dado sobreviveu)\n'
             'CONFIG GET maxmemory  -> 0              (voltou ao padrão)\n'
             'CONFIG GET maxmemory-policy -> noeviction',
    'explicacao': 'O dado persistiu porque o AOF foi habilitado nos argumentos do contêiner — '
      'configuração declarada, que sobrevive. Os 512 MB e o `allkeys-lru`, definidos por `CONFIG SET`, '
      'evaporaram. A lição está no contraste: o que está declarado persiste, o que foi ajustado em '
      'tempo de execução não.',
    'fonte': 'Lab 3, PARTE2-EVIDENCIAS.md, Seções 16.3 e 19'},
 ],
 'fechamento': 'O Redis vai muito além do cache de strings, e o fio comum das estruturas deste módulo é a '
   'troca consciente: bitmap e HyperLogLog trocam detalhe por memória; Stream troca simplicidade por '
   'garantia; RDB troca durabilidade por compactação. Saber o que se está abrindo mão é a competência '
   'real. Falta agora juntar os três sistemas da disciplina.',
 'perguntas': [
   'Você precisa saber quantos usuários únicos acessaram o site no mês. HyperLogLog ou Set? O que muda na resposta se depois pedirem a lista de quem acessou?',
   'Por que um bitmap de presença com IDs de usuário esparsos (1, 5000, 900000) pode ser um desperdício?',
   'Sua fila de e-mails usa Pub/Sub e alguns e-mails não são enviados. Qual a causa provável?',
   'Uma instância guarda cache e também locks distribuídos. Que política de eviction você escolhe?',
 ],
})
