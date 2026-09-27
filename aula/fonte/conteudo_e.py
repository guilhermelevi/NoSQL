#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modulo de sintese: os tres sistemas juntos. Fecha a aula."""

MODULOS = []

MODULOS.append({
 'tema': 'sintese',
 'titulo': 'Os três juntos: registro, busca e latência',
 'duracao_min': 35,
 'abertura': 'Os três laboratórios pareciam exercícios separados. Não eram: juntos, eles montam a '
             'arquitetura que aparece em quase todo sistema de porte — e respondem à pergunta de qual '
             'banco usar com um "os três, em camadas diferentes".',
 'objetivos': [
   'Descrever o fluxo MongoDB → GELF → Logstash → Elasticsearch → Kibana e o papel de cada peça.',
   'Explicar por que o acoplamento entre os sistemas é unidirecional e o que isso garante.',
   'Avaliar a escolha de UDP para transporte de log, com o que ela ganha e o que sacrifica.',
   'Posicionar o Redis como camada de latência e reconhecer o problema de invalidação que ele cria.',
   'Aplicar o critério de decisão entre os três sistemas a requisitos concretos.',
 ],
 'conceitos': [
   {'nome': 'O fluxo do Lab 2, peça por peça',
    'explicacao': 'O MongoDB escreve log na saída padrão, como qualquer processo. O driver de log GELF '
      'do Docker intercepta essa saída e a envia por UDP para a porta 12201. O Logstash escuta ali, '
      'aplica o pipeline configurado e escreve no Elasticsearch, num índice nomeado por data. O Kibana '
      'lê o Elasticsearch e apresenta. Nenhuma peça conhece as outras além da vizinha imediata: trocar o '
      'Elasticsearch por outro destino exigiria mudar apenas o output do Logstash.',
    'analogia': 'Uma esteira de triagem postal. Cada posto sabe de onde recebe e para onde entrega, e '
      'nenhum precisa conhecer o percurso inteiro.'},

   {'nome': 'Acoplamento de um lado só',
    'explicacao': 'O MongoDB não sabe que o Elasticsearch existe. Ele apenas emite log, e emitiria da '
      'mesma forma se ninguém estivesse escutando. Essa direção única é o que torna a arquitetura '
      'resiliente: derrubar toda a camada de busca não afeta a capacidade do banco de aceitar escritas. '
      'A recíproca não vale — sem a fonte, o índice derivado deixa de ser alimentado.',
    'erro_comum': 'Inverter a dependência, fazendo a aplicação escrever primeiro no Elasticsearch e '
      'depois no banco principal. Qualquer indisponibilidade da busca passa a derrubar a escrita.'},

   {'nome': 'UDP: troca garantia por isolamento',
    'explicacao': 'GELF sobre UDP não estabelece conexão nem confirma entrega. A consequência boa é que '
      'o contêiner sobe e opera mesmo com o Logstash fora do ar — os pacotes são descartados e nada '
      'bloqueia. A ruim é que não há garantia: sob perda de rede ou sobrecarga, linhas de log somem sem '
      'aviso. Para telemetria o compromisso é razoável; para auditoria, não. Repare que é a mesma '
      'escolha do Pub/Sub do Redis: entrega a quem está ouvindo, e quem não estava perdeu.',
    'erro_comum': 'Usar um pipeline best-effort para trilha de auditoria com valor legal. No dia em que '
      'faltar a linha crítica, não haverá como saber se ela nunca existiu ou se foi perdida.'},

   {'nome': 'A terceira camada: latência',
    'explicacao': 'MongoDB responde "qual o estado deste registro, com garantia". Elasticsearch responde '
      '"que documentos são relevantes para esta pergunta". Redis responde "qual o valor agora, no menor '
      'tempo possível" — e aceita perdê-lo. As três perguntas exigem estruturas de dados diferentes, e é '
      'por isso que nenhum sistema responde bem às três. O Redis não é um banco menor: é um banco com '
      'outro compromisso, em que a memória volátil é característica de projeto e não limitação.',
    'analogia': 'A biblioteca tem o acervo, o catálogo e a mesa onde os livros em uso ficam abertos. '
      'Perder a mesa custa alguns minutos; perder o catálogo custa um mutirão; perder o acervo é '
      'irreversível.'},

   {'nome': 'O índice de busca e o cache nunca são a fonte da verdade',
    'explicacao': 'Este é o princípio que organiza tudo. Elasticsearch e Redis são derivados: se forem '
      'perdidos, reconstroem-se a partir da fonte. Se a fonte for perdida, viram uma coleção de '
      'afirmações sobre dados que não existem mais. Daí duas consequências de projeto: todo pipeline de '
      'indexação precisa ser reexecutável do zero, e todo cache precisa tolerar estar vazio — se o '
      'sistema não funciona com o cache frio, ele não tem um cache, tem uma dependência.',
    'erro_comum': 'Gravar no Redis algo que não existe em nenhum outro lugar — um contador de uso '
      'faturável, o estado de um carrinho. No dia do reinício sem persistência, o dado simplesmente não '
      'volta.'},

   {'nome': 'A invalidação, que é o preço do cache',
    'explicacao': 'Cachear é duplicar, e toda duplicata pode divergir. O TTL limita por quanto tempo a '
      'divergência dura, mas não a impede: se o registro mudar no MongoDB, o Redis continua servindo o '
      'valor antigo até o prazo vencer. Quando isso não é tolerável, é preciso invalidar explicitamente '
      'no momento da escrita — apagar a chave no mesmo fluxo que atualiza o banco. É por isso que a '
      'famosa frase sobre as duas coisas difíceis em computação cita nomear coisas e invalidar cache.',
    'erro_comum': 'Escolher um TTL longo por medo de sobrecarregar o banco e conviver com dados '
      'desatualizados que ninguém consegue explicar. O TTL é um limite superior para a inconsistência — '
      'defini-lo é decidir quanta divergência se aceita.'},

   {'nome': 'O critério de escolha, sem falso dilema',
    'explicacao': 'A pergunta útil não é "qual banco é melhor", é "que pergunta este dado precisa '
      'responder, com que garantia e em quanto tempo". Estado atual com escrita confirmada e transação: '
      'MongoDB. Relevância em texto livre, agregação exploratória, busca semântica: Elasticsearch. '
      'Leitura em microssegundos, contador atômico, estado efêmero com prazo: Redis. Quando um sistema '
      'precisa das três coisas — e a maioria precisa —, a resposta é os três, com fluxo de sincronização '
      'explícito e a verdade morando em um só lugar.',
    'erro_comum': 'Escolher um único sistema para tudo e depois forçá-lo no papel para o qual não foi '
      'feito: busca por relevância com regex no MongoDB, banco transacional no Elasticsearch, ou dado '
      'de negócio que só existe no Redis.'},
 ],
 'demos': [
   {'titulo': 'O pipeline do Lab 2 em treze linhas',
    'linguagem': 'json',
    'codigo': '# lab02-elastic/logstash/pipeline/logstash.conf\n'
              'input {\n'
              '  gelf { port => 12201 }\n'
              '}\n\n'
              'output {\n'
              '  elasticsearch {\n'
              '    hosts => ["http://elasticsearch:9200"]\n'
              '    index => "mongodb-logs-%{+YYYY.MM.dd}"\n'
              '  }\n'
              '  stdout { codec => rubydebug }\n'
              '}',
    'saida': 'health status index                   docs.count\n'
             'yellow open   mongodb-logs-2026.09.08        160\n'
             'yellow open   mongodb-logs-2026.09.09         86',
    'explicacao': 'Dois índices, um por dia — a rotação vem do padrão de data no nome. É exatamente esse '
      'formato que justifica o index template: índices que nascem sozinhos precisam de mapping declarado '
      'antes.',
    'fonte': 'lab02-elastic/logstash/pipeline/logstash.conf'},

   {'titulo': 'A prova de que o acoplamento é de um lado só',
    'linguagem': 'bash',
    'codigo': '# durante a reorganizacao do repositorio, toda a camada de busca foi derrubada:\n'
              '$ cd lab02-elastic && docker compose down\n'
              '$ cd ../lab01-mongodb && docker compose up -d   # MongoDB sobe normalmente\n\n'
              '# e ao religar, o fluxo recomeca sozinho:\n'
              '$ curl -s "localhost:9200/_cat/indices/mongodb-logs-*?v"',
    'saida': 'yellow open mongodb-logs-2026.09.09   86 docs',
    'explicacao': 'O MongoDB subiu com o Logstash fora do ar, sem erro e sem espera — porque GELF é UDP '
      'e não bloqueia. Os logs daquele intervalo foram perdidos, o que é aceitável para telemetria. Ao '
      'religar a camada de busca, a indexação recomeçou sem nenhuma intervenção.',
    'fonte': 'Reorganização do repositório, 08/09/2026'},

   {'titulo': 'A mesma pergunta nos três sistemas',
    'linguagem': 'javascript',
    'codigo': '// MongoDB — agregar por categoria\n'
              'db.transacoes.aggregate([\n'
              '  { $group: { _id: "$tipo", total: { $sum: 1 } } }\n'
              ']);\n\n'
              '// Elasticsearch — a mesma pergunta\n'
              'GET transacoes/_search\n'
              '{ "size": 0, "aggs": { "por_tipo": { "terms": { "field": "tipo" } } } }\n\n'
              '// Redis — a contagem ja pronta, mantida a cada escrita\n'
              'INCR transacoes:tipo:compra\n'
              'GET  transacoes:tipo:compra',
    'saida': 'MongoDB:       [ { _id: "compra", total: 12 }, { _id: "venda", total: 10 } ]\n'
             'Elasticsearch: [ { key: "compra", doc_count: 12 }, { key: "venda", doc_count: 10 } ]\n'
             'Redis:         "12"',
    'explicacao': 'Os dois primeiros **calculam** a resposta no momento da pergunta, percorrendo os '
      'dados. O Redis não calcula nada: devolve um número que foi mantido atualizado a cada escrita. É a '
      'troca central da camada de latência — trabalho antecipado na escrita em troca de leitura '
      'constante. O custo é que esse contador pode divergir se alguma escrita não passar pelo caminho '
      'que o incrementa.',
    'fonte': 'GABARITO.md Parte 12, PARTE2-EVIDENCIAS.md 12.9 e Lab 3 Seção 5.3'},

   {'titulo': 'A arquitetura completa, nos contêineres',
    'linguagem': 'bash',
    'codigo': '$ docker ps --format "table {{.Names}}\\t{{.Status}}"',
    'saida': 'NAMES               STATUS\n'
             'redis               Up (healthy)\n'
             'redisinsight        Up\n'
             'elasticsearch       Up (healthy)\n'
             'kibana              Up\n'
             'logstash            Up\n'
             'mongodb-container   Up',
    'explicacao': 'Seis contêineres, três bancos, três papéis. Nenhum dado de negócio é escrito '
      'diretamente no Elasticsearch ou no Redis: tudo que chega neles foi derivado de outra fonte. Essa '
      'frase é o resumo da disciplina inteira.',
    'fonte': 'Ambiente dos Labs 1, 2 e 3'},
 ],
 'fechamento': 'A competência que esta aula pretende deixar não é sintaxe de nenhum dos três — isso está '
   'na documentação. É saber formular a pergunta certa diante de um requisito: que garantia este dado '
   'exige, em quanto tempo ele precisa ser lido, que pergunta ele precisa responder, e onde mora a '
   'verdade. Respondido isso, a escolha da ferramenta é quase automática — e, com mais frequência do que '
   'parece, a resposta certa é mais de uma.',
 'perguntas': [
   'Se o Elasticsearch e o Redis são reconstruíveis, por que fazer backup deles?',
   'Sua aplicação precisa que uma alteração no MongoDB apareça na busca em menos de um segundo. O pipeline de log serve? O que você usaria?',
   'Você cacheia no Redis o perfil do usuário com TTL de 1 hora. O usuário troca a foto e reclama que a antiga continua aparecendo. O que fazer, e qual o custo de cada alternativa?',
   'Que perguntas você faria a um time que propõe guardar o carrinho de compras apenas no Redis?',
   'Onde mora a fonte da verdade no sistema em que você trabalha ou estuda, e como você sabe disso?',
 ],
})
