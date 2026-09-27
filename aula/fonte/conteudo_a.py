#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modulos 1 a 4 da aula (contexto + MongoDB)."""

MODULOS = []

# =====================================================================
MODULOS.append({
 'tema': 'neutro',
 'titulo': 'Por que NoSQL: o problema antes da solução',
 'duracao_min': 25,
 'abertura': 'O modelo relacional resolve bem um conjunto de problemas há cinquenta anos. '
             'A pergunta desta aula não é o que há de errado com ele — é que problemas apareceram '
             'depois que ele já estava consolidado, e por que exigiram estruturas diferentes.',
 'objetivos': [
   'Identificar as três pressões concretas que motivaram os bancos não relacionais: esquema móvel, escala horizontal e busca por relevância.',
   'Situar MongoDB, Elasticsearch e Redis dentro da taxonomia NoSQL, sabendo dizer a que família cada um pertence.',
   'Enunciar o teorema CAP com precisão, incluindo o que a versão popular dele distorce.',
   'Sustentar a tese central da aula: os três sistemas dos laboratórios não competem entre si, ocupam camadas diferentes.',
 ],
 'conceitos': [
   {'nome': 'NoSQL não quer dizer "sem SQL"',
    'explicacao': 'O termo pegou como "Not Only SQL". Ele não descreve uma tecnologia, descreve uma '
      'recusa: a de tratar tabela com esquema fixo como a única forma de organizar dados. O que une '
      'sistemas tão diferentes quanto Redis, Cassandra, Neo4j, MongoDB e Elasticsearch não é uma '
      'característica comum positiva — é o fato de nenhum deles ser um banco relacional. Por isso '
      'a pergunta "NoSQL é melhor que SQL?" não tem resposta: é como perguntar se um veículo terrestre '
      'é melhor que um Fusca.',
    'erro_comum': 'Tratar NoSQL como categoria única e concluir que "NoSQL não tem transação" ou '
      '"NoSQL não tem esquema". O MongoDB tem transação multi-documento desde a versão 4.0 e permite '
      'validação de esquema por coleção. A generalização é falsa para praticamente qualquer afirmação.'},

   {'nome': 'A taxonomia: cinco famílias, três representantes',
    'explicacao': 'Chave-valor (DynamoDB, Memcached) guarda um valor sob uma chave, em geral sem saber '
      'o que há dentro. Documento (MongoDB, CouchDB) guarda estruturas aninhadas e sabe consultar campos '
      'dentro delas. Coluna larga (Cassandra, HBase) organiza por família de colunas e otimiza escrita em '
      'volume. Grafo (Neo4j) trata a relação como cidadã de primeira classe. Motor de busca '
      '(Elasticsearch, Solr) inverte o problema: em vez de ir do documento ao conteúdo, vai do termo aos '
      'documentos. O Redis costuma ser classificado como chave-valor, mas a rigor escapa da caixa: o '
      'valor não é opaco, é uma estrutura que o servidor sabe manipular — daí o nome que ele próprio '
      'usa, data structure server. Os três laboratórios cobriram documento, motor de busca e chave-valor, '
      'justamente as famílias que mais aparecem juntas num mesmo sistema.',
    'analogia': 'Chave-valor clássico é o guarda-volumes: você entrega uma mala, recebe uma ficha, e '
      'ninguém olha dentro. Documento é o arquivo de pastas: cada pasta tem estrutura própria e dá para '
      'procurar por um campo específico. Motor de busca é o índice remissivo no fim do livro: não guarda '
      'o texto, guarda em que páginas cada palavra aparece. E o Redis é a mesa de trabalho: o que está '
      'ao alcance da mão agora, já organizado na forma em que vai ser usado.'},

   {'nome': 'ACID e BASE',
    'explicacao': 'ACID (atomicidade, consistência, isolamento, durabilidade) é a garantia de que uma '
      'transação ou acontece inteira ou não acontece. BASE (basically available, soft state, eventually '
      'consistent) troca parte dessa garantia por disponibilidade e escala: aceita-se que réplicas '
      'divirjam por um intervalo, desde que convirjam depois. A escolha não é ideológica, é de domínio: '
      'saldo bancário exige ACID; contador de visualizações de vídeo tolera BASE com folga.',
    'erro_comum': 'Assumir que "NoSQL é BASE". O MongoDB com write concern majority e read concern '
      'majority oferece garantias fortes; o Elasticsearch, por outro lado, é near real-time por projeto '
      'e nunca deve ser tratado como fonte da verdade transacional.'},

   {'nome': 'Teorema CAP, com honestidade',
    'explicacao': 'O enunciado correto é: quando ocorre uma partição de rede (P), o sistema precisa '
      'escolher entre continuar respondendo com dado possivelmente desatualizado (A) ou recusar a '
      'resposta para não violar consistência (C). Não é "escolha dois dos três" no dia a dia: partição '
      'de rede não é uma opção de projeto, é um evento que acontece. Fora de partição, um sistema pode '
      'perfeitamente ser consistente e disponível ao mesmo tempo. A formulação PACELC é mais útil: '
      'na partição, escolha entre A e C; caso contrário (Else), escolha entre latência (L) e consistência (C).',
    'erro_comum': 'Dizer que "MongoDB é CP e Cassandra é AP" como se fosse propriedade fixa. Em ambos, '
      'o comportamento depende de configuração — write concern, read preference, nível de consistência '
      'por consulta. A classificação é de configuração, não de produto.'},

   {'nome': 'A tese desta aula',
    'explicacao': 'Os laboratórios não foram exercícios independentes. O Lab 2 montou, sem anunciar, uma '
      'arquitetura de produção clássica: o MongoDB do Lab 1 emitindo logs, o Logstash recebendo, o '
      'Elasticsearch indexando, o Kibana exibindo. O Lab 3 trouxe a terceira peça. A divisão de trabalho é '
      'esta: um sistema guarda a verdade com garantia de escrita; outro constrói um índice derivado, '
      'otimizado para uma pergunta que o primeiro responde mal; o terceiro mantém em memória o estado que '
      'precisa ser lido em microssegundos e que pode ser perdido sem tragédia. Toda a aula volta a esse ponto.',
    'analogia': 'Uma biblioteca tem o acervo e tem o catálogo. O acervo é a verdade: se o catálogo '
      'sumir, reconstrói-se a partir dos livros. Se o acervo sumir, o catálogo vira uma lista de coisas '
      'que não existem mais. O Elasticsearch é o catálogo.'},
 ],
 'demos': [
   {'titulo': 'A arquitetura que o laboratório montou sem dizer',
    'linguagem': 'bash',
    'codigo': '$ docker ps --format "table {{.Names}}\\t{{.Status}}"',
    'saida': 'NAMES               STATUS\n'
             'mongodb-container   Up 11 hours\n'
             'kibana              Up 11 hours\n'
             'logstash            Up 11 hours\n'
             'elasticsearch       Up 11 hours (healthy)',
    'explicacao': 'Quatro contêineres, dois bancos, dois papéis. O MongoDB é o sistema de registro. '
      'Os outros três formam a camada de busca e observabilidade. Nenhum documento de negócio é escrito '
      'diretamente no Elasticsearch: tudo que chega lá foi derivado de outra fonte.',
    'fonte': 'Ambiente dos Labs 1 e 2, verificado em 09/09/2026'},

   {'titulo': 'O elo entre os dois laboratórios está em três linhas de configuração',
    'linguagem': 'yaml',
    'codigo': '# lab01-mongodb/docker-compose.yml\n'
              'logging:\n'
              '  driver: gelf\n'
              '  options:\n'
              '    gelf-address: "udp://localhost:12201"\n'
              '    tag: "mongodb-log"',
    'saida': 'health status index                   docs.count\n'
             'yellow open   mongodb-logs-2026.09.09        86',
    'explicacao': 'O driver de log GELF do Docker desvia a saída do MongoDB para a porta 12201/UDP, '
      'onde o Logstash escuta. O MongoDB não sabe que o Elasticsearch existe, e o Elasticsearch não '
      'sabe o que é um MongoDB. O acoplamento é de um lado só, e por isso o sistema tolera a queda '
      'da camada de busca.',
    'fonte': 'lab01-mongodb/docker-compose.yml e logstash/pipeline/logstash.conf'},
 ],
 'fechamento': 'Guarde a divisão de papéis: um sistema responde "qual é o estado atual deste registro?" '
   'com garantia; o outro responde "que documentos são relevantes para esta pergunta?" com velocidade. '
   'Os próximos três módulos tratam do primeiro. Depois, os três seguintes tratam do segundo.',
 'perguntas': [
   'Se o MongoDB do laboratório sabe emitir log e o Elasticsearch sabe indexá-lo, por que não gravar o log direto no Elasticsearch e eliminar o Logstash?',
   'Um sistema de e-commerce precisa de catálogo com busca por texto e de carrinho com consistência forte. Que arranjo você proporia, e onde ficaria a fonte da verdade?',
   'Em que situação concreta você aceitaria que dois usuários vissem valores diferentes do mesmo dado por alguns segundos?',
 ],
})

# =====================================================================
MODULOS.append({
 'tema': 'mongo',
 'titulo': 'MongoDB: o modelo de documento e o CRUD',
 'duracao_min': 45,
 'abertura': 'Um documento não é uma linha com JSON dentro. A diferença muda como se modela, como se '
             'consulta e onde se erra — e o primeiro laboratório produziu vários desses erros de forma '
             'instrutiva.',
 'objetivos': [
   'Explicar a hierarquia database → coleção → documento e por que a criação é preguiçosa.',
   'Distinguir BSON de JSON e prever o efeito prático da tipagem numa consulta.',
   'Usar os operadores de atualização corretamente, sabendo o que acontece quando se omite o $set.',
   'Escolher entre deleteOne e deleteMany com consciência do risco de cada um.',
   'Aplicar o princípio do menor privilégio com roles de banco.',
 ],
 'conceitos': [
   {'nome': 'Criação preguiçosa de banco e coleção',
    'explicacao': 'O comando use não escreve nada em disco: ele apenas aponta a variável db para um '
      'nome. O banco passa a existir no momento em que o primeiro documento é gravado, e o mesmo vale '
      'para a coleção. Por isso o createCollection é opcional — ele só é necessário quando se precisa '
      'declarar alguma opção no ato da criação, como validação de esquema, coleção capped (tamanho fixo, '
      'sobrescrevendo os documentos mais antigos) ou time-series. Fora desses casos, ele serve apenas '
      'para tornar a intenção explícita no código.',
    'erro_comum': 'Rodar um update contra uma coleção cujo nome foi digitado errado. O MongoDB não '
      'reclama: ele cria a coleção vazia e reporta zero documentos modificados. O erro passa despercebido '
      'porque não há mensagem de erro — foi exatamente o que aconteceu na Parte 7 do Lab 1, cujo roteiro '
      'mandava usar db.estudantes numa altura em que a coleção ainda se chamava alunos.'},

   {'nome': 'BSON: a tipagem que o JSON não tem',
    'explicacao': 'O MongoDB armazena BSON, um formato binário que estende o JSON com tipos que o JSON '
      'não possui: inteiro de 32 e 64 bits, double, decimal128, data, binário, ObjectId. Isso não é '
      'detalhe de implementação — é o que permite comparar datas e números corretamente. A string "60" '
      'e o número 60 são valores distintos e uma busca por um não encontra o outro. Pior: o operador '
      '$gt aplicado a strings compara em ordem alfabética, de modo que "9" é maior que "10".',
    'erro_comum': 'Importar dados de CSV sem converter tipos e depois estranhar que { idade: { $gt: 20 } } '
      'não retorne ninguém, porque todas as idades foram gravadas como string.'},

   {'nome': 'ObjectId: doze bytes que carregam informação',
    'explicacao': 'Quando não se fornece um _id, o driver gera um ObjectId de 12 bytes: 4 bytes de '
      'timestamp Unix, 5 bytes de valor aleatório por processo e 3 bytes de contador incremental. '
      'Duas consequências práticas: ordenar por _id ordena aproximadamente por ordem de inserção, e o '
      'identificador é gerado no cliente, o que permite inserir sem ida ao servidor para reservar um '
      'número — diferente de uma sequência de banco relacional.',
    'analogia': 'É uma etiqueta de encomenda que já traz a data e a agência de origem impressas. '
      'Você não precisa consultar a central para saber quando foi postada.'},

   {'nome': 'Cursor: find devolve um ponteiro, não os dados',
    'explicacao': 'O find() devolve um cursor — uma referência que o servidor vai entregando em lotes, '
      'para não carregar toda a coleção na memória de uma vez. É por isso que ele aceita encadear '
      '.sort(), .limit() e .skip(): esses métodos alteram a consulta antes de ela ser executada, não '
      'filtram um resultado já pronto. O findOne() devolve o documento em si e por isso não aceita '
      'encadeamento algum.',
    'erro_comum': 'Usar .skip() com valores altos para paginar. O servidor precisa percorrer e descartar '
      'todos os documentos pulados, então a página 1000 custa muito mais que a página 1. Paginação por '
      'faixa de valor (range pagination) escala; skip não.'},

   {'nome': 'O $set é obrigatório — e omiti-lo destrói o documento',
    'explicacao': 'Os operadores de atualização dizem o que fazer com o documento encontrado. O $set '
      'cria o campo se não existir e sobrescreve se existir; o $unset remove a chave; o $inc soma; o '
      '$push acrescenta a um array. Se o segundo argumento do updateOne não usar operador nenhum, o '
      'MongoDB interpreta como substituição integral: o documento inteiro vira o objeto passado, e todo '
      'campo que não estava ali é perdido.',
    'erro_comum': 'Escrever updateOne({nome:"Ana Costa"}, {idade:24}) esperando alterar só a idade. '
      'O resultado é um documento que contém apenas idade: 24 — nome, curso e todo o resto foram apagados, '
      'sem aviso.'},

   {'nome': 'Remover a chave não é gravar null',
    'explicacao': 'Depois de um $unset, o campo deixa de existir no documento e passa a ser encontrado '
      'por { campo: { $exists: false } }. Se em vez disso fosse gravado null, o campo continuaria '
      'existindo com valor nulo, e a consulta por $exists: false não o encontraria. A distinção importa '
      'em agregação: campos ausentes são ignorados pelo $avg, enquanto null participa da conta.',
    'analogia': 'Apagar a linha do formulário é diferente de escrever "não se aplica" nela. Nos dois '
      'casos não há valor útil, mas só no segundo há registro de que a pergunta foi feita.'},

   {'nome': 'matchedCount e modifiedCount são números diferentes',
    'explicacao': 'O retorno de um update informa quantos documentos casaram com o filtro (matchedCount) '
      'e quantos efetivamente mudaram (modifiedCount). Eles divergem quando o valor novo é igual ao que '
      'já estava gravado: o documento casou, mas nada foi escrito. Ler os dois números é a forma de '
      'saber se a operação fez o que se esperava.',
    'erro_comum': 'Verificar apenas modifiedCount e concluir que o filtro não encontrou nada, quando na '
      'verdade encontrou e o dado já estava correto.'},

   {'nome': 'Menor privilégio com roles',
    'explicacao': 'O usuário é criado dentro de um banco, e esse banco vira o authSource dele — o lugar '
      'onde o servidor procura a credencial ao autenticar. A role read libera find, count e aggregate; '
      'a readWrite acrescenta insert, update, delete, createCollection e createIndex. Nenhuma das duas '
      'permite criar usuário ou alterar permissão, o que exige roles administrativas. O ponto crucial '
      'é que a permissão é verificada pelo servidor a cada operação, não no momento da conexão.',
    'erro_comum': 'Concluir que a credencial está correta porque a conexão foi aceita. Um usuário com '
      'role read conecta normalmente e só descobre o limite quando tenta escrever.'},
 ],
 'demos': [
   {'titulo': 'Tipagem: o que se grava é o que se busca',
    'linguagem': 'javascript',
    'codigo': 'db.disciplinas.insertMany([\n'
              '  { nome: "Bancos de Dados Não Relacionais", carga_horaria: 60, obrigatoria: true },\n'
              '  { nome: "Tópicos em Big Data", carga_horaria: 40, obrigatoria: false }\n'
              ']);',
    'explicacao': 'carga_horaria é número e obrigatoria é booleano — não são strings. A escolha parece '
      'trivial no insert e cobra o preço na consulta: gravado como "60", o campo não é encontrado por '
      '{ carga_horaria: 60 } nem comparado corretamente por $gt.',
    'fonte': 'GABARITO.md, Parte 5, EX 5.2'},

   {'titulo': 'Esquema flexível e o preço dele na agregação',
    'linguagem': 'javascript',
    'codigo': 'db.alunos.insertOne({ nome: "Lucas Moreira", idade: 26,\n'
              '                     curso: "Data Science", cidade: "Brasília" });\n\n'
              '// mais tarde, agrupando por um campo que só um documento tem:\n'
              'db.estudantes.aggregate([\n'
              '  { $group: { _id: "$cidade", total: { $sum: 1 } } }\n'
              ']);',
    'saida': '[ { _id: null, total: 2 }, { _id: "Brasília", total: 1 } ]',
    'explicacao': 'O banco aceitou um documento com um campo que nenhum outro possui, sem reclamar. '
      'A conta chega no $group: todo documento sem o campo de agrupamento cai num grupo de _id: null. '
      'Isso não é erro, é a regra — mas quem não a conhece lê o resultado como se fosse defeito de dados.',
    'fonte': 'GABARITO.md, Parte 5 (EX 5.3) e Parte 10 (EX 10.3)'},

   {'titulo': 'A permissão é verificada a cada operação, não na conexão',
    'linguagem': 'bash',
    'codigo': 'db.createUser({\n'
              '  user: "leitura_user", pwd: "senha123",\n'
              '  roles: [ { role: "read", db: "dbNoSQLBD" } ]\n'
              '});\n\n'
              '$ mongosh "mongodb://leitura_user:senha123@localhost:27017/dbNoSQLBD"\n'
              '> db.estudantes.find()      // funciona\n'
              '> db.estudantes.insertOne({ nome: "teste" })',
    'saida': 'MongoServerError: not authorized on dbNoSQLBD to execute command insert',
    'explicacao': 'A conexão foi aceita sem qualquer aviso. O limite só apareceu na primeira escrita. '
      'É esse o comportamento que torna o menor privilégio uma defesa real: se a credencial de um serviço '
      'de relatório vazar, o atacante herda apenas leitura.',
    'fonte': 'GABARITO.md, Parte 11, EX 11.2'},

   {'titulo': 'deleteMany não tem desfazer',
    'linguagem': 'javascript',
    'codigo': '// disciplina de trabalho: rodar o filtro como find antes\n'
              'db.temp.find({});          // 1. conferir na tela o que vai sumir\n'
              'db.temp.deleteMany({});    // 2. só então trocar find por deleteMany',
    'saida': '{ acknowledged: true, deletedCount: 3 }',
    'explicacao': 'A coleção temp continuou existindo, vazia, com seus índices — deleteMany remove '
      'documentos, não a coleção. Quem apaga a coleção do catálogo é o drop(). Fora de transação não '
      'há rollback, então conferir o filtro com find antes é a única rede de proteção.',
    'fonte': 'GABARITO.md, Parte 8, EX 8.2 e 8.3'},
 ],
 'fechamento': 'O modelo de documento troca a rigidez do esquema por flexibilidade, e cobra essa troca '
   'em disciplina: tipos consistentes, operadores explícitos e conferência antes de apagar. Com o CRUD '
   'estabelecido, a próxima pergunta é como extrair informação agregada de uma coleção — que é onde o '
   'MongoDB se distancia de vez do modelo relacional.',
 'perguntas': [
   'Por que o MongoDB não avisa quando você atualiza uma coleção que não existe? Que decisão de projeto está por trás disso?',
   'Um campo ausente e um campo com null se comportam igual no find? E no $avg?',
   'Se ordenar por _id equivale a ordenar por data de inserção, por que ainda assim gravar um campo criado_em?',
   'Que role você daria a um serviço que gera relatórios noturnos, e por quê?',
 ],
})

# =====================================================================
MODULOS.append({
 'tema': 'mongo',
 'titulo': 'MongoDB: o Aggregation Framework',
 'duracao_min': 40,
 'abertura': 'O find responde "quais documentos". A agregação responde "o que esses documentos dizem '
             'em conjunto". A diferença entre as duas perguntas é a diferença entre consultar e analisar.',
 'objetivos': [
   'Descrever o pipeline como sequência de estágios e prever o formato da saída de cada um.',
   'Posicionar o $match corretamente e justificar a posição em termos de desempenho.',
   'Explicar por que $lookup devolve array e o que o $unwind faz com ele.',
   'Reconhecer quando $facet economiza uma passada sobre os dados.',
 ],
 'conceitos': [
   {'nome': 'O pipeline é uma esteira',
    'explicacao': 'Cada estágio recebe o que o anterior devolveu e entrega ao seguinte. Isso significa '
      'que a ordem não é estilo, é semântica: o mesmo conjunto de estágios em ordem diferente produz '
      'resultado diferente. O cifrão antes do nome do campo significa "o valor deste campo"; sem ele, '
      'seria a string literal. No $group, o _id define o critério de agrupamento, e _id: null junta '
      'tudo num resultado único.',
    'analogia': 'Uma linha de produção. Cada posto recebe a peça do posto anterior, faz uma coisa só, '
      'e passa adiante. Trocar dois postos de lugar muda o produto final.'},

   {'nome': '$match antes é WHERE, $match depois é HAVING',
    'explicacao': 'Colocado antes do $group, o $match filtra documentos crus — equivale ao WHERE do SQL, '
      'reduz o volume que entra na agregação e, o mais importante, ainda consegue usar índice. Colocado '
      'depois do $group, filtra o resultado já agregado — equivale ao HAVING, e é a única posição em que '
      'se pode filtrar por um campo calculado, como uma média que não existia antes do agrupamento. '
      'A regra prática: empurre o $match o mais para cima que a semântica permitir.',
    'erro_comum': 'Filtrar depois do $group por um critério que poderia ter sido aplicado antes. '
      'O resultado é o mesmo, mas o custo não: agrupou-se documento que seria descartado, e sem índice.'},

   {'nome': '$avg ignora ausente, $sum: 1 conta todo mundo',
    'explicacao': 'O $avg desconsidera documentos em que o campo não existe, em vez de tratá-los como '
      'zero. É o comportamento desejável: uma média de notas não deve ser puxada para baixo por alunos '
      'que ainda não têm nota lançada. Já o $sum: 1 conta o documento independentemente de ter ou não '
      'o campo, porque está somando a constante 1, não o campo. Confundir os dois produz relatório errado '
      'que parece certo.',
    'erro_comum': 'Calcular média dividindo $sum do campo por $sum: 1. O numerador ignora ausentes e o '
      'denominador não, então a média sai menor que a real.'},

   {'nome': 'Ordem dos branches no $switch',
    'explicacao': 'O $switch avalia os branches em sequência e o primeiro caso verdadeiro vence — os '
      'demais nem são testados. Numa classificação por faixas, isso obriga a ir da condição mais restritiva '
      'para a mais frouxa. Se { $gte: 7 } vier antes de { $gte: 9 }, a nota 9,7 será classificada como B, '
      'porque satisfaz o primeiro teste. Documentos que não satisfazem nenhum branch caem no default.',
    'erro_comum': 'Escrever as faixas em ordem crescente, por parecer mais natural de ler, e obter '
      'classificação sempre colada na faixa mais baixa.'},

   {'nome': '$lookup devolve array, sempre',
    'explicacao': 'O $lookup faz o equivalente a um LEFT OUTER JOIN, mas o resultado vai para um campo '
      'no formato de array, mesmo quando apenas um documento casou — e um array vazio quando nenhum casou. '
      'Para achatar isso no formato de junção do SQL, usa-se o $unwind, que produz um documento por item '
      'do array. Atenção: por padrão o $unwind descarta documentos cujo array veio vazio, o que silenciosamente '
      'transforma o LEFT JOIN em INNER JOIN. Para preservá-los, é preciso preserveNullAndEmptyArrays: true.',
    'erro_comum': 'Fazer $lookup seguido de $unwind e perceber depois que os registros sem correspondência '
      'sumiram do relatório — sem nenhuma mensagem indicando isso.'},

   {'nome': '$facet: vários pipelines, uma passada',
    'explicacao': 'O $facet executa múltiplos pipelines independentes sobre a mesma entrada e devolve '
      'todos os resultados num único documento. Serve para painéis, em que se quer contagem total, máximo '
      'e distribuição ao mesmo tempo, sem varrer a coleção três vezes.',
    'analogia': 'É a mesma matéria-prima entrando em três linhas de produção paralelas, em vez de passar '
      'três vezes pela mesma linha.'},
 ],
 'demos': [
   {'titulo': 'A média que o $avg calcula corretamente',
    'linguagem': 'javascript',
    'codigo': 'db.estudantes.aggregate([\n'
              '  { $match: { cidade: "São Paulo" } },\n'
              '  { $group: { _id: "$cidade", media_nota: { $avg: "$nota" } } }\n'
              ']);',
    'saida': '[ { _id: "São Paulo", media_nota: 6.5 } ]',
    'explicacao': '6,5 é a nota de Ricardo Mendes, o único estudante de São Paulo. Nos agrupamentos por '
      'curso, as médias não foram estragadas por Carlos, Ana e Lucas, que não têm o campo nota — o $avg '
      'simplesmente não os considerou.',
    'fonte': 'GABARITO.md, Parte 12, EX 12.2'},

   {'titulo': 'Classificação por faixas: a ordem decide o resultado',
    'linguagem': 'javascript',
    'codigo': 'db.estudantes.aggregate([\n'
              '  { $project: {\n'
              '    nome: 1, nota: 1,\n'
              '    conceito: { $switch: {\n'
              '      branches: [\n'
              '        { case: { $gte: ["$nota", 9] }, then: "A" },\n'
              '        { case: { $gte: ["$nota", 7] }, then: "B" }\n'
              '      ],\n'
              '      default: "C"\n'
              '    } }\n'
              '  } }\n'
              ']);',
    'explicacao': 'Invertendo as duas linhas do branches, a nota 9,7 passa a receber B, porque o teste '
      '$gte: 7 é verdadeiro e vence primeiro. Quem não tem nota cai no default e recebe C — o que pode '
      'ou não ser o desejado, e precisa ser decisão consciente.',
    'fonte': 'GABARITO.md, Parte 12, EX 12.3'},

   {'titulo': 'WHERE e HAVING no mesmo pipeline',
    'linguagem': 'javascript',
    'codigo': '// posição 1 — equivale ao WHERE: filtra documento cru, usa índice\n'
              '{ $match: { cidade: "Brasília" } },\n'
              '{ $group: { _id: "$curso", media_nota: { $avg: "$nota" } } }\n\n'
              '// posição 2 — equivale ao HAVING: só aqui media_nota existe\n'
              '{ $group: { _id: "$curso", media_nota: { $avg: "$nota" } } },\n'
              '{ $match: { media_nota: { $gt: 8 } } }',
    'explicacao': 'O segundo $match não poderia estar antes: media_nota é um campo criado pelo $group '
      'e não existe nos documentos originais. Já o primeiro poderia estar depois — funcionaria, mas '
      'agruparia documentos que seriam descartados em seguida, e sem poder usar índice.',
    'fonte': 'GABARITO.md, Parte 12, EX 12.5'},
 ],
 'fechamento': 'O pipeline é a ferramenta analítica do MongoDB, e quase toda decisão de desempenho nele '
   'se resume a uma pergunta: quanto dado consigo descartar antes do estágio caro? Essa pergunta leva '
   'diretamente ao próximo módulo, porque descartar cedo com eficiência depende de índice.',
 'perguntas': [
   'Por que o $match depois do $group não consegue usar índice?',
   'Você precisa da média de notas e da contagem de alunos por curso. Vale um $facet ou dois pipelines separados?',
   'Depois de um $lookup seguido de $unwind, seu relatório perdeu 12 registros. O que provavelmente aconteceu?',
 ],
})

# =====================================================================
MODULOS.append({
 'tema': 'mongo',
 'titulo': 'MongoDB: indexação e desempenho',
 'duracao_min': 35,
 'abertura': 'Índice é a única estrutura em que se paga escrita para ganhar leitura. Saber criar é fácil; '
             'a competência real está em saber quando não criar — e em medir o efeito em vez de supor.',
 'objetivos': [
   'Ler a saída do explain e distinguir COLLSCAN de IXSCAN com FETCH.',
   'Usar totalDocsExamined como métrica de qualidade do índice, em vez do tempo de execução.',
   'Aplicar a regra do prefixo à esquerda para decidir a ordem dos campos num índice composto.',
   'Enumerar os casos em que criar índice piora o sistema.',
 ],
 'conceitos': [
   {'nome': 'COLLSCAN, IXSCAN e FETCH',
    'explicacao': 'COLLSCAN significa collection scan: o servidor leu todos os documentos, um a um, '
      'comparando o campo. Com índice, aparecem dois estágios aninhados: o IXSCAN percorre a estrutura '
      'do índice e encontra as chaves que casam; o FETCH usa os endereços guardados nessas chaves para '
      'buscar os documentos completos no disco. São dois estágios porque o índice guarda apenas o campo '
      'indexado e o ponteiro — não o documento inteiro.',
    'analogia': 'COLLSCAN é folhear o livro página por página procurando uma palavra. IXSCAN é consultar '
      'o índice remissivo no fim; FETCH é ir até as páginas que o índice apontou.'},

   {'nome': 'Meça totalDocsExamined, não o tempo',
    'explicacao': 'Em coleção pequena, o tempo de execução com e sem índice é indistinguível — e às vezes '
      'o índice sai mais lento, porque consultá-lo e depois buscar os documentos custa mais do que varrer '
      'oito registros. O número que revela a qualidade do índice é totalDocsExamined: quantos documentos '
      'o servidor precisou abrir para responder. A meta é que ele fique próximo de nReturned. Uma razão '
      'de 1:1 é um índice perfeito para aquela consulta; 1000:1 é um índice que não está servindo.',
    'erro_comum': 'Benchmarkar índice numa base de teste com poucos documentos, concluir que "não fez '
      'diferença" e não criar o índice em produção, onde a coleção tem milhões de registros.'},

   {'nome': 'A regra do prefixo à esquerda',
    'explicacao': 'Um índice composto { cidade: 1, nota: -1 } atende consultas por cidade, e por cidade '
      'combinada com nota — inclusive entregando o resultado já ordenado por nota, sem ordenação em '
      'memória. Mas não atende consulta apenas por nota. O índice está ordenado primeiro por cidade; '
      'buscar só por nota exigiria varrer todos os blocos de cidade. Por isso a ordem dos campos num '
      'índice composto é decisão de projeto, não detalhe de escrita.',
    'analogia': 'Uma lista telefônica ordenada por sobrenome e depois por nome. Dá para achar todos os '
      'Silva, e dá para achar Silva, João. Não dá para achar todos os Joãos sem ler a lista inteira.'},

   {'nome': 'Índice único: a integridade é do servidor',
    'explicacao': 'Um índice com { unique: true } faz o servidor recusar a escrita de valor repetido, '
      'devolvendo o erro E11000 duplicate key error, e o documento não é gravado. A validação acontece '
      'no servidor, no momento da escrita — não é convenção da aplicação, é garantia. Dois detalhes '
      'operacionais: não se converte um índice existente em único, é preciso removê-lo e recriar; e se '
      'a coleção já contiver valores repetidos, é a criação do índice que falha.',
    'erro_comum': 'Confiar em validação apenas na camada de aplicação. Duas instâncias do serviço '
      'gravando ao mesmo tempo passam pela validação da aplicação e produzem duplicata; só o índice '
      'único no servidor impede isso.'},

   {'nome': 'Quando o índice piora o sistema',
    'explicacao': 'Coleção pequena: varrer sai mais barato que consultar o índice e buscar os documentos. '
      'Campo de baixa cardinalidade, como um booleano ativo: o índice aponta para metade da base, não '
      'elimina quase nada, e o planejador tende a ignorá-lo. Carga de escrita intensa: cada índice precisa '
      'ser atualizado em todo insert, update e delete — cinco índices são cinco estruturas a manter por '
      'gravação. Campo que nunca aparece em filtro, ordenação ou $lookup: ocupa disco e memória sem '
      'devolver nada. E o índice redundante: tendo { curso: 1, idade: -1 }, criar { curso: 1 } é '
      'desperdício, porque o composto já atende busca por curso sozinho.',
    'erro_comum': 'Criar um índice para cada campo "por precaução". O resultado é escrita lenta, uso de '
      'memória alto e um planejador com opções demais para avaliar.'},
 ],
 'demos': [
   {'titulo': 'O efeito do índice medido, não suposto',
    'linguagem': 'javascript',
    'codigo': '// antes de criar o índice\n'
              'db.estudantes.find({ cidade: "Brasília" }).explain("executionStats");\n\n'
              'db.estudantes.createIndex({ cidade: 1 });\n\n'
              '// depois\n'
              'db.estudantes.find({ cidade: "Brasília" }).explain("executionStats");',
    'saida': 'antes:  stage: COLLSCAN   totalDocsExamined: 8   totalKeysExamined: 0\n'
             'depois: stage: FETCH  ->  IXSCAN   totalKeysExamined: deixou de ser zero',
    'explicacao': 'O tempo praticamente não mudou, e com oito documentos isso é esperado. O que mudou '
      'foi totalDocsExamined, que caiu de oito para apenas os documentos que interessam. É esse número '
      'que se projeta para uma coleção de milhões.',
    'fonte': 'GABARITO.md, Parte 13, EX 13.2'},

   {'titulo': 'Um índice que serve filtro e ordenação de uma vez',
    'linguagem': 'javascript',
    'codigo': 'db.estudantes.createIndex({ cidade: 1, nota: -1 });\n\n'
              'db.estudantes.find({ cidade: "Brasília" }).sort({ nota: -1 });',
    'explicacao': 'Esse índice atende a consulta inteira: filtra por cidade e já devolve na ordem de '
      'nota decrescente, dispensando ordenação em memória. Note que a direção declarada no índice (-1) '
      'casa com a direção pedida no sort. O mesmo índice não serviria para uma busca apenas por nota.',
    'fonte': 'GABARITO.md, Parte 13, EX 13.3'},

   {'titulo': 'O servidor recusa a duplicata',
    'linguagem': 'javascript',
    'codigo': 'db.cursos.createIndex({ nome: 1 }, { unique: true });\n\n'
              'db.cursos.insertOne({ nome: "Data Science", duracao: "8 meses", modalidade: "EAD" });',
    'saida': 'MongoServerError: E11000 duplicate key error collection: dbNoSQLBD.cursos index: nome_1',
    'explicacao': 'O documento não foi gravado. Quem barrou foi o servidor, na escrita — uma garantia '
      'de integridade que nenhuma validação de aplicação consegue oferecer sob concorrência.',
    'fonte': 'GABARITO.md, Parte 13, EX 13.4'},
 ],
 'fechamento': 'O índice B-tree do MongoDB resolve com elegância igualdade, faixa e ordenação. O que ele '
   'não resolve é relevância em texto livre: ele sabe dizer se um campo é igual a "banco de dados", mas '
   'não sabe dizer quais documentos são os mais relevantes para essa expressão, nem encontrar "bancos de '
   'dados" no meio de um parágrafo. É exatamente esse limite que justifica a existência do Elasticsearch, '
   'e é onde a aula vira.',
 'perguntas': [
   'Sua consulta retorna 50 documentos e o explain mostra totalDocsExamined: 40000. O que isso diz sobre o índice?',
   'Você tem { curso: 1, idade: -1 }. Que consultas esse índice atende e que consultas ele não atende?',
   'Um sistema recebe 10 mil escritas por segundo e faz uma consulta analítica por dia. Vale indexar o campo dessa consulta?',
   'Por que não se pode converter um índice existente em índice único?',
 ],
})
