# Laboratório 01 - MongoDB

Bancos de Dados Não Relacionais - CEUB
Prof. Raul Carvalho de Souza
Aluno: Guilherme Levi

Ambiente usado: MongoDB 8.2.12, mongosh 2.9.2, banco dbNoSQLBD.
Os comandos estão nos arquivos da pasta Playgrounds, feitos na extensão MongoDB do VSCode.

## Observação sobre o ambiente

Rodei o laboratório no meu Mac com OrbStack em vez da VM. O roteiro pede a imagem mongo:4.4, mas nem ela nem a 8.0 sobem aqui. O container ficava reiniciando sem parar e o log mostrava sempre a mesma mensagem:

```
MongoDB cannot start: Linux kernel versions 6.19 and newer has a known incompatibility with this version of MongoDB.
```

É o bug SERVER-121912. Conferi o kernel com `docker run --rm alpine uname -r` e deu 7.0.14, que é o kernel do OrbStack. Troquei a imagem para mongo:8.2, que já tem a correção, e subiu normal. Como essa imagem já vem com o mongosh embutido, não precisei fazer a Parte 2 (instalação pelo apt). É por isso que as versões aqui são diferentes das do enunciado.

## Parte 1 - Preparação do ambiente

**EX 1.1** O container é o mongodb-container e a porta é 0.0.0.0:27017->27017/tcp. O nome vem do container_name que está no docker-compose.yml. Se não tivesse essa linha o Compose criaria um nome automático tipo nosql-mongodb-1. O mapeamento faz a porta 27017 do meu Mac apontar para a 27017 de dentro do container, e é isso que deixa a extensão do VSCode conectar em localhost:27017.

**EX 1.2** Com o -d o container sobe em segundo plano e o terminal volta na hora. Sem o -d o log do container toma conta do terminal e se eu apertar Ctrl+C o container cai junto. Na prática usei o -d e depois `docker logs -f mongodb-container` quando quis acompanhar o log, assim dá para parar de olhar sem parar o banco.

**EX 1.3** Serve para garantir que todo mundo comece do mesmo ponto, sem sobra de teste anterior. O motivo mais importante é que o entrypoint da imagem só executa os scripts que estão em /docker-entrypoint-initdb.d/, no caso o init-mongo.js, quando a pasta de dados está vazia. Se tiver qualquer arquivo lá o script é ignorado sem avisar nada e o usuário admin não é criado. No meu caso teve ainda um terceiro motivo: os arquivos do WiredTiger gravados por uma versão não são lidos por outra, então como troquei a imagem de 4.4 para 8.2 limpar a pasta virou obrigação.

## Parte 2 - Instalação do mongosh

**EX 2.1** Deu 8.2.12 no servidor, com mongosh 2.9.2. O db.version() mostra a versão do servidor (mongod), enquanto o banner que aparece ao conectar mostra também a do cliente. São dois programas separados e podem ser diferentes, um mongosh 2.x conversa numa boa com servidor 6, 7 ou 8.

**EX 2.2** Sem a senha na URI o mongosh abre um prompt pedindo a senha e não mostra o que eu digito. Com a senha na URI ele conecta direto, sem perguntar nada. A forma com senha embutida é boa para script e para CI, onde não tem ninguém para digitar. Fora isso a interativa é melhor, porque senha na URI fica gravada no histórico do shell, aparece no `ps` para outros usuários da máquina e costuma vazar em log.

**EX 2.3** Apareceram admin, config e local. São os bancos internos do MongoDB: o admin guarda os usuários e as permissões, o config guarda metadados de sharding e sessões, e o local guarda o oplog e coisas que nunca são replicadas para outro nó.

## Parte 3 - Operações básicas

**EX 3.1** O dbExercicio não apareceu. O use só aponta a variável db para aquele nome, não escreve nada em disco. O MongoDB cria banco e coleção de forma preguiçosa, só na hora que o primeiro documento é gravado. Se eu fizesse um `db.teste.insertOne({})` ele apareceria na mesma hora.

**EX 3.2**

```
use dbNoSQLBD          // no mongosh
use('dbNoSQLBD');      // no playground
```

Essa diferença me pegou no começo. O playground é JavaScript puro, então os atalhos do shell (use, show, exit) não funcionam lá, tem que ser a forma de função com parênteses. Quando tentei colar `show dbs` no meio de um bloco deu SyntaxError.

**EX 3.3** É o `db` sozinho no mongosh, ou `db.getName()` no playground. O prompt também mostra, ele muda de `test>` para `dbNoSQLBD>` depois do use.

## Parte 4 - Criação de coleções

**EX 4.1** `db.createCollection("professores");`

**EX 4.2** `db.createCollection("disciplinas");`

**EX 4.3** É o `show collections` no mongosh, ou `db.getCollectionNames()` no playground. Voltou alunos, cursos, disciplinas e professores.

**EX 4.4** Não exige. Se eu fizer um insertOne numa coleção que não existe ele cria na hora, e vale para o banco também. O createCollection só é necessário quando preciso definir alguma opção no momento da criação, tipo validação de schema, coleção capped (que tem tamanho fixo e vai sobrescrevendo os documentos mais antigos) ou time-series. Fora esses casos ele só serve para deixar a intenção explícita.

## Parte 5 - Inserção de documentos

**EX 5.1**

```
db.professores.insertMany([
  { nome: "Raul Carvalho", especialidade: "Bancos NoSQL", anos_experiencia: 12 },
  { nome: "Helena Dias", especialidade: "Engenharia de Dados", anos_experiencia: 8 },
  { nome: "Marcos Prado", especialidade: "Machine Learning", anos_experiencia: 5 }
]);
```

**EX 5.2**

```
db.disciplinas.insertMany([
  { nome: "Bancos de Dados Não Relacionais", carga_horaria: 60, obrigatoria: true },
  { nome: "Tópicos em Big Data", carga_horaria: 40, obrigatoria: false }
]);
```

Aqui prestei atenção nos tipos, a carga_horaria é número e a obrigatoria é booleano, não são string. Isso importa porque "60" e 60 são valores diferentes no BSON e uma busca por um não acha o outro. E o $gt só compara direito em número, em string ele compara na ordem alfabética.

**EX 5.3**

```
db.alunos.insertOne({ nome: "Lucas Moreira", idade: 26, curso: "Data Science", cidade: "Brasília" });
```

Esse documento ficou com um campo que nenhum outro tem, a cidade, e o banco aceitou sem reclamar. É a flexibilidade de schema na prática. Isso volta a aparecer na Parte 10, quando agrupei por cidade e todos os que não têm o campo caíram juntos num grupo com _id: null.

**EX 5.4** O insertOne grava um documento e devolve um insertedId. O insertMany recebe um array e devolve os insertedIds, um ObjectId para cada documento. A diferença que pesa mesmo é desempenho, porque o insertMany manda o lote inteiro numa ida só ao servidor, enquanto vários insertOne custam uma viagem de rede cada. Por padrão o insertMany é ordenado e para no primeiro erro, mas com { ordered: false } ele continua inserindo o resto.

## Parte 6 - Consultas

**EX 6.1** `db.professores.find();`

**EX 6.2** `db.alunos.find({ idade: { $lte: 22 } });`

**EX 6.3** `db.alunos.find({ curso: "Engenharia de Dados" });`

Para igualdade não precisa de operador nenhum, é só campo: valor. Mas é comparação exata e sensível a maiúscula e acento, se eu escrevesse "engenharia de dados" não vinha nada.

**EX 6.4** `db.alunos.findOne();`

A diferença é que o find() devolve um cursor, que é um ponteiro que o servidor vai entregando em lotes para não carregar tudo na memória de uma vez, e por isso aceita encadear .sort(), .limit() e .skip(). O findOne() já devolve o documento pronto e não aceita encadear nada.

**EX 6.5**

| SQL | MongoDB |
|-----|---------|
| > | $gt |
| < | $lt |
| >= | $gte |
| <= | $lte |

Além desses tem o $ne para diferente, o $in para quando o valor está numa lista e o $nin para o contrário.

## Parte 7 - Atualizações

O roteiro manda usar db.estudantes nessa parte, mas essa coleção só existe depois do renameCollection da Parte 10. Rodei em db.alunos. Se rodar como está no PDF não dá erro, o MongoDB só cria uma coleção estudantes vazia e atualiza zero documentos, o que passa despercebido.

**EX 7.1**

```
db.alunos.updateOne(
  { nome: "Ana Costa" },
  { $set: { idade: 24 } }
);
```

**EX 7.2**

```
db.alunos.updateMany(
  {},
  { $set: { email: "sem_email@labmongo.com" } }
);
```

O filtro {} pega todos os documentos. O retorno mostra matchedCount e modifiedCount, que são diferentes quando o valor novo é igual ao que já estava lá.

**EX 7.3**

```
db.alunos.updateMany(
  {},
  { $unset: { email: "" } }
);
```

O "" nem é usado, o $unset só olha o nome do campo. Qualquer valor ali daria no mesmo.

**EX 7.4** O $set cria o campo se ele não existe e sobrescreve se já existe. O $unset apaga a chave do documento. Apagar não é a mesma coisa que gravar null, porque depois do $unset o campo some de vez e passa a ser achado por { email: { $exists: false } }, enquanto com null ele continuaria existindo só que com valor nulo. Uma coisa que aprendi aqui é que o $set é obrigatório, sem ele um `updateOne({nome:"Ana Costa"}, {idade:24})` substituiria o documento inteiro e apagaria o nome e o curso.

## Parte 8 - Remoção

**EX 8.1** `db.alunos.deleteOne({ nome: "Mariana Souza" });`

**EX 8.2**

```
db.temp.insertMany([
  { item: "A", valor: 1 },
  { item: "B", valor: 2 },
  { item: "C", valor: 3 }
]);

db.temp.deleteMany({});
```

Voltou deletedCount: 3. A coleção temp continuou existindo mesmo vazia, com os índices dela. Quem apaga a coleção inteira do catálogo é o db.temp.drop().

**EX 8.3** O deleteOne apaga só o primeiro que bater com o filtro, mesmo que vários batam, e é o mais seguro porque se eu errar o filtro no máximo perco um documento. O deleteMany apaga todos que baterem e serve para limpeza em lote. O que faço para não me arrepender é rodar a condição num find() antes, olhar na tela o que apareceu, e só aí trocar o find por deleteMany. Fora de transação não tem como voltar atrás.

## Parte 9 - Formatação e estatísticas

**EX 9.1** `db.cursos.find().pretty();`

O .pretty() era do shell antigo, o mongo, que imprimia tudo numa linha só. No mongosh de hoje e no playground o resultado já sai formatado, então chamar o método não dá erro mas também não muda nada.

**EX 9.2** `db.alunos.countDocuments();` e deu 3, que são o Carlos, a Ana e o Lucas, depois das remoções da Parte 8. Tem também o estimatedDocumentCount(), que lê os metadados em vez de percorrer a coleção, então é instantâneo em base grande, só que não aceita filtro e pode ficar desatualizado se o banco cair de forma abrupta.

**EX 9.3** `db.cursos.getIndexes();` e só existe o _id_. Ele é criado automaticamente em qualquer coleção e não dá para remover, porque é ele que garante que a chave primária não repita. Reparei que o nome do índice vem do campo mais a direção, então { nome: 1 } vira nome_1 e { curso: 1, idade: -1 } vira curso_1_idade_-1. É esse nome que preciso passar depois no dropIndex.

**EX 9.4** O collections é quantas coleções o banco tem. O dataSize é a soma do tamanho dos documentos em bytes, o dado bruto, sem contar índice. Olhei dois campos vizinhos que ajudam a entender: o storageSize é o espaço que está realmente ocupado no disco, e costuma ser menor que o dataSize por causa da compressão do WiredTiger, e o indexSize é o quanto os índices custam, que sobe a cada createIndex. Esse indexSize é a prova do que a Parte 13 fala, que índice acelera leitura mas ocupa espaço.

## Parte 10 - Operações avançadas

O renameCollection é a virada do laboratório, daqui para frente a coleção chama estudantes. Ele mantém os documentos e os índices, muda só o nome. Se rodar duas vezes dá erro porque alunos já não existe mais.

**EX 10.1** `db.estudantes.find().sort({ idade: -1 });`

No sort o 1 é crescente e o -1 é decrescente.

**EX 10.2** `db.estudantes.find().limit(3);`

**EX 10.3**

```
db.estudantes.aggregate([
  { $group: { _id: "$cidade", total: { $sum: 1 } } }
]);
```

Rodando antes dos inserts da Parte 12 veio _id: null com total 2 e Brasília com total 1, porque só o Lucas tinha o campo cidade. Todo documento que não tem o campo do agrupamento cai em null. Não é erro, é assim que o $group trata campo que não existe.

**EX 10.4** `db.estudantes.find().sort({ idade: 1 }).limit(2);`

A ordem que eu escrevo o sort e o limit não muda o resultado, porque o planejador sempre ordena antes de cortar. Quando o campo ordenado tem índice essa combinação fica bem rápida, porque o servidor percorre o índice já na ordem certa e para assim que chega no limite, sem precisar carregar e ordenar a coleção toda na memória.

## Parte 11 - Controle de usuários

**EX 11.1**

```
use dbNoSQLBD

db.createUser({
  user: "leitura_user",
  pwd: "senha123",
  roles: [ { role: "read", db: "dbNoSQLBD" } ]
});
```

O usuário é criado no banco em que eu estou, e esse banco vira o authSource dele, que é onde o servidor vai procurar a credencial na hora de autenticar. Por isso a conexão do admin precisa de ?authSource=admin, já que ele foi criado no banco admin e não no dbNoSQLBD.

**EX 11.2** Conectei assim:

```
docker exec -it mongodb-container mongosh "mongodb://leitura_user:senha123@localhost:27017/dbNoSQLBD"
```

O find funcionou normal, mas o insertOne deu erro:

```
MongoServerError: not authorized on dbNoSQLBD to execute command insert
```

Isso acontece porque a role read só libera comando de leitura, e a permissão é conferida pelo servidor a cada operação, não na hora de conectar. Ou seja, conectar sem erro não quer dizer que posso fazer tudo, o usuário entra normal e só descobre o limite quando tenta escrever.

**EX 11.3**

| Operação | read | readWrite |
|---|---|---|
| find, count, aggregate | sim | sim |
| insert, update, delete | não | sim |
| createCollection, createIndex, drop | não | sim |

Nenhuma das duas deixa criar usuário, mexer em permissão ou entrar em outro banco. Para isso precisa de role administrativa tipo dbAdmin, userAdmin ou root, que é a que o admin do container tem. A ideia por trás é o menor privilégio, dar para cada aplicação só o que ela precisa. Um sistema que só gera relatório recebe read, aí se tiver um bug ou a senha vazar ninguém apaga dado.

## Parte 12 - Aggregation Framework

O pipeline funciona como uma esteira, cada estágio recebe o que o anterior devolveu. O $ na frente do nome do campo quer dizer "o valor desse campo", sem o $ seria a string literal. O _id do $group é o campo que define os grupos, e _id: null junta tudo num resultado só.

**EX 12.1**

```
db.estudantes.aggregate([
  { $group: { _id: "$curso", menor_nota: { $min: "$nota" } } }
]);
```

**EX 12.2**

```
db.estudantes.aggregate([
  { $match: { cidade: "São Paulo" } },
  { $group: { _id: "$cidade", media_nota: { $avg: "$nota" } } }
]);
```

Deu 6.5, que é a nota do Ricardo Mendes, o único de São Paulo. Uma coisa importante do $avg é que ele ignora quem não tem o campo, em vez de contar como zero. Por isso as médias por curso não ficaram estragadas pelo Carlos, pela Ana e pelo Lucas, que não têm nota. Já o $sum: 1 conta o documento de qualquer jeito, tendo o campo ou não.

**EX 12.3**

```
db.estudantes.aggregate([
  { $project: {
    nome: 1,
    nota: 1,
    conceito: {
      $switch: {
        branches: [
          { case: { $gte: ["$nota", 9] }, then: "A" },
          { case: { $gte: ["$nota", 7] }, then: "B" }
        ],
        default: "C"
      }
    }
  } }
]);
```

A ordem dos branches faz diferença, porque o primeiro case verdadeiro ganha e os outros nem são testados. Se eu invertesse as duas linhas a nota 9.7 cairia em B, já que o $gte: 7 seria verdadeiro primeiro. Quem não tem nota cai no default e fica com C.

**EX 12.4**

```
db.estudantes.aggregate([
  { $facet: {
    total_estudantes: [ { $count: "total" } ],
    maior_nota: [ { $group: { _id: null, maximo: { $max: "$nota" } } } ]
  } }
]);
```

O $facet roda vários pipelines independentes em cima da mesma entrada, numa passada só pelos dados. O _id: null é o jeito padrão de calcular um agregado da coleção inteira.

**EX 12.5** O $match antes do $group filtra os documentos crus e é o mesmo que o WHERE do SQL. É sempre melhor deixar nessa posição quando dá, porque diminui o volume que entra na agregação e ainda consegue usar índice, o que não é mais possível depois que os dados já foram agrupados.

```
{ $match: { cidade: "Brasília" } },
{ $group: { _id: "$curso", media_nota: { $avg: "$nota" } } }
```

O $match depois do $group filtra o resultado já agregado e é o mesmo que o HAVING. Só nessa posição dá para filtrar por media_nota, que é um campo que nem existia antes do agrupamento.

```
{ $group: { _id: "$curso", media_nota: { $avg: "$nota" } } },
{ $match: { media_nota: { $gt: 8 } } }
```

O pipeline do item 12.10 usa os dois no mesmo comando, então serve de exemplo dos dois casos de uma vez.

Uma observação sobre o $lookup: ele sempre devolve um array no campo do "as", mesmo quando só bate um documento. É por isso que existe o $unwind, que quebra o array em um documento por item e deixa o resultado parecido com um JOIN de SQL. Só que o $unwind joga fora os documentos cujo array veio vazio, a não ser que eu use preserveNullAndEmptyArrays: true.

## Parte 13 - Indexação

A ordem de execução importa aqui, porque para mostrar o efeito do índice eu preciso medir antes de criar.

**EX 13.1**

```
db.estudantes.createIndex({ cidade: 1 });
db.estudantes.getIndexes();
```

**EX 13.2** Antes de criar o índice o stage era COLLSCAN, com totalDocsExamined: 8 e totalKeysExamined: 0. Depois virou FETCH com um IXSCAN dentro, e o totalKeysExamined deixou de ser zero.

COLLSCAN é collection scan, quer dizer que o MongoDB leu todos os documentos um por um comparando o campo. Aparecem dois estágios porque o índice guarda só o campo indexado e o endereço do documento, então o IXSCAN percorre o índice e acha as chaves que batem, e o FETCH usa esses endereços para ir buscar os documentos inteiros no disco.

O que mudou de verdade não foi o tempo, que com 8 documentos é irrelevante e às vezes até piora, foi o totalDocsExamined, que caiu de 8 para só os documentos que interessam. É esse número que faz diferença quando a coleção cresce.

**EX 13.3**

```
db.estudantes.createIndex({ cidade: 1, nota: -1 });

db.estudantes.find({ cidade: "Brasília" }).sort({ nota: -1 });
```

Esse índice serve a consulta inteira, ele filtra por cidade e já entrega o resultado na ordem de nota, então nem precisa ordenar na memória. O detalhe que entendi aqui é o prefixo à esquerda: esse índice atende busca por cidade sozinho e por cidade mais nota, mas não atende busca só por nota. É igual uma lista ordenada por sobrenome e depois por nome, dá para achar todos os Silva e dá para achar Silva, João, mas não dá para achar todos os João sem varrer tudo. Por isso a ordem dos campos no índice é uma decisão de projeto.

**EX 13.4**

```
db.cursos.createIndex({ nome: 1 }, { unique: true });

db.cursos.insertOne({ nome: "Data Science", duracao: "8 meses", modalidade: "EAD" });
```

O insert falhou com E11000 duplicate key error e o documento não foi gravado. Quem barra é o servidor, no momento da escrita, não a aplicação, então é uma garantia de integridade de verdade e não só uma convenção. Dois detalhes que percebi: se já existe um índice normal no campo tem que apagar antes, porque não dá para converter um índice em único, e se a coleção já tiver valor repetido é a criação do índice que falha.

**EX 13.5** Não vale a pena criar índice em coleção pequena, porque varrer tudo acaba saindo mais barato do que consultar o índice e depois ir buscar os documentos, que é exatamente o caso desse laboratório com 8 documentos. Também não vale em campo de baixa cardinalidade, tipo um booleano ativo, porque o índice aponta para metade da base e não elimina quase nada, aí o planejador nem usa. Em coleção com muita escrita atrapalha, porque cada índice precisa ser atualizado em todo insert, update e delete, então cinco índices são cinco estruturas para manter a cada gravação. E não faz sentido indexar campo que nunca aparece em filtro, ordenação ou $lookup, porque só ocupa disco e memória sem devolver nada. Tem ainda o caso do índice redundante, que é quando eu já tenho { curso: 1, idade: -1 } e crio também { curso: 1 }, sendo que o composto já resolve a busca por curso sozinho.

## Como ficou no final

O banco dbNoSQLBD terminou com as coleções estudantes (8 documentos), cursos, professores, disciplinas, temp (vazia) e resultado, essa última gerada pelo $out.

Duas coisas do roteiro que me travaram e vale anotar. A primeira é que as Partes 7 e 8 usam db.estudantes, mas essa coleção só passa a existir depois do renameCollection da Parte 10, e como o MongoDB cria coleção sozinho isso não dá erro, só atualiza zero documento em silêncio. A segunda é que os comentários do enunciado usam #, que é comentário de shell do Linux. No mongosh e no playground é JavaScript, então o comentário é // e colar as linhas com # dá SyntaxError.
