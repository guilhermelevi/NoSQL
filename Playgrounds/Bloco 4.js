// =====================================================================
// BLOCO 4 — PARTE 6: consultas
// =====================================================================
//
// RESPOSTA EX 6.5 — equivalência com o SQL:
//   >   ->  $gt      (greater than)
//   <   ->  $lt      (less than)
//   >=  ->  $gte     (greater than or equal)
//   <=  ->  $lte     (less than or equal)
//   Completam a família: $ne (diferente), $in (está na lista), $nin (não está).
//
// RESPOSTA EX 6.4 (diferença find x findOne) — find() devolve um CURSOR, um ponteiro
//   que o servidor entrega em lotes, o que evita carregar milhões de documentos na
//   memória, e aceita encadear .sort(), .limit() e .skip(). findOne() devolve o
//   documento em si, já pronto, e por isso não aceita encadeamento.
//
// Obs.: o playground só mostra no painel o resultado da ÚLTIMA expressão. Por isso
// os console.log — eles imprimem na aba Output (Cmd+Shift+U). O .toArray() é
// necessário porque find() devolve cursor, e imprimir o cursor não mostra os dados.
// =====================================================================

use('dbNoSQLBD');

// Parte 6 — todos os documentos
console.log("--- alunos ---");
console.log(db.alunos.find().toArray());

console.log("--- cursos ---");
console.log(db.cursos.find().toArray());

// Parte 6 — filtro por comparação: idade > 22
console.log("--- idade > 22 ---");
console.log(db.alunos.find({ idade: { $gt: 22 } }).toArray());

// RESPOSTA EX 6.1 — todos os professores
console.log("--- professores ---");
console.log(db.professores.find().toArray());

// RESPOSTA EX 6.2 — idade menor ou igual a 22
console.log("--- idade <= 22 ---");
console.log(db.alunos.find({ idade: { $lte: 22 } }).toArray());

// RESPOSTA EX 6.3 — igualdade dispensa operador: basta campo: valor.
// A comparação é exata, sensível a maiúsculas e acentos.
console.log("--- curso = Engenharia de Dados ---");
console.log(db.alunos.find({ curso: "Engenharia de Dados" }).toArray());

// RESPOSTA EX 6.4 — um único documento, sem cursor
db.alunos.findOne();
