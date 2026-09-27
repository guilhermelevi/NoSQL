#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Anexos: armadilhas reais, exercicios e avaliacao."""

ARMADILHAS = [
 {'titulo': 'A imagem mongo:4.4 do roteiro não sobe em kernel moderno',
  'sistema': 'MongoDB',
  'sintoma': 'O contêiner entra em laço de reinício. O log repete sempre a mesma linha e o serviço nunca '
             'fica disponível.',
  'causa_raiz': 'Bug SERVER-121912: versões antigas do MongoDB têm incompatibilidade conhecida com kernels '
                'Linux 6.19 ou superiores. O OrbStack roda kernel 7.0.14, verificado com '
                'docker run --rm alpine uname -r. O roteiro pressupõe a VM Ubuntu, cujo kernel é mais antigo.',
  'diagnostico': 'Ler o log do contêiner em vez de olhar apenas o status. O laço de reinício não diz a '
                 'causa; a mensagem no log diz.',
  'correcao': 'Trocar para mongo:8.2, que já contém a correção. Efeito colateral bem-vindo: essa imagem '
              'traz o mongosh embutido, o que torna a Parte 2 do roteiro (instalação via apt) desnecessária.',
  'licao': 'A versão fixada num roteiro carrega premissas sobre o ambiente que o roteiro não declara. '
           'Quando a versão indicada não sobe, o primeiro passo é ler o log, não trocar de ferramenta.',
  'evidencia': 'MongoDB cannot start: Linux kernel versions 6.19 and newer has a known incompatibility '
               'with this version of MongoDB.'},

 {'titulo': 'Elasticsearch 8.x exige HTTPS e token por padrão',
  'sistema': 'Elasticsearch',
  'sintoma': 'Seguindo o roteiro, o Kibana não conecta e as chamadas em http://localhost:9200 são recusadas.',
  'causa_raiz': 'A partir do 8.0, a segurança vem ligada por padrão: TLS obrigatório, senha gerada na '
                'primeira subida e token de inscrição para o Kibana. O roteiro foi escrito para o 7.x, '
                'onde tudo isso era opcional.',
  'diagnostico': 'Ler o log do contêiner do Elasticsearch na primeira subida — é ali que a senha gerada e '
                 'o token de inscrição aparecem, uma única vez.',
  'correcao': 'Para o laboratório, definir xpack.security.enabled=false no compose. Isso desliga '
              'autenticação, autorização por roles, TLS entre nós e no cliente, e a auditoria.',
  'licao': 'Desligar segurança para estudar é legítimo e deve ser uma decisão consciente e registrada. '
           'O risco real não é o ambiente de laboratório: é essa configuração viajar para produção dentro '
           'de um compose copiado.',
  'evidencia': 'lab02-elastic/docker-compose.yml — environment: xpack.security.enabled=false'},

 {'titulo': 'O roteiro afirma que o analyzer standard remove acentos. Não remove.',
  'sistema': 'Elasticsearch',
  'sintoma': 'A seção 12.3 do roteiro diz que o analyzer explica "por que match joao encontra João". '
             'Quem confia na afirmação e implementa busca contando com isso descobre em produção que não funciona.',
  'causa_raiz': 'O analyzer standard aplica lowercase e separa por limites de palavra, mas não faz '
                'transliteração. Os tokens gerados preservam o acento, e "joao" e "joão" permanecem termos '
                'distintos no índice invertido.',
  'diagnostico': 'Rodar POST _analyze com o texto e inspecionar os tokens, em vez de supor o comportamento. '
                 'Depois confirmar com uma busca real, comparando as duas grafias.',
  'correcao': 'Declarar um analyzer customizado com o filtro asciifolding na cadeia, e aplicá-lo tanto na '
              'indexação quanto na busca. O padrão comum é manter o campo original e acrescentar um '
              'sub-campo folded para busca insensível a acento.',
  'licao': 'Material didático também erra. O custo de verificar uma afirmação sobre o motor é um comando; '
           'o custo de não verificar é uma busca que falha silenciosamente para uma parte dos usuários.',
  'evidencia': 'match "João" -> 1 hit    |    match "joao" -> 0 hits\n'
               'match "joão" -> 1 hit    |    match "JOÃO" -> 1 hit\n'
               'tokens de "JOÃO, da Silva; em BRASÍLIA!": [joão, da, silva, em, brasília]'},

 {'titulo': 'Um índice com política ILM inexistente é criado sem erro — e falha depois, em silêncio',
  'sistema': 'Elasticsearch',
  'sintoma': 'O template referencia as políticas minha_politica e politica_transacoes, que nunca foram '
             'criadas. O template é aceito, o índice é criado, tudo parece correto. Meses depois, os índices '
             'não rotacionam nem expiram, e ninguém sabe por quê.',
  'causa_raiz': 'A validação de index.lifecycle.name não acontece na criação. O setting é apenas gravado. '
                'Quem resolve o nome da política é o serviço de ILM, que roda periodicamente em segundo '
                'plano — e é lá, de forma assíncrona, que o erro aparece.',
  'diagnostico': 'GET <indice>/_ilm/explain. Foi o que revelou o problema num teste controlado: o índice '
                 'aparece como managed: true, mas com step: ERROR e a razão explícita.',
  'correcao': 'Criar a política antes do template, ou remover as duas linhas de lifecycle do template se '
              'não houver política. E monitorar índices em estado de erro de ILM, porque eles não avisam.',
  'licao': 'Aceitação da configuração não é validação da configuração. Em sistemas com componentes '
           'assíncronos, "acknowledged: true" significa apenas que a instrução foi registrada — não que '
           'ela vá funcionar.',
  'evidencia': 'PUT teste_ilm-000001  ->  { "acknowledged": true, "shards_acknowledged": true }\n'
               'GET teste_ilm-000001/_ilm/explain  ->  step: ERROR\n'
               '   step_info: { "type": "illegal_argument_exception",\n'
               '                "reason": "policy [politica_fantasma] does not exist" }'},

 {'titulo': 'PUT _template é a API legada do 7.x',
  'sistema': 'Elasticsearch',
  'sintoma': 'Todos os PUT _template do roteiro funcionam, mas cada um devolve um aviso amarelo de '
             'depreciação no Dev Tools.',
  'causa_raiz': 'A API de templates foi reescrita no 7.8 e a antiga entrou em depreciação. A nova é '
                'PUT _index_template, com settings, mappings e aliases aninhados dentro de um objeto template, '
                'e com suporte a composable templates — blocos reutilizáveis combinados por prioridade.',
  'diagnostico': 'Ler os avisos de depreciação em vez de ignorá-los. Eles são a única antecipação que se '
                 'tem de uma quebra em versão futura.',
  'correcao': 'Migrar para PUT _index_template. A estrutura muda: o que estava na raiz passa a ficar dentro '
              'de "template": { "settings": {...}, "mappings": {...} }.',
  'licao': 'Aviso de depreciação é dívida com prazo. Funciona hoje, quebra numa atualização maior — e '
           'quase sempre no pior momento.',
  'evidencia': 'PUT _template/meu_template  ->  200 OK + warning de depreciação'},

 {'titulo': 'O BM25 conta documentos que já foram deletados',
  'sistema': 'Elasticsearch',
  'sintoma': 'O explain de uma consulta num índice com 2 documentos reporta N = 3, "total number of '
             'documents with field". O número não bate com a contagem do índice.',
  'causa_raiz': 'Segmentos do Lucene são imutáveis. Um update não altera o documento: grava uma versão nova '
                'e marca a anterior como deletada. As estatísticas de frequência usadas pelo BM25 são lidas '
                'do segmento e incluem os documentos marcados, até que ocorra um merge.',
  'diagnostico': 'Comparar docs.count com docs.deleted em _cat/indices e cruzar com o N do explain. '
                 'No experimento controlado: 2 documentos, 1 update, docs.deleted = 1, e N passou de 2 para 3.',
  'correcao': 'Nenhuma correção é necessária — é o comportamento projetado. O efeito no ranking é '
              'desprezível em índices grandes e some no merge. O que se corrige é a expectativa de quem lê '
              'o explain.',
  'licao': 'Score de relevância depende de estatísticas do corpus, e essas estatísticas são de segmento, '
           'não de uma contagem lógica. É por isso que o mesmo documento pode receber scores levemente '
           'diferentes em shards diferentes.',
  'evidencia': '2 docs vivos, 0 deletados  ->  n=2, N=2\n'
               'apos 1 update              ->  n=3, N=3  (docs.count=2, docs.deleted=1)'},

 {'titulo': 'A Parte 7 do roteiro atualiza uma coleção que ainda não existe',
  'sistema': 'MongoDB',
  'sintoma': 'Os comandos da Parte 7 rodam sem erro e reportam zero documentos modificados. Nada acontece, '
             'e nada avisa.',
  'causa_raiz': 'O roteiro usa db.estudantes na Parte 7, mas a coleção só passa a se chamar assim depois '
                'do renameCollection da Parte 10. Como o MongoDB cria coleção de forma preguiçosa, o update '
                'contra um nome inexistente cria uma coleção vazia e atualiza nada.',
  'diagnostico': 'Ler matchedCount e modifiedCount no retorno. Ambos em zero, sem erro, significa que o '
                 'filtro não casou — ou que a coleção está vazia por não ser a que se pensava.',
  'correcao': 'Rodar a Parte 7 contra db.alunos, que é o nome da coleção naquele momento do roteiro.',
  'licao': 'Ausência de erro não é evidência de sucesso. Em sistemas que criam recursos sob demanda, '
           'errar o nome produz silêncio, não exceção — e silêncio é mais difícil de depurar que falha.',
  'evidencia': 'db.estudantes.updateOne(...) -> { matchedCount: 0, modifiedCount: 0 }'},

 {'titulo': 'Os comentários do roteiro quebram no mongosh',
  'sistema': 'MongoDB',
  'sintoma': 'Colar um bloco do enunciado no playground do VS Code produz SyntaxError, mesmo com os '
             'comandos corretos.',
  'causa_raiz': 'O roteiro comenta com #, que é sintaxe de shell. O mongosh e o playground executam '
                'JavaScript, onde o comentário é //. E os atalhos do shell (use, show dbs, exit) também não '
                'existem no playground: lá é use("dbNoSQLBD") e db.getCollectionNames().',
  'diagnostico': 'A mensagem de SyntaxError aponta a linha do comentário, não o comando — o que despista.',
  'correcao': 'Trocar # por // e usar a forma de função dos comandos de shell no playground.',
  'licao': 'O mongosh parece um shell mas é um interpretador JavaScript. Saber qual linguagem está sendo '
           'interpretada evita uma classe inteira de erros que parecem inexplicáveis.',
  'evidencia': 'show dbs  ->  SyntaxError no playground   |   db.getMongo().getDBNames()  ->  funciona'},
]

EXERCICIOS = [
 {'numero': 1, 'titulo': 'Modelar sem repetir o modelo relacional', 'sistema': 'mongodb',
  'dificuldade': 'basico', 'tempo_min': 15,
  'enunciado': 'Você precisa guardar pedidos de uma loja. Cada pedido tem cliente, data, endereço de '
    'entrega e uma lista de itens, cada item com produto, quantidade e preço unitário. Um colega propôs '
    'três coleções — pedidos, itens e enderecos — ligadas por identificadores, como seria em SQL. '
    'Proponha a modelagem em documento e defenda a decisão de aninhar ou referenciar cada parte.',
  'esperado': 'Um documento de exemplo e a justificativa de cada escolha, considerando como o dado é lido '
    'e como ele muda ao longo do tempo.',
  'solucao_codigo': 'db.pedidos.insertOne({\n'
    '  cliente_id: ObjectId("..."),          // REFERENCIA: cliente vive alem do pedido\n'
    '  data: new Date("2026-09-09T10:00:00Z"),\n'
    '  endereco_entrega: {                   // ANINHADO: e uma copia historica\n'
    '    logradouro: "SQN 210 Bloco B",\n'
    '    cidade: "Brasília", uf: "DF", cep: "70862-020"\n'
    '  },\n'
    '  itens: [                              // ANINHADO: nao existe fora do pedido\n'
    '    { produto: "Teclado", quantidade: 1, preco_unitario: 250.00 },\n'
    '    { produto: "Monitor", quantidade: 2, preco_unitario: 899.90 }\n'
    '  ],\n'
    '  total: 2049.80\n'
    '});',
  'solucao_comentario': 'A regra é perguntar o que é lido junto e o que muda junto. Os itens não existem '
    'fora do pedido e são sempre lidos com ele: aninhar evita junção e garante atomicidade, já que a '
    'escrita de um documento é atômica. O endereço é aninhado por outro motivo — ele precisa ser uma '
    'cópia congelada. Se fosse referência ao cadastro do cliente, mudar o endereço hoje reescreveria o '
    'histórico de entregas de dois anos atrás. Já o cliente é referenciado porque tem vida própria, é '
    'compartilhado por muitos pedidos e é atualizado independentemente. O total é redundante e calculável, '
    'mas evita recomputar em toda listagem — desnormalização deliberada.',
  'criterio_correcao': 'A resposta precisa justificar cada decisão pelo padrão de leitura e pelo ciclo de '
    'vida do dado. Aninhar tudo ou referenciar tudo, sem argumento, não atende. Identificar que o endereço '
    'é cópia histórica é o ponto de maior valor.'},

 {'numero': 2, 'titulo': 'Um pipeline que responde a uma pergunta de negócio', 'sistema': 'mongodb',
  'dificuldade': 'intermediario', 'tempo_min': 20,
  'enunciado': 'Usando a coleção de pedidos do exercício anterior, produza um relatório dos três produtos '
    'que mais geraram receita em 2026, com receita total e quantidade vendida, considerando apenas pedidos '
    'da cidade de Brasília.',
  'esperado': 'Um pipeline de agregação com os estágios na ordem correta e a justificativa da posição do $match.',
  'solucao_codigo': 'db.pedidos.aggregate([\n'
    '  { $match: {                                    // 1. WHERE: cedo, corta volume e usa indice\n'
    '      "endereco_entrega.cidade": "Brasília",\n'
    '      data: { $gte: new Date("2026-01-01"), $lt: new Date("2027-01-01") }\n'
    '  } },\n'
    '  { $unwind: "$itens" },                         // 2. um documento por item\n'
    '  { $group: {                                    // 3. agrupa pelo produto\n'
    '      _id: "$itens.produto",\n'
    '      receita: { $sum: { $multiply: ["$itens.quantidade", "$itens.preco_unitario"] } },\n'
    '      unidades: { $sum: "$itens.quantidade" }\n'
    '  } },\n'
    '  { $sort: { receita: -1 } },\n'
    '  { $limit: 3 }\n'
    ']);',
  'solucao_comentario': 'O $match vem primeiro por dois motivos: reduz o volume que entra no $unwind, que '
    'multiplica documentos, e é a única posição em que consegue usar índice. Um índice '
    '{ "endereco_entrega.cidade": 1, data: 1 } atenderia esse filtro. O $unwind é necessário porque itens '
    'é array e o $group precisa de um documento por item. Note que a receita é calculada dentro do $sum '
    'com $multiply — não existe campo receita no documento, ele é derivado no próprio estágio.',
  'criterio_correcao': 'O $match precisa estar antes do $unwind. Colocá-lo depois produz o mesmo resultado '
    'com custo maior e sem índice — vale correção parcial, com a justificativa cobrada.'},

 {'numero': 3, 'titulo': 'Diagnosticar um índice que não está servindo', 'sistema': 'mongodb',
  'dificuldade': 'intermediario', 'tempo_min': 15,
  'enunciado': 'Uma consulta db.pedidos.find({ status: "entregue" }).sort({ data: -1 }).limit(20) está '
    'lenta. Existe o índice { status: 1 }. O explain mostra IXSCAN, mas também um estágio SORT e '
    'totalDocsExamined muito acima de 20. Explique o que está acontecendo e proponha a correção.',
  'esperado': 'O diagnóstico do estágio SORT em memória e um índice composto que o elimine.',
  'solucao_codigo': '// diagnostico\n'
    'db.pedidos.find({ status: "entregue" }).sort({ data: -1 }).limit(20)\n'
    '  .explain("executionStats");\n'
    '// stage: SORT  <- ordenacao em memoria, apos buscar todos os "entregue"\n\n'
    '// correcao\n'
    'db.pedidos.createIndex({ status: 1, data: -1 });\n\n'
    '// depois: o SORT desaparece, totalDocsExamined cai para ~20',
  'solucao_comentario': 'O índice { status: 1 } serve ao filtro, mas não à ordenação. O servidor busca '
    'todos os pedidos entregues — que podem ser milhões — e só então ordena por data em memória, para '
    'no fim descartar tudo menos vinte. O índice composto { status: 1, data: -1 } resolve os dois de uma '
    'vez: percorre apenas a faixa de status entregue, já na ordem de data decrescente, e para assim que '
    'junta vinte documentos. Se o SORT exceder o limite de memória, o MongoDB aborta a consulta — outro '
    'sintoma do mesmo problema.',
  'criterio_correcao': 'Identificar que o estágio SORT é o custo real, e que a ordem e a direção dos '
    'campos no índice composto importam. Propor apenas { data: -1 } separado não resolve.'},

 {'numero': 4, 'titulo': 'Escolher entre text e keyword', 'sistema': 'elasticsearch',
  'dificuldade': 'basico', 'tempo_min': 15,
  'enunciado': 'Um índice de artigos precisa: buscar por palavras no título, listar quantos artigos '
    'existem por autor, filtrar por tag exata e ordenar por data. Escreva o mapping e justifique o tipo '
    'de cada campo.',
  'esperado': 'Um mapping com a decisão text/keyword/multi-field explicada campo a campo.',
  'solucao_codigo': 'PUT artigos\n'
    '{ "mappings": { "properties": {\n'
    '    "titulo": { "type": "text",\n'
    '      "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },\n'
    '    "autor":  { "type": "text",\n'
    '      "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } } },\n'
    '    "tags":   { "type": "keyword" },\n'
    '    "publicado_em": { "type": "date" }\n'
    '} } }\n\n'
    '// agregar por autor usa o sub-campo, nao o campo analisado:\n'
    'GET artigos/_search\n'
    '{ "size": 0, "aggs": { "por_autor": { "terms": { "field": "autor.keyword" } } } }',
  'solucao_comentario': 'titulo é text porque precisa de busca full-text; ganha .keyword por precaução, '
    'caso venha a ser ordenado. autor precisa das duas capacidades ao mesmo tempo — buscar por nome '
    'parcial e agrupar por nome inteiro — e por isso o multi-field é obrigatório: agregar por autor '
    'analisado agruparia por primeiro nome e sobrenome separadamente. tags é keyword puro porque é '
    'vocabulário fechado e nunca será buscado por palavra solta. Note que um campo keyword aceita array '
    'sem declaração especial: no Elasticsearch todo campo é implicitamente multivalorado.',
  'criterio_correcao': 'O ponto central é perceber que autor exige multi-field. Declarar autor apenas '
    'como text inviabiliza a agregação; apenas como keyword inviabiliza a busca parcial.'},

 {'numero': 5, 'titulo': 'must ou filter: onde cada cláusula pertence', 'sistema': 'elasticsearch',
  'dificuldade': 'intermediario', 'tempo_min': 15,
  'enunciado': 'Monte a consulta: artigos que falem sobre "bancos de dados distribuídos", publicados em '
    '2026, com a tag nosql, ordenados por relevância. Decida o que vai em must e o que vai em filter, e '
    'justifique.',
  'esperado': 'Uma bool query com a separação correta e a justificativa em termos de score e cache.',
  'solucao_codigo': 'GET artigos/_search\n'
    '{ "query": { "bool": {\n'
    '    "must": [\n'
    '      { "match": { "titulo": "bancos de dados distribuídos" } }\n'
    '    ],\n'
    '    "filter": [\n'
    '      { "term":  { "tags": "nosql" } },\n'
    '      { "range": { "publicado_em": { "gte": "2026-01-01", "lt": "2027-01-01" } } }\n'
    '    ]\n'
    '} } }',
  'solucao_comentario': 'Só o match vai em must, porque só ele exprime "quão bem este artigo responde à '
    'pergunta". Tag e intervalo de data são critérios binários: ou o documento satisfaz ou não, e nada '
    'neles torna um artigo mais relevante que outro. Em filter, o Elasticsearch pula o cálculo de score e '
    'pode reaproveitar o resultado em cache de bitset entre consultas — o mesmo filtro de ano será '
    'reutilizado por milhares de buscas diferentes. Colocar tudo em must funcionaria e devolveria os '
    'mesmos documentos, mas paga cálculo desnecessário e perde o cache.',
  'criterio_correcao': 'A separação precisa estar correta e a justificativa precisa mencionar score e '
    'cache. Justificar apenas por "boa prática" não atende.'},

 {'numero': 6, 'titulo': 'Uma agregação que responde a uma pergunta editorial', 'sistema': 'elasticsearch',
  'dificuldade': 'intermediario', 'tempo_min': 15,
  'enunciado': 'Produza, em uma única consulta, os cinco autores com mais artigos publicados em 2026 e, '
    'para cada um, a data do artigo mais recente. Não traga nenhum documento no resultado.',
  'esperado': 'Uma agregação terms com sub-agregação e size: 0.',
  'solucao_codigo': 'GET artigos/_search\n'
    '{\n'
    '  "size": 0,\n'
    '  "query": { "range": { "publicado_em": { "gte": "2026-01-01", "lt": "2027-01-01" } } },\n'
    '  "aggs": {\n'
    '    "top_autores": {\n'
    '      "terms": { "field": "autor.keyword", "size": 5, "order": { "_count": "desc" } },\n'
    '      "aggs": {\n'
    '        "mais_recente": { "max": { "field": "publicado_em" } }\n'
    '      }\n'
    '    }\n'
    '  }\n'
    '}',
  'solucao_comentario': 'Agregações aninham: a max roda dentro de cada bucket produzido pela terms. O '
    'size: 5 limita os buckets; o size: 0 no nível da consulta impede que documentos sejam devolvidos. '
    'Um detalhe importante para produção: em cluster com vários shards, o doc_count da terms é aproximado, '
    'porque cada shard devolve seu top parcial. O campo sum_other_doc_count na resposta informa quantos '
    'documentos ficaram fora dos buckets retornados.',
  'criterio_correcao': 'Precisa ter size: 0, usar o sub-campo keyword e aninhar a sub-agregação dentro '
    'da terms. Mencionar a aproximação em cluster multi-shard é diferencial.'},

 {'numero': 7, 'titulo': 'Por que a busca semântica não achou o código do produto', 'sistema': 'vetorial',
  'dificuldade': 'desafio', 'tempo_min': 20,
  'enunciado': 'Uma busca semântica sobre catálogo funciona bem para "notebook leve para viagem", mas '
    'falha quando o usuário digita o código exato "XPS-13-9370" — o produto existe e não é retornado. '
    'Explique a causa e proponha uma solução.',
  'esperado': 'O diagnóstico do ponto cego da busca vetorial e uma estratégia híbrida.',
  'solucao_codigo': 'GET catalogo/_search\n'
    '{\n'
    '  "query": {                                   // ramo lexical: pega o codigo exato\n'
    '    "bool": { "should": [\n'
    '      { "term":  { "sku": "XPS-13-9370" } },\n'
    '      { "match": { "descricao": "XPS-13-9370" } }\n'
    '    ] }\n'
    '  },\n'
    '  "knn": {                                     // ramo semantico: pega a intencao\n'
    '    "field": "embedding",\n'
    '    "query_vector": [ /* embedding da consulta */ ],\n'
    '    "k": 10, "num_candidates": 100\n'
    '  },\n'
    '  "rank": { "rrf": { "rank_window_size": 50, "rank_constant": 20 } }\n'
    '}',
  'solucao_comentario': 'Modelos de embedding são treinados em linguagem natural. Um código como '
    'XPS-13-9370 é tokenizado em fragmentos sem significado semântico, e o vetor resultante não se '
    'aproxima do vetor do produto — a busca vetorial é estruturalmente cega a identificadores. Já o BM25 '
    'acerta esse caso com facilidade, porque o termo é raro e o IDF o premia. A solução é híbrida, e o '
    'RRF é a forma correta de fundir: em vez de somar scores de escalas incompatíveis, ele soma o inverso '
    'da posição de cada documento em cada ranking, o que dispensa normalização. Um campo sku declarado '
    'como keyword garante a correspondência exata.',
  'criterio_correcao': 'Identificar que o ponto cego é estrutural, não um defeito de configuração, e '
    'propor combinação com busca lexical. Propor apenas "aumentar o k" não atende.'},

 {'numero': 8, 'titulo': 'Onde mora a verdade', 'sistema': 'integrador',
  'dificuldade': 'desafio', 'tempo_min': 20,
  'enunciado': 'Um time propõe: "vamos gravar os pedidos direto no Elasticsearch, já que precisamos de '
    'busca e ele é mais rápido para consultar. Elimina o MongoDB e um ponto de sincronização." '
    'Você é responsável pela arquitetura. Responda ao time com argumentos técnicos e proponha uma alternativa.',
  'esperado': 'Uma análise que identifique os riscos concretos e desenhe o fluxo alternativo.',
  'solucao_codigo': '// Fluxo proposto — a verdade em um lugar so, indice derivado e reconstruivel\n'
    '\n'
    '   aplicacao\n'
    '       |\n'
    '       v  escrita confirmada (write concern majority)\n'
    '   [ MongoDB ]  <-- fonte da verdade\n'
    '       |\n'
    '       v  change stream (ou CDC)\n'
    '   [ pipeline de sincronizacao ]  <-- reexecutavel do zero\n'
    '       |\n'
    '       v  bulk\n'
    '   [ Elasticsearch ]  <-- indice derivado, descartavel\n'
    '\n'
    '// reconstrucao completa deve ser um procedimento normal, nao uma emergencia:\n'
    '//   1. cria indice novo com o mapping atualizado\n'
    '//   2. reindexa a partir do MongoDB\n'
    '//   3. troca o alias para o indice novo\n'
    '//   4. remove o antigo',
  'solucao_comentario': 'Os riscos concretos: o Elasticsearch é near real-time, então um pedido gravado '
    'não é imediatamente pesquisável, o que quebra o fluxo de confirmação ao cliente; não há transação '
    'multi-documento, então baixar estoque e criar pedido não podem ser atômicos; e mudar o tipo de um '
    'campo exige reindexar — o que, sem fonte externa, significa reindexar a partir do próprio índice, '
    'carregando qualquer defeito de mapping adiante. O argumento decisivo é esse último: um índice '
    'derivado pode ser reconstruído porque existe uma fonte; se ele for a fonte, toda evolução de esquema '
    'vira migração de risco. A alternativa mantém a busca — o time ganha o que queria — sem pôr a verdade '
    'num sistema projetado para ser descartável.',
  'criterio_correcao': 'Precisa citar pelo menos dois riscos técnicos concretos (near real-time, ausência '
    'de transação, reindexação) e desenhar um fluxo em que o índice seja reconstruível. Responder apenas '
    '"não é boa prática" não atende.'},

 {'numero': 9, 'titulo': 'A busca que falha só para alguns usuários', 'sistema': 'integrador',
  'dificuldade': 'intermediario', 'tempo_min': 15,
  'enunciado': 'Usuários relatam que buscar por "Sao Paulo" não retorna nada, enquanto "São Paulo" '
    'funciona. O campo é text com analyzer standard. Reproduza o diagnóstico e implemente a correção.',
  'esperado': 'O diagnóstico via _analyze e um analyzer customizado com asciifolding.',
  'solucao_codigo': '// 1. diagnostico: os tokens preservam o acento\n'
    'POST _analyze\n'
    '{ "analyzer": "standard", "text": "São Paulo" }\n'
    '// -> [ "são", "paulo" ]     e "sao" nunca casa com "são"\n\n'
    '// 2. correcao: analyzer com asciifolding, aplicado na indexacao e na busca\n'
    'PUT cidades\n'
    '{\n'
    '  "settings": { "analysis": { "analyzer": {\n'
    '    "pt_sem_acento": {\n'
    '      "tokenizer": "standard",\n'
    '      "filter": [ "lowercase", "asciifolding" ]\n'
    '    }\n'
    '  } } },\n'
    '  "mappings": { "properties": {\n'
    '    "nome": {\n'
    '      "type": "text",\n'
    '      "analyzer": "pt_sem_acento",\n'
    '      "fields": { "keyword": { "type": "keyword", "ignore_above": 256 } }\n'
    '    }\n'
    '  } }\n'
    '}\n\n'
    '// 3. verificacao\n'
    'POST cidades/_analyze\n'
    '{ "field": "nome", "text": "São Paulo" }   // -> [ "sao", "paulo" ]',
  'solucao_comentario': 'A verificação com _analyze antes e depois é o que transforma suposição em '
    'diagnóstico. O asciifolding precisa valer para indexação e busca — se só a busca dobrasse o acento, '
    '"sao" continuaria não encontrando o termo "são" gravado no índice. Detalhe operacional importante: '
    'mudar analyzer de um campo existente exige reindexar, porque os termos já gravados foram produzidos '
    'pelo analyzer antigo. Este é exatamente o erro que o roteiro do Lab 2 comete ao afirmar que o '
    'standard já resolveria isso.',
  'criterio_correcao': 'Precisa usar _analyze como diagnóstico, aplicar asciifolding e reconhecer que a '
    'mudança exige reindexação dos dados existentes.'},

 {'numero': 10, 'titulo': 'Estimar antes de indexar', 'sistema': 'elasticsearch',
  'dificuldade': 'desafio', 'tempo_min': 20,
  'enunciado': 'Você vai indexar 5 milhões de documentos com embeddings de 768 dimensões para um sistema '
    'de RAG. Estime a memória necessária para os vetores, com e sem quantização int8, e discuta as '
    'implicações da escolha.',
  'esperado': 'O cálculo numérico e uma discussão do compromisso entre memória, precisão e custo.',
  'solucao_codigo': '// float32: 4 bytes por dimensao\n'
    '5.000.000 x 768 x 4 bytes  = 15.360.000.000 bytes  ~= 14,3 GiB\n'
    '\n'
    '// int8 (padrao do ES 8.x): 1 byte por dimensao\n'
    '5.000.000 x 768 x 1 byte   =  3.840.000.000 bytes  ~=  3,6 GiB\n'
    '\n'
    '// e ainda ha o grafo HNSW, proporcional a m (default 16)\n'
    '\n'
    '// conferir o que o mapping realmente aplicou:\n'
    'GET meu_indice/_mapping\n'
    '// "index_options": { "type": "int8_hnsw", "m": 16, "ef_construction": 100 }',
  'solucao_comentario': 'Quatro vezes menos memória é a diferença entre caber e não caber no heap de um '
    'nó — e o HNSW só é rápido quando o grafo está em memória. O custo é um erro de precisão que aparece '
    'na terceira ou quarta casa decimal do score, como se mediu no laboratório: o knn ficou levemente '
    'abaixo do valor teórico de (1+cos)/2, justamente por causa da quantização. Em recuperação para RAG '
    'isso é irrelevante, porque o que importa é o conjunto dos k vizinhos, não o valor exato do score. '
    'Seria relevante se o score fosse usado como limiar absoluto de decisão. Vale notar que reduzir '
    'dimensões do modelo, quando ele suporta, costuma economizar mais que quantizar.',
  'criterio_correcao': 'O cálculo precisa estar correto e a discussão precisa reconhecer que a perda de '
    'precisão é aceitável para ranking e problemática para limiar absoluto. Lembrar do grafo HNSW além '
    'dos vetores é diferencial.'},
]

QUIZ = [
 {'numero': 1,
  'pergunta': 'Um índice do Elasticsearch está com status yellow. O que se pode afirmar com certeza?',
  'alternativas': [
    'Há perda de dados e o índice precisa ser restaurado de backup.',
    'Todos os shards primários estão ativos, mas pelo menos uma réplica não foi alocada.',
    'O cluster está sobrecarregado e rejeitando escritas.',
    'O mapping do índice está inconsistente com os documentos gravados.'],
  'correta': 'B',
  'justificativa': 'Yellow significa primários ativos e alguma réplica não alocada — o índice está '
    'plenamente funcional, apenas sem redundância. A alternativa A confunde yellow com red, que é o estado '
    'em que falta primário. C e D são tentadoras porque yellow parece alerta de saúde, mas o estado do '
    'cluster reporta apenas alocação de shards, nada sobre carga ou mapping.'},

 {'numero': 2,
  'pergunta': 'db.alunos.updateOne({ nome: "Ana" }, { idade: 24 }) foi executado. Qual o resultado?',
  'alternativas': [
    'A idade de Ana é atualizada para 24 e os demais campos permanecem.',
    'O comando falha com erro de sintaxe por faltar operador.',
    'O documento inteiro é substituído e passa a conter apenas idade: 24.',
    'Nada acontece, porque o segundo argumento não contém operador de atualização.'],
  'correta': 'C',
  'justificativa': 'Sem operador, o MongoDB interpreta o segundo argumento como substituição integral: '
    'nome e todos os outros campos são perdidos. A alternativa A é o que quase todo mundo espera, e é '
    'justamente por isso que o erro é perigoso. B é tentadora porque um erro seria o comportamento '
    'defensivo — mas não há erro. D descreveria um no-op, que também não ocorre.'},

 {'numero': 3,
  'pergunta': 'Por que uma agregação terms sobre um campo declarado apenas como text falha?',
  'alternativas': [
    'Porque campos text não são indexados.',
    'Porque o campo foi tokenizado e não existe um valor único por documento para formar buckets.',
    'Porque agregações só funcionam sobre campos numéricos.',
    'Porque falta declarar doc_values no mapping.'],
  'correta': 'B',
  'justificativa': 'O campo text é quebrado em termos pelo analyzer, então "São Paulo" vira dois termos e '
    'não há um valor íntegro para agrupar. A alternativa A é falsa — text é indexado, é justamente o que o '
    'torna pesquisável. C é falsa, pois terms agrega sobre keyword normalmente. D chega perto do mecanismo '
    'real (campos text não têm doc_values habilitados), mas a causa raiz é a tokenização, e habilitar '
    'fielddata seria a solução errada.'},

 {'numero': 4,
  'pergunta': 'Você precisa que um sistema de e-commerce baixe estoque e registre a venda de forma '
    'atômica, e também ofereça busca por relevância no catálogo. Qual arranjo é adequado?',
  'alternativas': [
    'Somente Elasticsearch, usando bulk para agrupar as duas operações.',
    'Somente MongoDB, implementando a busca com expressões regulares.',
    'MongoDB como fonte da verdade e Elasticsearch como índice derivado, sincronizados por um pipeline reexecutável.',
    'Elasticsearch como fonte da verdade e MongoDB como cache de leitura.'],
  'correta': 'C',
  'justificativa': 'Cada sistema no papel para o qual foi construído. A alternativa A falha porque bulk '
    'não é transação: agrupa requisições, não garante atomicidade. B funciona mal — regex não ordena por '
    'relevância e não usa índice invertido, degradando com o volume. D inverte os papéis e põe a verdade '
    'num sistema near real-time, sem transação e cuja evolução de esquema exige reindexação.'},

 {'numero': 5,
  'pergunta': 'O explain de uma consulta MongoDB mostra IXSCAN, um estágio SORT e totalDocsExamined muito '
    'maior que nReturned. Qual a interpretação?',
  'alternativas': [
    'O índice está corrompido e precisa ser reconstruído.',
    'O índice atende ao filtro mas não à ordenação, então o servidor ordena em memória.',
    'A consulta não usa índice algum.',
    'O número alto de documentos examinados é normal quando há limit.'],
  'correta': 'B',
  'justificativa': 'A presença simultânea de IXSCAN e SORT é a assinatura desse problema: o índice serviu '
    'ao filtro, mas a ordenação teve de ser feita depois, em memória, sobre todos os documentos que '
    'casaram. C é contrariada pelo próprio IXSCAN. A é raro e não se diagnostica assim. D é a tentadora: '
    'com um índice adequado, o limit permite parar cedo justamente porque não há SORT no caminho.'},

 {'numero': 6,
  'pergunta': 'Qual afirmação sobre o teorema CAP é correta?',
  'alternativas': [
    'Todo sistema distribuído deve escolher permanentemente dois entre consistência, disponibilidade e tolerância a partição.',
    'Durante uma partição de rede, o sistema precisa escolher entre responder com dado possivelmente desatualizado ou recusar a resposta.',
    'Bancos NoSQL são AP e bancos relacionais são CA, por definição do modelo de dados.',
    'Tolerância a partição pode ser dispensada em sistemas com rede confiável.'],
  'correta': 'B',
  'justificativa': 'O teorema descreve a escolha durante a partição, não uma propriedade permanente. '
    'A alternativa A é a versão popular e distorcida — fora de partição, um sistema pode ser consistente e '
    'disponível ao mesmo tempo. C é falsa porque a classificação depende de configuração, não de produto '
    'ou modelo de dados. D é sedutora, mas partição não é escolha de projeto: é evento que ocorre em '
    'qualquer rede real.'},

 {'numero': 7,
  'pergunta': 'Ao comparar script_score com cosineSimilarity e a query knn sobre os mesmos vetores, '
    'observou-se scores 1,99895 e 0,99936 para o mesmo documento. Por quê?',
  'alternativas': [
    'A query knn calculou errado, porque é aproximada.',
    'São fórmulas diferentes: script_score usa cos + 1,0 e o knn usa (1 + cos) / 2, e o knn ainda opera sobre vetores quantizados.',
    'O script_score considerou outros documentos no cálculo do score.',
    'O knn normalizou os vetores antes de comparar e o script_score não.'],
  'correta': 'B',
  'justificativa': 'As faixas são diferentes por definição — 0 a 2 contra 0 a 1 — e a pequena diferença '
    'restante vem da quantização int8 do HNSW. A alternativa A trata "aproximado" como "errado": o '
    'ranking foi idêntico nos dois caminhos. C descreve o BM25, cujo score depende de estatísticas do '
    'corpus, não o cosseno, que é calculado par a par. D inverte: a similaridade de cosseno já é '
    'invariante ao comprimento, por construção.'},

 {'numero': 8,
  'pergunta': 'Um _bulk com mil documentos retornou HTTP 200. O que se pode concluir?',
  'alternativas': [
    'Todos os mil documentos foram indexados com sucesso.',
    'A requisição foi processada, mas pode haver falhas por item, que só o campo errors revela.',
    'Os documentos foram aceitos e já estão pesquisáveis.',
    'Nenhum documento falhou, mas alguns podem estar aguardando refresh.'],
  'correta': 'B',
  'justificativa': 'O bulk devolve 200 mesmo com falhas parciais — é obrigatório inspecionar errors e o '
    'status de cada item. A é o erro clássico. C soma dois enganos: além da falha parcial, ignora o '
    'near real-time. D é a mais sutil: acerta o refresh, mas afirma indevidamente que nenhum item falhou.'},

 {'numero': 9,
  'pergunta': 'Um índice do Elasticsearch com 2 documentos reporta N = 3 no explain do BM25. Qual a explicação?',
  'alternativas': [
    'Erro de contagem que se corrige com refresh.',
    'Há um documento em outro shard que não aparece na contagem.',
    'As estatísticas são lidas do segmento e incluem documentos marcados como deletados por um update anterior.',
    'O BM25 soma 1 ao total para evitar divisão por zero.'],
  'correta': 'C',
  'justificativa': 'Segmentos Lucene são imutáveis: um update grava versão nova e marca a antiga como '
    'deletada, e as estatísticas contam a marcada até o merge. A alternativa D é tentadora porque a '
    'fórmula do IDF realmente tem constantes de suavização — mas elas são 0,5, e não explicam N. '
    'A e B propõem causas plausíveis que o experimento controlado descarta.'},

 {'numero': 10,
  'pergunta': 'Um índice foi criado a partir de um template que aponta para uma política ILM inexistente. '
    'O que acontece?',
  'alternativas': [
    'A criação do índice falha com erro explícito.',
    'O índice é criado normalmente e o ILM ignora o setting.',
    'O índice é criado com acknowledged: true, e o erro só aparece de forma assíncrona em _ilm/explain.',
    'O template é rejeitado no momento em que é registrado.'],
  'correta': 'C',
  'justificativa': 'A validação não ocorre na criação: o setting é apenas gravado, e quem tenta resolver '
    'a política é o serviço de ILM, em segundo plano. Verificado em teste: acknowledged: true na criação '
    'e step: ERROR no _ilm/explain. As alternativas A e D descrevem o comportamento defensivo que se '
    'esperaria; B parece inofensiva, mas o índice fica marcado como managed e nunca rotaciona.'},
]

TABELA_DECISAO = [
 {'requisito': 'Transação envolvendo múltiplos documentos, com garantia de tudo-ou-nada',
  'sistema': 'MongoDB',
  'porque': 'Transações multi-documento com ACID desde a versão 4.0. O Elasticsearch não oferece transação.'},
 {'requisito': 'Busca por relevância em texto livre, ordenada por qualidade da correspondência',
  'sistema': 'Elasticsearch',
  'porque': 'Índice invertido com BM25. No MongoDB, o índice de texto existe mas é limitado, e regex não usa índice.'},
 {'requisito': 'Leitura do estado atual de um registro por identificador, imediatamente após a escrita',
  'sistema': 'MongoDB',
  'porque': 'Leitura consistente logo após a confirmação da escrita. O Elasticsearch é near real-time e '
            'só torna o documento pesquisável no refresh seguinte.'},
 {'requisito': 'Agregação exploratória sobre dezenas de milhões de eventos, com facetas e filtros combinados',
  'sistema': 'Elasticsearch',
  'porque': 'Agregações distribuídas sobre estruturas colunares, executadas em paralelo por shard.'},
 {'requisito': 'Busca semântica por significado, para RAG',
  'sistema': 'Elasticsearch',
  'porque': 'dense_vector com HNSW e query knn nativa a partir da versão 8. O MongoDB Atlas oferece '
            'equivalente, mas não a edição community usada no laboratório.'},
 {'requisito': 'Garantia de unicidade de um campo sob escrita concorrente',
  'sistema': 'MongoDB',
  'porque': 'Índice único validado pelo servidor no momento da escrita, devolvendo E11000. O Elasticsearch '
            'só garante unicidade do _id.'},
 {'requisito': 'Correlacionar logs de vários serviços numa linha do tempo comum',
  'sistema': 'Elasticsearch',
  'porque': 'É o caso de uso para o qual a stack foi desenhada — foi exatamente o que o Lab 2 montou.'},
 {'requisito': 'Fonte da verdade de qualquer dado de negócio',
  'sistema': 'MongoDB',
  'porque': 'Índice de busca é derivado e descartável por princípio. Se ele for a fonte, toda evolução de '
            'mapping vira migração de risco, sem origem para reconstruir.'},
]

GLOSSARIO = [
 {'termo': 'BSON', 'definicao': 'Formato binário do MongoDB que estende o JSON com tipos como data, '
   'decimal128, binário e ObjectId.'},
 {'termo': 'ObjectId', 'definicao': 'Identificador de 12 bytes gerado no cliente, contendo timestamp, '
   'valor aleatório por processo e contador.'},
 {'termo': 'Cursor', 'definicao': 'Ponteiro devolvido pelo find, que entrega documentos em lotes e aceita '
   'encadear sort, limit e skip.'},
 {'termo': 'COLLSCAN', 'definicao': 'Estágio do explain indicando que a coleção inteira foi varrida, '
   'documento por documento.'},
 {'termo': 'IXSCAN', 'definicao': 'Estágio em que o índice foi percorrido para localizar as chaves que '
   'casam com o filtro.'},
 {'termo': 'totalDocsExamined', 'definicao': 'Quantos documentos o servidor abriu para responder. '
   'Comparado a nReturned, mede a qualidade do índice.'},
 {'termo': 'Prefixo à esquerda', 'definicao': 'Regra segundo a qual um índice composto atende consultas '
   'sobre seus primeiros campos, na ordem declarada, mas não sobre os posteriores isoladamente.'},
 {'termo': 'Pipeline de agregação', 'definicao': 'Sequência de estágios em que cada um recebe a saída do '
   'anterior; a ordem altera o resultado e o custo.'},
 {'termo': '$facet', 'definicao': 'Estágio que executa vários pipelines independentes sobre a mesma '
   'entrada, numa única passada pelos dados.'},
 {'termo': 'Shard', 'definicao': 'Partição de um índice do Elasticsearch; cada shard é um índice Lucene '
   'completo e independente.'},
 {'termo': 'Réplica', 'definicao': 'Cópia de um shard primário, que oferece tolerância a falha e '
   'capacidade adicional de leitura.'},
 {'termo': 'Índice invertido', 'definicao': 'Estrutura que mapeia cada termo para a lista de documentos '
   'em que ele ocorre, com frequência e posição.'},
 {'termo': 'Analyzer', 'definicao': 'Cadeia que transforma texto em termos: filtros de caractere, '
   'tokenizador e filtros de token.'},
 {'termo': 'asciifolding', 'definicao': 'Filtro de token que converte caracteres acentuados em seus '
   'equivalentes ASCII, tornando a busca insensível a acento.'},
 {'termo': 'text e keyword', 'definicao': 'text é analisado e serve a busca full-text; keyword é um termo '
   'único e serve a filtro exato, ordenação e agregação.'},
 {'termo': 'BM25', 'definicao': 'Função de relevância padrão do Elasticsearch, combinando frequência do '
   'termo com saturação, frequência inversa nos documentos e normalização por tamanho.'},
 {'termo': 'Near real-time', 'definicao': 'Propriedade de o documento indexado só se tornar pesquisável '
   'após o refresh, que por padrão ocorre a cada segundo.'},
 {'termo': 'Alias', 'definicao': 'Nome estável que aponta para um ou mais índices físicos, permitindo '
   'trocá-los sem alterar a aplicação.'},
 {'termo': 'dense_vector', 'definicao': 'Tipo de campo que armazena um embedding, com número de dimensões '
   'fixo e igual ao do modelo que o gerou.'},
 {'termo': 'HNSW', 'definicao': 'Grafo navegável de mundo pequeno em camadas, que encontra vizinhos '
   'aproximados em tempo sublinear.'},
 {'termo': 'Similaridade de cosseno', 'definicao': 'Medida do ângulo entre dois vetores, de -1 a 1, '
   'invariante ao comprimento deles.'},
 {'termo': 'RRF', 'definicao': 'Reciprocal Rank Fusion: funde rankings somando o inverso da posição de '
   'cada documento, dispensando normalização de scores.'},
 {'termo': 'RAG', 'definicao': 'Recuperação de trechos relevantes numa base de conhecimento para compor '
   'o contexto de um modelo de linguagem antes da geração.'},
 {'termo': 'GELF', 'definicao': 'Graylog Extended Log Format; driver de log do Docker que envia a saída '
   'do contêiner por UDP a um coletor.'},
 {'termo': 'ILM', 'definicao': 'Index Lifecycle Management: automatiza rollover, migração entre camadas '
   'de armazenamento e expurgo de índices.'},
]

LEITURAS = [
 'Documentação oficial do MongoDB, seção Aggregation Pipeline Optimization — explica quais reordenações o '
 'planejador faz sozinho e quais dependem de você.',
 'Elasticsearch: The Definitive Guide (Gormley e Tong) — anterior ao 8.x, mas a melhor explicação em '
 'português ou inglês sobre índice invertido, analyzers e relevância.',
 'Designing Data-Intensive Applications (Martin Kleppmann), capítulos 3 e 5 — estruturas de armazenamento '
 'e replicação, com o rigor que falta na maioria dos tutoriais.',
 'Artigo original do HNSW (Malkov e Yashunin, 2016) — leitura acessível para quem quer entender por que a '
 'busca aproximada funciona.',
 'Documentação do Elasticsearch sobre Retrievers e RRF — a forma atual de fazer busca híbrida, que '
 'substitui a combinação manual por script_score usada no laboratório.',
 'MongoDB University, curso M201 (Performance) — gratuito, e cobre explain e estratégia de índices com '
 'muito mais profundidade do que um laboratório permite.',
]
