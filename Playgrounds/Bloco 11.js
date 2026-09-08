// =====================================================================
// BLOCO 11 — PARTE 13: indexação
// =====================================================================
//
// A ORDEM IMPORTA: para provar o efeito do índice é preciso medir ANTES de criá-lo.
// Por isso o arquivo está dividido em quatro etapas — rode uma de cada vez, com
// "Run Selected Playground Blocks", incluindo sempre a linha do use().
//
// COLLSCAN é collection scan: o MongoDB leu todos os documentos, um a um. IXSCAN
// significa que ele consultou o índice antes. Com poucos documentos a diferença de
// TEMPO é irrelevante e pode até piorar — o que prova o ponto é totalDocsExamined
// cair e totalKeysExamined aparecer.
//
// RESPOSTA EX 13.2 — stage ANTES do índice em cidade: COLLSCAN, com
//   totalDocsExamined: 8 e totalKeysExamined: 0. DEPOIS: FETCH com um IXSCAN
//   aninhado, e totalKeysExamined deixa de ser zero. São dois estágios porque o
//   índice guarda só o campo indexado e o endereço do documento: o IXSCAN acha as
//   chaves, o FETCH busca os documentos completos em disco. O que mudou de verdade é
//   totalDocsExamined, que cai de 8 para o número de documentos que interessam — é
//   esse número que escala.
//
// RESPOSTA EX 13.5 — quando NÃO criar índices:
//   1) Coleções pequenas, onde varrer tudo já é mais barato que consultar o índice e
//      depois buscar os documentos — exatamente o caso deste laboratório.
//   2) Campos de baixa cardinalidade, como um booleano ativo: o índice aponta para
//      metade da base, não elimina candidatos e o planejador tende a ignorá-lo.
//   3) Coleções com escrita intensa, já que cada índice é atualizado a cada insert,
//      update e delete. Cinco índices = cinco estruturas a manter em toda escrita.
//   4) Campos que nunca aparecem em filtro, ordenação ou $lookup: só ocupam disco e
//      memória sem retorno.
//   5) Índices redundantes: tendo { curso: 1, idade: -1 }, criar também { curso: 1 }
//      é desperdício, porque o composto já atende buscas por curso sozinho.
// =====================================================================


// ---------------------------------------------------------------------
// 13a — MEDIR SEM ÍNDICE (rodar primeiro)
// ---------------------------------------------------------------------

use('dbNoSQLBD');

db.estudantes.dropIndexes();

// EX 13.2 — stage ANTES de indexar cidade: anote stage, totalDocsExamined e
// totalKeysExamined
console.log("--- busca por cidade, SEM indice ---");
console.log(db.estudantes.find({ cidade: "Brasília" }).explain("executionStats").executionStats);

// 13.10 passo 2 — busca por idade, sem índice
db.estudantes.find({ idade: { $gt: 22 } }).explain("executionStats").executionStats;


// ---------------------------------------------------------------------
// 13b — CRIAR OS ÍNDICES E MEDIR DE NOVO
// ---------------------------------------------------------------------

use('dbNoSQLBD');

db.estudantes.createIndex({ nome: 1 });
db.estudantes.createIndex({ idade: 1 });

// 13.5 — campos usados no $lookup
db.estudantes.createIndex({ curso: 1 });
db.cursos.createIndex({ nome: 1 });

// RESPOSTA EX 13.1 — índice em cidade + verificação
db.estudantes.createIndex({ cidade: 1 });
console.log("--- indices de estudantes ---");
console.log(db.estudantes.getIndexes());

// EX 13.2 — stage DEPOIS de indexar cidade
console.log("--- busca por cidade, COM indice ---");
console.log(db.estudantes.find({ cidade: "Brasília" }).explain("executionStats").executionStats);

// 13.10 passo 4 — busca por idade, agora com índice
db.estudantes.find({ idade: { $gt: 22 } }).explain("executionStats").executionStats;


// ---------------------------------------------------------------------
// 13c — ÍNDICE COMPOSTO E ÍNDICE ÚNICO
//
// Prefixo à esquerda: { curso: 1, idade: -1 } atende buscas por curso sozinho e por
// curso + idade, mas NÃO por idade sozinho. É como uma lista ordenada por sobrenome
// e depois nome: dá para achar todos os "Silva" e "Silva, João", mas não todos os
// "João" sem varrer tudo. A ordem dos campos é decisão de projeto.
// ---------------------------------------------------------------------

use('dbNoSQLBD');

// 13.6 — índice composto
db.estudantes.createIndex({ curso: 1, idade: -1 });
console.log(db.estudantes.find({ curso: "Data Science" }).sort({ idade: -1 }).toArray());

// RESPOSTA EX 13.3 — composto cidade + nota, e a consulta que se beneficia dele:
// filtra por cidade e já entrega na ordem de nota, dispensando ordenação em memória
db.estudantes.createIndex({ cidade: 1, nota: -1 });
console.log(db.estudantes.find({ cidade: "Brasília" }).sort({ nota: -1 }).toArray());

// 13.7 — gera o e-mail a partir do nome. Repare nos COLCHETES em volta do $set: isso
// é um update com pipeline de agregação, e é o que permite calcular o novo valor a
// partir de outro campo do próprio documento. Um $set comum só aceita valores fixos.
db.estudantes.updateMany(
    {},
    [ { $set: { email: { $concat: [
        { $replaceAll: { input: { $toLower: "$nome" }, find: " ", replacement: "." } },
        "@labmongo.com"
    ] } } } ]
);
console.log(db.estudantes.find({}, { nome: 1, email: 1 }).toArray());

db.estudantes.createIndex({ email: 1 }, { unique: true });

// RESPOSTA EX 13.4 — índice único em cursos.nome.
// O dropIndex antes é necessário porque o índice não-único já existe do 13b: não dá
// para converter um índice em único, é preciso remover e recriar. Se a coleção já
// tivesse duplicatas, a CRIAÇÃO do índice é que falharia.
db.cursos.dropIndex("nome_1");
db.cursos.createIndex({ nome: 1 }, { unique: true });

// Isto FALHA com E11000 duplicate key error collection: dbNoSQLBD.cursos
// index: nome_1 dup key: { nome: "Data Science" } — e o documento não é gravado.
// A restrição é aplicada pelo servidor no momento da escrita, não pela aplicação.
db.cursos.insertOne({ nome: "Data Science", duracao: "8 meses", modalidade: "EAD" });


// ---------------------------------------------------------------------
// 13d — REMOÇÃO DE ÍNDICES (rodar por último)
//
// O nome do índice deriva do campo e da direção: { nome: 1 } vira "nome_1" e
// { curso: 1, idade: -1 } vira "curso_1_idade_-1". Por isso o getIndexes() antes.
// dropIndexes() remove todos menos o _id_, que é permanente — inclusive o índice
// único de email.
// ---------------------------------------------------------------------

use('dbNoSQLBD');

console.log(db.estudantes.getIndexes());

db.estudantes.dropIndex("nome_1");
db.estudantes.dropIndexes();

db.estudantes.getIndexes();
