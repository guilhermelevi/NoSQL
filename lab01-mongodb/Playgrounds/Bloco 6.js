// =====================================================================
// BLOCO 6 — PARTE 8: remoção
// =====================================================================
//
// RESPOSTA EX 8.3 — deleteOne remove apenas o PRIMEIRO documento que casar com o
//   filtro, mesmo que vários casem. É a escolha para atingir um registro específico
//   e a mais segura: um filtro mal escrito destrói no máximo um documento.
//   deleteMany remove TODOS os que casarem, e serve a limpeza em lote.
//   Prática que evita acidente: rodar a condição num find() primeiro, conferir na
//   tela o que aparece, e só então trocar find por deleteMany. Fora de transação,
//   a remoção é irreversível.
//
// deleteMany({}) esvazia a coleção mas ela continua existindo, com seus índices.
// Quem elimina a coleção do catálogo é db.temp.drop().
// =====================================================================

use('dbNoSQLBD');

console.log("--- antes: " + db.alunos.countDocuments() + " alunos ---");

// Parte 8 — remove um documento
db.alunos.deleteOne({ nome: "Rafael Lima" });

// RESPOSTA EX 8.1 — remove Mariana Souza
db.alunos.deleteOne({ nome: "Mariana Souza" });

// RESPOSTA EX 8.2 — insere 3 em temp e apaga todos
db.temp.insertMany([
    { item: "A", valor: 1 },
    { item: "B", valor: 2 },
    { item: "C", valor: 3 }
]);
console.log("--- temp criada com " + db.temp.countDocuments() + " docs ---");

db.temp.deleteMany({});
console.log("--- temp apos deleteMany: " + db.temp.countDocuments() + " docs ---");

// a coleção continua existindo, mesmo vazia
console.log(db.getCollectionNames());

// estado final: 3 alunos (Carlos, Ana e Lucas)
db.alunos.find().toArray();
