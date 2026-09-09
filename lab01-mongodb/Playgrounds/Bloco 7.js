// =====================================================================
// BLOCO 7 — PARTE 9: formatação, estatísticas e índices
// =====================================================================
//
// RESPOSTA EX 9.1 — db.cursos.find().pretty()
//   O .pretty() existia para o shell antigo (mongo), que imprimia tudo numa linha só.
//   No mongosh atual e no playground a formatação já é automática: chamar o método
//   não dá erro, apenas não muda nada.
//
// RESPOSTA EX 9.2 — 3 documentos (Carlos, Ana e Lucas), após as remoções da Parte 8.
//   Existe também estimatedDocumentCount(), que lê metadados em vez de percorrer a
//   coleção: instantâneo em bases enormes, mas não aceita filtro e pode ficar
//   desatualizado após uma parada abrupta.
//
// RESPOSTA EX 9.3 — em cursos existe só o índice _id_, criado automaticamente em
//   toda coleção e impossível de remover: é ele que garante a unicidade da chave
//   primária. O nome do índice deriva do campo e da direção: { nome: 1 } vira
//   "nome_1" e { curso: 1, idade: -1 } vira "curso_1_idade_-1". É desse nome que o
//   dropIndex depende.
//
// RESPOSTA EX 9.4 — em db.stats(), collections é a quantidade de coleções do banco e
//   dataSize é a soma do tamanho dos documentos em bytes, o dado bruto, sem índices.
//   Dois vizinhos ajudam a ler: storageSize é o espaço realmente ocupado em disco,
//   normalmente MENOR que dataSize por causa da compressão do WiredTiger; indexSize
//   é o custo dos índices, que cresce a cada createIndex — a contrapartida concreta
//   do "índice acelera leitura mas custa espaço" da Parte 13.
// =====================================================================

use('dbNoSQLBD');

console.log("--- alunos ---");
console.log(db.alunos.find().toArray());

// RESPOSTA EX 9.1
console.log("--- cursos ---");
console.log(db.cursos.find().toArray());

// RESPOSTA EX 9.2
console.log("--- total de alunos: " + db.alunos.countDocuments() + " ---");

// RESPOSTA EX 9.3
console.log("--- indices de cursos ---");
console.log(db.cursos.getIndexes());

console.log("--- indices de alunos (antes) ---");
console.log(db.alunos.getIndexes());

db.alunos.createIndex({ nome: 1 });

console.log("--- indices de alunos (depois) ---");
console.log(db.alunos.getIndexes());

console.log("--- findOne ---");
console.log(db.alunos.findOne());

// RESPOSTA EX 9.4
db.stats();
