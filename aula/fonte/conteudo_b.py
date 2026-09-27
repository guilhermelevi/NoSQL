#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modulos 5 a 8 da aula (Elasticsearch e sintese)."""

MODULOS = []

# =====================================================================
MODULOS.append({
 'tema': 'elastic',
 'titulo': 'Elasticsearch: arquitetura e o índice invertido',
 'duracao_min': 45,
 'abertura': 'O MongoDB responde rápido a "qual documento tem cidade igual a Brasília". Nenhum índice '
             'B-tree responde bem a "quais documentos falam sobre bancos de dados, ordenados por relevância". '
             'Essa segunda pergunta exige inverter a estrutura de dados.',
 'objetivos': [
   'Explicar cluster, node, index, shard e replica, e diagnosticar um cluster em estado yellow.',
   'Descrever o índice invertido e contrastá-lo com o B-tree do MongoDB.',
   'Prever o resultado de um analyzer sobre um texto e explicar por que match e term diferem.',
   'Justificar a escolha entre must e filter em termos de score e cache.',
   'Ler um explain de BM25 e identificar as três forças que compõem o score.',
 ],
 'conceitos': [
   {'nome': 'Cluster, node, shard e replica',
    'explicacao': 'Um cluster é um conjunto de nós que se coordenam. Um índice é dividido em shards, '
      'que são índices Lucene completos e independentes — é o shard que permite distribuir um índice '
      'grande demais para uma máquina. Cada shard primário pode ter réplicas, que servem a dois '
      'propósitos ao mesmo tempo: tolerância a falha e capacidade de leitura, já que consultas podem ser '
      'atendidas pela réplica. A regra que explica o estado do cluster: o Elasticsearch nunca aloca uma '
      'réplica no mesmo nó do seu primário, porque isso não protegeria contra nada.',
    'erro_comum': 'Interpretar o estado yellow como defeito. Yellow significa que todos os shards '
      'primários estão ativos e alguma réplica não foi alocada — o cluster está plenamente funcional, '
      'apenas sem redundância. Red é que significa primário faltando, ou seja, dado inacessível.'},

   {'nome': 'O índice invertido',
    'explicacao': 'Um índice comum vai do documento para o conteúdo. O índice invertido faz o contrário: '
      'para cada termo do vocabulário, guarda a lista de documentos em que ele aparece — a posting list — '
      'junto com frequência e posição. Responder "quais documentos contêm banco" vira uma consulta direta '
      'ao termo, sem varrer documento algum. E como as listas estão ordenadas, uma busca por dois termos '
      'é a interseção de duas listas ordenadas, operação linear no tamanho delas. É essa estrutura, '
      'implementada pelo Lucene, que está por baixo de todo o Elasticsearch.',
    'analogia': 'O índice remissivo no fim de um livro técnico: não guarda o texto, guarda em que páginas '
      'cada termo aparece. Procurar "normalização" no remissivo é instantâneo; procurar folheando não é.'},

   {'nome': 'O analyzer decide o que vira termo',
    'explicacao': 'Antes de entrar no índice invertido, o texto passa pelo analyzer, que faz três coisas '
      'em sequência: filtros de caractere, tokenização (quebra em termos) e filtros de token (minúsculas, '
      'remoção de stopwords, stemming). O ponto crucial é que o mesmo analyzer é aplicado na indexação e '
      'na busca — é essa simetria que faz a consulta encontrar o documento. Quando os dois divergem, a '
      'busca falha silenciosamente.',
    'erro_comum': 'Supor que o analyzer standard remove acentos. Ele não remove: faz minúsculas e separa '
      'por limites de palavra, mas "joão" e "joao" permanecem termos distintos. Remover acento exige o '
      'filtro asciifolding num analyzer customizado.'},

   {'nome': 'match analisa, term não',
    'explicacao': 'O match passa o texto da consulta pelo mesmo analyzer do campo e busca os termos '
      'resultantes — é a busca full-text. O term procura o valor exatamente como foi escrito, sem análise '
      'alguma. Daí a regra prática: match sobre campo text, term sobre campo keyword. Usar term sobre um '
      'campo text quase sempre devolve vazio, porque o valor original ("São Paulo") nunca foi armazenado '
      'como termo — o que está no índice são os tokens ("são", "paulo").',
    'erro_comum': 'Escrever { "term": { "cidade": "São Paulo" } } sobre um campo text e receber zero '
      'resultados, concluindo que o dado não existe. O correto é cidade.keyword, ou trocar para match.'},

   {'nome': 'must pontua, filter apenas seleciona',
    'explicacao': 'Dentro de uma bool query, as cláusulas em must contribuem para o score de relevância; '
      'as cláusulas em filter apenas decidem se o documento entra ou não, sem influenciar a ordenação. '
      'A diferença é de custo: como filter não calcula score, o Elasticsearch pode reaproveitar o '
      'resultado em cache de bitset entre consultas. Critérios binários — faixa de data, categoria, '
      'status — pertencem a filter. Só o que expressa "quão bem este documento responde à pergunta" '
      'pertence a must.',
    'erro_comum': 'Colocar tudo em must por hábito. O sistema funciona, mas paga cálculo de score para '
      'condições que são simples sim-ou-não e perde o cache.'},

   {'nome': 'BM25: as três forças do score',
    'explicacao': 'O BM25 combina três fatores. A frequência do termo no documento (TF) aumenta o score, '
      'mas com saturação: a décima ocorrência acrescenta muito menos que a segunda. A frequência inversa '
      'nos documentos (IDF) premia termos raros — um termo presente em todos os documentos não '
      'discrimina nada e recebe peso baixo. E a normalização por tamanho penaliza documentos longos, '
      'porque conter o termo num texto de dez mil palavras é menos significativo do que contê-lo em vinte. '
      'A fórmula do IDF aparece literalmente no explain: log(1 + (N - n + 0.5) / (n + 0.5)).',
    'analogia': 'Numa biblioteca, encontrar "de" num livro não diz nada — está em todos. Encontrar '
      '"hidrodinâmica" diz muito. E encontrá-la num panfleto de duas páginas diz mais do que encontrá-la '
      'numa enciclopédia de mil.'},

   {'nome': 'Near real-time: o documento não aparece na hora',
    'explicacao': 'O Lucene grava em segmentos imutáveis. Um documento indexado fica num buffer em '
      'memória e só se torna pesquisável quando ocorre o refresh, que por padrão roda a cada segundo e '
      'cria um novo segmento. Por isso o Elasticsearch é near real-time e não real-time. Segmentos são '
      'imutáveis, o que traz uma consequência importante: atualizar um documento não altera nada — grava-se '
      'uma versão nova e marca-se a antiga como deletada. O espaço e as estatísticas da versão antiga só '
      'somem quando ocorre um merge de segmentos.',
    'erro_comum': 'Indexar um documento em teste automatizado e consultá-lo na linha seguinte, obtendo '
      'zero resultados. A correção é usar ?refresh=true na escrita — em teste. Em produção, forçar '
      'refresh a cada escrita destrói o desempenho, porque cria um segmento por operação.'},
 ],
 'demos': [
   {'titulo': 'Diagnosticar um cluster yellow',
    'linguagem': 'json',
    'codigo': 'GET _cat/shards/meu_indice-000001,transacoes-000001?v',
    'saida': 'index             shard prirep state      docs  store   node\n'
             'transacoes-000001 0     p      STARTED       2   18kb   96ef8f7b41d1\n'
             'transacoes-000001 0     r      UNASSIGNED\n'
             'meu_indice-000001 0     p      STARTED       2 17.7kb   96ef8f7b41d1\n'
             'meu_indice-000001 0     r      UNASSIGNED',
    'explicacao': 'Os primários (p) estão STARTED; as réplicas (r) estão UNASSIGNED e sem nó atribuído. '
      'Com um único nó não há onde alocá-las, porque o Elasticsearch se recusa a pôr a réplica junto do '
      'primário. O cluster funciona por completo — apenas não sobrevive à perda do nó.',
    'fonte': 'PARTE2-EVIDENCIAS.md, seção 12.1'},

   {'titulo': 'O que o analyzer realmente faz — e o que não faz',
    'linguagem': 'json',
    'codigo': 'POST _analyze\n'
              '{ "analyzer": "standard", "text": "JOÃO, da Silva; em BRASÍLIA!" }',
    'saida': 'tokens: [ "joão", "da", "silva", "em", "brasília" ]',
    'explicacao': 'A pontuação sumiu e tudo virou minúscula — mas os acentos permaneceram. O roteiro do '
      'laboratório afirma que isso explica "por que match joao encontra João". Foi testado no cluster: '
      'match "joao" retorna zero resultados, enquanto "joão" e "JOÃO" retornam um. O analyzer standard '
      'explica o lowercase, não a insensibilidade a acento.',
    'fonte': 'PARTE2-EVIDENCIAS.md, seção 12.3; teste de acentuação executado em 08/09/2026'},

   {'titulo': 'O IDF do BM25, com os números do laboratório',
    'linguagem': 'json',
    'codigo': 'GET meu_indice/_search\n'
              '{ "query": { "match": { "nome": "João" } }, "explain": true }',
    'saida': 'weight(nome:joão in 0) [PerFieldSimilarity]  = 0.4700036\n'
             '  boost = 2.2\n'
             '  idf, computed as log(1 + (N - n + 0.5) / (n + 0.5))  = 0.47000363\n'
             '      n, number of documents containing term = 2\n'
             '      N, total number of documents with field = 3\n'
             '  tf = 0.45454544',
    'explicacao': 'Repare no detalhe: o índice tinha apenas 2 documentos vivos, mas o BM25 reporta N = 3. '
      'A causa é a imutabilidade dos segmentos — a Parte 10 fez um update, que gravou versão nova e marcou '
      'a antiga como deletada, e as estatísticas contam o documento deletado até o merge. Isso foi '
      'confirmado em experimento controlado: um índice com 2 documentos, após um único update, passa a '
      'reportar N = 3 com docs.deleted = 1.',
    'fonte': 'PARTE2-EVIDENCIAS.md, seção 12.6; experimento de verificação em 09/09/2026'},
 ],
 'fechamento': 'O índice invertido é o que torna a busca por relevância viável, e o BM25 é o que a torna '
   'útil. Mas nada disso funciona se os campos não forem declarados com o tipo certo — e é aí que a '
   'modelagem no Elasticsearch se revela mais rígida do que a do MongoDB, não menos.',
 'perguntas': [
   'Se réplica serve para tolerância a falha, por que ela também aumenta a capacidade de leitura?',
   'Um campo tem o termo "banco" em todos os documentos do índice. Que score de IDF ele recebe, e o que isso significa na prática?',
   'Por que forçar refresh a cada escrita destrói o desempenho em produção?',
   'Como você faria uma busca que encontrasse "João" digitando "joao"?',
 ],
})

# =====================================================================
MODULOS.append({
 'tema': 'elastic',
 'titulo': 'Elasticsearch: mapping, ingestão e consulta',
 'duracao_min': 40,
 'abertura': 'No MongoDB, gravar primeiro e pensar no esquema depois costuma dar certo. No Elasticsearch, '
             'essa ordem custa caro: o mapping precisa existir antes do índice nascer, porque mudar o '
             'tipo de um campo exige reindexar tudo.',
 'objetivos': [
   'Escolher entre text e keyword com base na operação pretendida.',
   'Justificar a existência de index template no ciclo de vida de índices que rotacionam.',
   'Explicar o papel do alias e do is_write_index numa estratégia de rollover.',
   'Comparar a Bulk API com inserções individuais em termos de custo.',
   'Traduzir uma agregação do Elasticsearch para o $group do MongoDB e vice-versa.',
 ],
 'conceitos': [
   {'nome': 'text e keyword resolvem problemas opostos',
    'explicacao': 'Um campo text passa pelo analyzer, é quebrado em termos e serve para busca full-text — '
      'mas por isso mesmo não pode ser usado para ordenação, agregação exata ou filtro por valor integral. '
      'Um campo keyword é armazenado como um único termo, sem análise, e serve exatamente para o que o '
      'text não serve. Como quase todo campo textual precisa das duas coisas, o padrão é declarar o '
      'multi-field: o campo é text e ganha um sub-campo .keyword. É por isso que aparece cidade para '
      'buscar e cidade.keyword para agregar.',
    'erro_comum': 'Tentar ordenar ou agregar por um campo text e receber o erro "Fielddata is disabled '
      'on text fields by default". A mensagem sugere habilitar fielddata, o que é quase sempre a decisão '
      'errada: consome memória proporcional ao vocabulário. O certo é usar o sub-campo keyword.'},

   {'nome': 'ignore_above: o corte silencioso',
    'explicacao': 'O sub-campo keyword costuma vir com ignore_above: 256, o que significa que valores '
      'com mais de 256 caracteres simplesmente não são indexados naquele sub-campo. O documento é '
      'aceito e o campo text continua pesquisável, mas o valor some das agregações e dos filtros exatos. '
      'É um comportamento defensivo — evita termos gigantes no índice — que se manifesta como dado '
      'faltando em relatório.',
    'erro_comum': 'Agregar por um campo .keyword e notar que alguns registros não aparecem em bucket '
      'algum, sem nenhum erro que indique o motivo.'},

   {'nome': 'Index template: o mapping precede o índice',
    'explicacao': 'Índices que rotacionam por tempo — logs diários, por exemplo — nascem sozinhos quando '
      'o primeiro documento chega. Se não houvesse template, cada índice novo teria mapping inferido '
      'automaticamente, e bastaria um documento atípico para que um campo virasse texto num dia e número '
      'no outro. O template casa por padrão de nome e aplica settings, mappings e aliases a todo índice '
      'criado que corresponda ao padrão. Ele age na criação: alterar o template não muda índices que já '
      'existem.',
    'erro_comum': 'Corrigir o mapping no template e supor que os índices já criados foram corrigidos. '
      'Só valem para os próximos; os antigos precisam de reindex.'},

   {'nome': 'Alias e is_write_index',
    'explicacao': 'O alias é um nome estável que aponta para um ou mais índices físicos. A aplicação '
      'escreve e lê por meio dele e nunca precisa saber que por baixo existe transacoes-000001, depois '
      '000002, e assim por diante. Quando o alias aponta para vários índices, é preciso marcar um deles '
      'com is_write_index: true para dizer onde as escritas devem cair — leituras vão a todos, escritas '
      'a apenas um. É esse mecanismo que torna o rollover transparente.',
    'analogia': 'É o encaminhamento de correspondência. O remetente continua escrevendo para o mesmo '
      'endereço; quem se muda é o destinatário, e a correspondência antiga continua acessível.'},

   {'nome': 'Bulk API: o custo está na viagem, não na escrita',
    'explicacao': 'Vinte inserções individuais são vinte requisições HTTP, com vinte handshakes, vinte '
      'roteamentos de coordenação e vinte respostas. Um único _bulk com vinte operações é uma requisição '
      'só: o nó coordenador agrupa as operações por shard e as despacha em lote. O ganho não vem de '
      'escrever mais rápido, vem de eliminar o custo por viagem. O mesmo raciocínio vale para o '
      'insertMany do MongoDB.',
    'erro_comum': 'Assumir que status 200 no _bulk significa que tudo deu certo. O bulk devolve 200 mesmo '
      'com falhas parciais — é obrigatório inspecionar o campo errors e o status de cada item.'},

   {'nome': 'Agregações: o mesmo conceito, outra sintaxe',
    'explicacao': 'A agregação terms cria um bucket por valor distinto do campo e conta os documentos de '
      'cada um — é o $group com $sum: 1 do MongoDB. A avg calcula média — é o $group com $avg. O size: 0 '
      'no corpo da consulta pede que os documentos não sejam devolvidos, apenas os buckets, o que evita '
      'trafegar dados que ninguém vai ler. E, como no MongoDB, agregações operam sobre valores exatos: '
      'por isso o campo agregado precisa ser keyword.',
    'analogia': 'São dois idiomas descrevendo a mesma operação. Quem entende agrupamento em um, entende '
      'no outro assim que traduz o vocabulário.'},
 ],
 'demos': [
   {'titulo': 'O template que garante o tipo antes do índice existir',
    'linguagem': 'json',
    'codigo': 'PUT _template/transacoes_template\n'
              '{\n'
              '  "index_patterns": ["transacoes-*"],\n'
              '  "settings": {\n'
              '    "index.lifecycle.name": "politica_transacoes",\n'
              '    "index.lifecycle.rollover_alias": "transacoes"\n'
              '  },\n'
              '  "mappings": { "properties": {\n'
              '    "usuario": { "type": "text",\n'
              '      "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },\n'
              '    "valor":   { "type": "double" },\n'
              '    "tipo":    { "type": "keyword" },\n'
              '    "data":    { "type": "date",\n'
              '      "format": "strict_date_optional_time||epoch_millis" }\n'
              '  } }\n'
              '}',
    'saida': '{ "acknowledged": true }',
    'explicacao': 'Note as três decisões de modelagem: usuario é text com sub-campo keyword, porque '
      'precisa ser buscado e agregado; tipo é keyword puro, porque é categoria fechada e nunca será '
      'buscado por palavra solta; valor é double, o que habilita range e avg. Trocar tipo por text '
      'quebraria a agregação do próximo slide.',
    'fonte': 'PARTE1-EVIDENCIAS.md, Parte 6'},

   {'titulo': 'Alias com índice de escrita definido',
    'linguagem': 'json',
    'codigo': 'PUT transacoes-000001\n'
              '{ "aliases": { "transacoes": { "is_write_index": true } } }',
    'saida': '{ "acknowledged": true, "shards_acknowledged": true, "index": "transacoes-000001" }',
    'explicacao': 'A partir daqui a aplicação usa apenas o nome transacoes. Quando o rollover criar o '
      '000002 e transferir a marca de escrita, nenhuma linha de código da aplicação muda — e as consultas '
      'continuam alcançando os dois índices.',
    'fonte': 'PARTE1-EVIDENCIAS.md, Parte 7'},

   {'titulo': 'Agregação por categoria, com os números reais do lab',
    'linguagem': 'json',
    'codigo': 'GET transacoes/_search\n'
              '{ "size": 0,\n'
              '  "aggs": { "total_por_tipo": { "terms": { "field": "tipo" } } } }',
    'saida': '"buckets": [\n'
             '  { "key": "compra", "doc_count": 12 },\n'
             '  { "key": "venda",  "doc_count": 10 }\n'
             ']',
    'explicacao': 'Vinte e dois documentos, dois buckets. Isso só funciona porque tipo foi declarado '
      'keyword no template. Se fosse text, os valores teriam sido tokenizados e a agregação falharia. '
      'O equivalente em MongoDB seria { $group: { _id: "$tipo", total: { $sum: 1 } } }.',
    'fonte': 'PARTE2-EVIDENCIAS.md, seção 12.9'},

   {'titulo': 'Média sobre campo numérico',
    'linguagem': 'json',
    'codigo': 'GET transacoes/_search\n'
              '{ "size": 0, "aggs": { "valor_medio": { "avg": { "field": "valor" } } } }',
    'saida': '"hits": { "total": { "value": 22 } },\n'
             '"aggregations": { "valor_medio": { "value": 302.26590909090913 } }',
    'explicacao': 'A média de 22 transações. O size: 0 fez com que nenhum documento fosse devolvido — '
      'apenas o resultado agregado. Sem ele, o Elasticsearch mandaria os 10 primeiros documentos junto, '
      'de graça, para ninguém ler.',
    'fonte': 'PARTE2-EVIDENCIAS.md, seção 12.9'},
 ],
 'fechamento': 'Modelagem no Elasticsearch é uma decisão antecipada: text ou keyword, com ou sem '
   'sub-campo, template antes do índice. Feita a modelagem, a busca lexical está resolvida — mas ela '
   'só encontra o que foi escrito com as mesmas palavras. Buscar por significado exige outra estrutura.',
 'perguntas': [
   'Você precisa agregar por país e também buscar por nome de país digitado parcialmente. Como declara o campo?',
   'Um _bulk de mil documentos retornou 200. Por que isso não basta para concluir que tudo foi indexado?',
   'Se alterar o template não corrige índices existentes, como você corrigiria o mapping de um índice em produção?',
   'Por que agregação exige keyword, se o campo text contém a mesma informação?',
 ],
})

# =====================================================================
MODULOS.append({
 'tema': 'elastic',
 'titulo': 'Busca vetorial, busca híbrida e RAG',
 'duracao_min': 40,
 'abertura': 'O BM25 encontra documentos que usam as mesmas palavras da consulta. Quem pergunta "qual a '
             'capital do Brasil" e tem no acervo um texto que diz "Brasília é a sede do governo federal" '
             'não recebe nada — não há palavra em comum. Resolver isso exige representar significado, '
             'não grafia.',
 'objetivos': [
   'Explicar o que é um embedding e por que proximidade vetorial aproxima significado.',
   'Declarar um campo dense_vector e justificar a escolha do número de dimensões.',
   'Distinguir script_score de knn em termos de exatidão, custo e faixa de score.',
   'Descrever o pipeline de RAG e justificar por que se indexam chunks, não documentos.',
 ],
 'conceitos': [
   {'nome': 'Embedding: significado como coordenada',
    'explicacao': 'Um embedding é um vetor de números reais produzido por um modelo treinado, de modo que '
      'textos com sentido próximo recebam vetores próximos no espaço. O modelo não guarda as palavras: '
      'guarda uma posição num espaço de centenas de dimensões, onde a distância codifica relação '
      'semântica. É isso que permite recuperar "Brasília é a sede do governo" a partir de "capital do '
      'Brasil", sem nenhuma palavra em comum.',
    'analogia': 'Um mapa de cidades. Nada no nome "Campinas" indica que ela está perto de São Paulo — '
      'quem informa isso são as coordenadas. O embedding faz o mesmo com significado: transforma sentido '
      'em posição, e semelhança em proximidade.'},

   {'nome': 'dense_vector e a rigidez das dimensões',
    'explicacao': 'O campo dense_vector armazena o vetor e exige declarar dims, o número de dimensões. '
      'Esse número não é escolha livre: precisa coincidir exatamente com a saída do modelo usado. O '
      'all-MiniLM-L6-v2 produz 384 dimensões; outros modelos produzem 768, 1024 ou 1536. Documento com '
      'dimensão diferente da declarada é rejeitado, e trocar de modelo depois obriga a reindexar tudo, '
      'porque vetores de modelos diferentes não são comparáveis entre si — nem quando têm o mesmo número '
      'de dimensões.',
    'erro_comum': 'Comparar vetores gerados por modelos distintos. Os números têm o mesmo formato e a '
      'operação de cosseno funciona sem erro, mas o resultado não significa nada: são espaços diferentes.'},

   {'nome': 'Similaridade de cosseno',
    'explicacao': 'O cosseno entre dois vetores mede o ângulo entre eles, ignorando o comprimento: '
      'sim(A,B) = (A · B) / (||A|| × ||B||). O valor vai de 1, para vetores na mesma direção, passando '
      'por 0, para vetores ortogonais, até -1, para direções opostas. Ignorar o comprimento é desejável '
      'em texto, porque um documento longo e um curto sobre o mesmo assunto devem ser considerados '
      'próximos. Como o Elasticsearch exige score não negativo, o script_score soma 1,0 ao cosseno, '
      'deslocando a faixa para 0 a 2.',
    'analogia': 'Duas pessoas apontando para o mesmo ponto do horizonte. O cosseno mede se os braços '
      'apontam na mesma direção — não importa se um braço é mais comprido que o outro.'},

   {'nome': 'script_score é exato; knn é aproximado',
    'explicacao': 'O script_score avalia todos os documentos que passam pela query interna, calculando o '
      'cosseno sobre os vetores originais em ponto flutuante. É exato e custa O(n) — aceitável em '
      'milhares de documentos, inviável em milhões. A query knn do Elasticsearch 8 percorre um grafo '
      'HNSW, que encontra vizinhos prováveis em tempo sublinear, sem examinar todos os candidatos. '
      'Duas consequências: o resultado pode não ser o exato (por isso "aproximado"), e a faixa de score '
      'é outra — para cosseno, o knn usa (1 + cos) / 2, que vai de 0 a 1.',
    'erro_comum': 'Comparar diretamente o score de um script_score com o de um knn e concluir que um '
      '"achou melhor" que o outro. As escalas são diferentes por definição; comparar exige converter.'},

   {'nome': 'Quantização: o int8 que o 8.x aplica sozinho',
    'explicacao': 'No Elasticsearch 8.x, um dense_vector indexado ganha por padrão index_options do tipo '
      'int8_hnsw: os vetores são quantizados de 32 para 8 bits por dimensão, reduzindo memória em cerca '
      'de quatro vezes. O preço é um erro pequeno de precisão, que aparece como diferença na terceira ou '
      'quarta casa decimal do score. Em recuperação isso raramente altera o ranking, mas explica por que '
      'a conta do knn não fecha exatamente com a fórmula teórica.',
    'analogia': 'É arredondar todo preço para a dezena mais próxima antes de somar. O total continua '
      'servindo para decidir, mas não bate no centavo com a soma exata.'},

   {'nome': 'Busca híbrida',
    'explicacao': 'Lexical e vetorial erram de formas diferentes. O BM25 falha com sinônimos e paráfrases; '
      'a busca vetorial falha com termos exatos, códigos de produto, nomes próprios e números — coisas '
      'que o embedding tende a diluir. Combinar as duas cobre os dois pontos cegos. No laboratório a '
      'combinação foi feita com script_score, em que o match filtra e o cosseno reordena. Em produção, '
      'a técnica atual é RRF (Reciprocal Rank Fusion), que funde os dois rankings sem precisar normalizar '
      'escalas incompatíveis.',
    'erro_comum': 'Somar diretamente score de BM25 com score de cosseno. O BM25 não tem limite superior '
      'e varia com o corpus; o cosseno é limitado. A soma é dominada arbitrariamente por um dos dois.'},

   {'nome': 'RAG e a razão do chunking',
    'explicacao': 'Num pipeline de RAG, documentos são divididos em trechos, cada trecho vira um embedding, '
      'tudo é indexado, e a pergunta do usuário — também convertida em vetor — recupera os k trechos mais '
      'próximos, que entram no prompt do modelo de linguagem. Indexa-se trecho e não documento inteiro '
      'por duas razões: um vetor único para um documento longo é a média de assuntos demais e não se '
      'aproxima de nenhum, e o contexto entregue ao modelo precisa caber na janela. O tamanho do chunk é '
      'um compromisso — pequeno demais perde contexto, grande demais dilui o significado.',
    'erro_comum': 'Tratar o RAG como solução completa e ignorar a qualidade da recuperação. Se os '
      'trechos recuperados forem ruins, o modelo responde com confiança sobre a base errada.'},
 ],
 'demos': [
   {'titulo': 'O que o Elasticsearch 8 acrescenta ao mapping sem pedir',
    'linguagem': 'json',
    'codigo': 'PUT documentos_vetoriais\n'
              '{ "mappings": { "properties": {\n'
              '    "texto":     { "type": "text" },\n'
              '    "embedding": { "type": "dense_vector", "dims": 384 }\n'
              '} } }\n\n'
              'GET documentos_vetoriais/_mapping',
    'saida': '"embedding": {\n'
             '  "type": "dense_vector", "dims": 384,\n'
             '  "index": true,\n'
             '  "similarity": "cosine",\n'
             '  "index_options": { "type": "int8_hnsw", "m": 16, "ef_construction": 100 }\n'
             '}',
    'explicacao': 'Foram declarados dois atributos e voltaram cinco. O roteiro do laboratório, escrito '
      'para o Elasticsearch 7.x, afirma que index e similarity "não devem ser usados" — no 8.15 eles são '
      'aplicados automaticamente. Isso muda a prática: o campo já nasce indexado em HNSW e aceita a query '
      'knn, que no 7.x não existia.',
    'fonte': 'PARTE2-EVIDENCIAS.md, seção 13.2'},

   {'titulo': 'Os dois caminhos, medidos lado a lado',
    'linguagem': 'json',
    'codigo': '// caminho A — exato, forca bruta\n'
              'POST indice_conhecimento/_search\n'
              '{ "query": { "script_score": {\n'
              '    "query": { "match_all": {} },\n'
              '    "script": { "source": "cosineSimilarity(params.query_vector, \'embedding\') + 1.0",\n'
              '                "params": { "query_vector": [0.11, -0.40, 0.80, ...] } } } },\n'
              '  "size": 3 }\n\n'
              '// caminho B — aproximado, grafo HNSW\n'
              'POST indice_conhecimento/_search\n'
              '{ "knn": { "field": "embedding", "query_vector": [0.11, -0.40, 0.80, ...],\n'
              '           "k": 3, "num_candidates": 100 } }',
    'saida': 'titulo                  script_score      knn    cosseno exato   (1+cos)/2\n'
             'Curitiba                     1.99895  0.99936        0.998947    0.999473\n'
             'Cerrado brasileiro           1.99894  0.99935        0.998938    0.999469\n'
             'Capital do Brasil            1.99875  0.99924        0.998748    0.999374',
    'explicacao': 'Mesmo ranking pelos dois caminhos. O script_score bate exatamente com o cosseno '
      'calculado à mão (1,99895 = 0,998947 + 1). O knn fica levemente abaixo de (1+cos)/2 — a diferença '
      'é o erro da quantização int8. Ou seja: as duas colunas não divergem por bug, divergem porque uma '
      'é exata e a outra é aproximada e comprimida.',
    'fonte': 'PARTE2-EVIDENCIAS.md, seções 14.4 e EXTRA; verificação numérica em 09/09/2026'},
 ],
 'fechamento': 'Uma ressalva honesta sobre o laboratório: os vetores de 10 dimensões foram escritos à '
   'mão, não gerados por modelo. A mecânica do cosseno, do HNSW e da faixa de score é real e foi medida; '
   'a semântica, não — documentos "próximos" ali estavam próximos porque os números foram escolhidos '
   'assim. Com um modelo real de 384 dimensões, a mesma mecânica passa a carregar significado de verdade.',
 'perguntas': [
   'Por que o cosseno ignora o comprimento do vetor, e por que isso é desejável em texto?',
   'Sua busca vetorial não encontra o produto "XPS-13-9370" que o usuário digitou. Por quê, e o que você faria?',
   'Em que situação o knn devolveria um ranking diferente do script_score sobre os mesmos dados?',
   'Se o chunk pequeno perde contexto e o grande dilui significado, como você decidiria o tamanho?',
 ],
})

# =====================================================================
MODULOS.append({
 'tema': 'sintese',
 'titulo': 'Os dois juntos: sistema de registro e camada de busca',
 'duracao_min': 30,
 'abertura': 'Os dois laboratórios pareciam exercícios separados. Não eram: juntos, eles montaram uma '
             'arquitetura que aparece em quase todo sistema de porte — e que responde à pergunta de '
             'quando usar cada banco com um "os dois, em papéis diferentes".',
 'objetivos': [
   'Descrever o fluxo MongoDB → GELF → Logstash → Elasticsearch → Kibana e o papel de cada peça.',
   'Explicar por que o acoplamento entre os dois sistemas é unidirecional e o que isso garante.',
   'Avaliar a escolha de UDP para transporte de log, com suas vantagens e o que ela sacrifica.',
   'Aplicar o critério de decisão entre os dois sistemas a requisitos concretos.',
 ],
 'conceitos': [
   {'nome': 'O fluxo, peça por peça',
    'explicacao': 'O MongoDB escreve log na saída padrão, como qualquer processo. O driver de log GELF '
      'do Docker intercepta essa saída e a envia por UDP para a porta 12201. O Logstash escuta ali, '
      'aplica o pipeline configurado e escreve no Elasticsearch, num índice nomeado por data. O Kibana '
      'lê o Elasticsearch e apresenta. Nenhuma dessas peças conhece as outras além da vizinha imediata: '
      'trocar o Elasticsearch por outro destino exigiria mudar apenas o output do Logstash.',
    'analogia': 'Uma esteira de triagem postal. Cada posto sabe de onde recebe e para onde entrega, e '
      'nenhum precisa conhecer o percurso inteiro.'},

   {'nome': 'Acoplamento de um lado só',
    'explicacao': 'O MongoDB não sabe que o Elasticsearch existe. Ele apenas emite log, e emitiria da '
      'mesma forma se ninguém estivesse escutando. Essa direção única é o que torna a arquitetura '
      'resiliente: derrubar toda a camada de busca não afeta a capacidade do banco de aceitar escritas. '
      'A recíproca não vale — sem a fonte, o índice derivado deixa de ser alimentado.',
    'erro_comum': 'Inverter a dependência, fazendo a aplicação escrever primeiro no Elasticsearch e '
      'depois no banco principal. Qualquer indisponibilidade da busca passa a derrubar a escrita.'},

   {'nome': 'UDP: a escolha que troca garantia por isolamento',
    'explicacao': 'GELF sobre UDP não estabelece conexão nem confirma entrega. A consequência boa é que '
      'o contêiner sobe e opera mesmo com o Logstash fora do ar — os pacotes são simplesmente descartados '
      'e nada bloqueia. A consequência ruim é que não há garantia: sob perda de rede ou sobrecarga, '
      'linhas de log somem sem aviso. Para telemetria é um compromisso razoável; para auditoria, não. '
      'Auditoria exige transporte confiável e confirmação de entrega.',
    'erro_comum': 'Usar o mesmo pipeline de log best-effort para trilha de auditoria com valor legal. '
      'O dia em que faltar a linha crítica, não haverá como saber se ela nunca existiu ou se foi perdida.'},

   {'nome': 'O índice de busca nunca é a fonte da verdade',
    'explicacao': 'Este é o princípio que organiza tudo. O Elasticsearch é um índice derivado: se for '
      'perdido, reconstrói-se reindexando a partir da fonte. Se a fonte for perdida, o índice vira uma '
      'coleção de afirmações sobre dados que não existem mais. Isso tem consequência prática de projeto: '
      'todo pipeline de indexação precisa ser reexecutável do zero, e a decisão de "gravar só no '
      'Elasticsearch porque é mais rápido" deve ser recusada por padrão.',
    'analogia': 'O acervo e o catálogo da biblioteca. Perder o catálogo é trabalhoso; perder o acervo é '
      'irreversível.'},

   {'nome': 'O critério de escolha, sem falso dilema',
    'explicacao': 'A pergunta útil não é "qual banco é melhor", é "que pergunta este dado precisa '
      'responder, e com que garantia". Estado atual de um registro, com escrita confirmada e possibilidade '
      'de transação: MongoDB. Relevância em texto livre, agregação exploratória sobre volume, busca '
      'semântica: Elasticsearch. Quando um sistema precisa das duas coisas — e a maioria precisa — a '
      'resposta é os dois, com fluxo de sincronização explícito e a verdade morando em um só lugar.',
    'erro_comum': 'Escolher um único sistema para tudo e depois forçá-lo no papel para o qual não foi '
      'feito: implementar busca por relevância com regex no MongoDB, ou tratar o Elasticsearch como '
      'banco transacional.'},
 ],
 'demos': [
   {'titulo': 'O pipeline em treze linhas',
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
      'formato que justifica o index template do Módulo 6: índices que nascem sozinhos precisam de mapping '
      'declarado antes.',
    'fonte': 'lab02-elastic/logstash/pipeline/logstash.conf; estado do cluster em 09/09/2026'},

   {'titulo': 'A prova de que o acoplamento é de um lado só',
    'linguagem': 'bash',
    'codigo': '# durante a reorganizacao do repositorio, toda a camada de busca foi derrubada:\n'
              '$ cd lab02-elastic && docker compose down\n'
              '$ cd ../lab01-mongodb && docker compose up -d   # MongoDB sobe normalmente\n\n'
              '# e ao religar, o fluxo recomeca sozinho:\n'
              '$ curl -s "localhost:9200/_cat/indices/mongodb-logs-*?v"',
    'saida': 'yellow open mongodb-logs-2026.09.09   86 docs',
    'explicacao': 'O MongoDB subiu com o Logstash fora do ar, sem erro e sem espera — porque GELF é UDP '
      'e não bloqueia. Os logs daquele intervalo foram perdidos, o que é aceitável para telemetria. '
      'Ao religar a camada de busca, a indexação recomeçou sem nenhuma intervenção.',
    'fonte': 'Reorganização do repositório, 08/09/2026'},

   {'titulo': 'A mesma pergunta nos dois sistemas',
    'linguagem': 'javascript',
    'codigo': '// MongoDB — quantos documentos por categoria\n'
              'db.transacoes.aggregate([\n'
              '  { $group: { _id: "$tipo", total: { $sum: 1 } } }\n'
              ']);\n\n'
              '// Elasticsearch — a mesma pergunta\n'
              'GET transacoes/_search\n'
              '{ "size": 0, "aggs": { "por_tipo": { "terms": { "field": "tipo" } } } }',
    'saida': 'MongoDB:       [ { _id: "compra", total: 12 }, { _id: "venda", total: 10 } ]\n'
             'Elasticsearch: [ { key: "compra", doc_count: 12 }, { key: "venda", doc_count: 10 } ]',
    'explicacao': 'Mesma resposta, vocabulário diferente. A distinção entre os dois sistemas não está em '
      'agregar — os dois agregam bem. Está no que cada um faz com texto: só o Elasticsearch ordena por '
      'relevância, e só o MongoDB garante a escrita que originou o dado.',
    'fonte': 'GABARITO.md Parte 12 e PARTE2-EVIDENCIAS.md seção 12.9'},
 ],
 'fechamento': 'A competência que esta aula pretende deixar não é sintaxe de nenhum dos dois — isso está '
   'na documentação. É saber formular a pergunta certa diante de um requisito: que garantia este dado '
   'exige, que pergunta ele precisa responder, e onde mora a verdade. Respondido isso, a escolha da '
   'ferramenta é quase automática.',
 'perguntas': [
   'Se o Elasticsearch é descartável e reconstruível, por que fazer backup dele?',
   'Sua aplicação precisa que uma alteração no MongoDB apareça na busca em menos de um segundo. O pipeline de log serve? O que você usaria?',
   'Que perguntas você faria a um time que propõe migrar do PostgreSQL para o MongoDB?',
   'Onde mora a fonte da verdade no sistema em que você trabalha ou estuda, e como você sabe disso?',
 ],
})
