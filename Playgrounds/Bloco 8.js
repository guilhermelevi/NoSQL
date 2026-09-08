// =====================================================================
// BLOCO 8 — PARTE 10: rename, ordenação, limite e agregação
// =====================================================================
//
// O renameCollection é a FRONTEIRA do laboratório: a partir daqui a coleção se chama
// estudantes, e todos os blocos seguintes usam esse nome. Ele preserva documentos e
// índices, muda só o nome no catálogo. Rodar o arquivo duas vezes dá erro, porque
// alunos já não existe — nesse caso, comente a linha e siga.
//
// RESPOSTA EX 10.1 — db.estudantes.find().sort({ idade: -1 })
//   Em sort, 1 é crescente e -1 decrescente.
//
// RESPOSTA EX 10.2 — db.estudantes.find().limit(3)
//
// RESPOSTA EX 10.3 — agrupamento por cidade. Rodado ANTES dos inserts da Parte 12,
//   o resultado traz _id: null com total 2 e _id: "Brasília" com total 1, porque só
//   Lucas Moreira tem o campo cidade. Documentos sem o campo agrupado caem todos em
//   null: não é erro, é como o $group trata campo ausente.
//
// RESPOSTA EX 10.4 — db.estudantes.find().sort({ idade: 1 }).limit(2)
//   A ordem do encadeamento na escrita não altera o resultado: o planejador sempre
//   ordena antes de cortar. Quando existe índice no campo ordenado, essa combinação
//   fica eficiente — o servidor percorre o índice já na ordem e para ao atingir o
//   limite, sem carregar e ordenar a coleção inteira em memória.
// =====================================================================

use('dbNoSQLBD');

// Parte 10 — renomeia alunos -> estudantes (roda UMA vez só)
db.alunos.renameCollection("estudantes");
console.log(db.getCollectionNames());

// tamanho total da coleção em bytes (dados + índices)
console.log("--- totalSize: " + db.estudantes.totalSize() + " ---");

console.log("--- idade > 22, ordenado por nome ---");
console.log(db.estudantes.find({ idade: { $gt: 22 } }).sort({ nome: 1 }).toArray());

console.log("--- primeiros 2 ---");
console.log(db.estudantes.find().limit(2).toArray());

// RESPOSTA EX 10.1 — idade decrescente
console.log("--- idade DESC ---");
console.log(db.estudantes.find().sort({ idade: -1 }).toArray());

// RESPOSTA EX 10.2 — três primeiros
console.log("--- 3 primeiros ---");
console.log(db.estudantes.find().limit(3).toArray());

// RESPOSTA EX 10.4 — os 2 mais novos: ordena crescente e corta
console.log("--- 2 mais novos ---");
console.log(db.estudantes.find().sort({ idade: 1 }).limit(2).toArray());

console.log("--- total por curso ---");
console.log(db.estudantes.aggregate([
    { $group: { _id: "$curso", total: { $sum: 1 } } }
]).toArray());

// RESPOSTA EX 10.3 — quantidade por cidade
db.estudantes.aggregate([
    { $group: { _id: "$cidade", total: { $sum: 1 } } }
]).toArray();
