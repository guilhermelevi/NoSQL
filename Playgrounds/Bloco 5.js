// =====================================================================
// BLOCO 5 — PARTE 7: atualizações
// =====================================================================
//
// ATENÇÃO: o roteiro usa db.estudantes aqui, mas essa coleção só passa a existir na
// Parte 10, com o renameCollection. Rodar como está no PDF não dá erro — o MongoDB
// cria uma coleção "estudantes" vazia e atualiza ZERO documentos, em silêncio, o que
// é pior que um erro. Por isso os comandos abaixo usam db.alunos.
//
// RESPOSTA EX 7.4 — $set cria o campo se não existir e sobrescreve se existir.
//   $unset remove a chave do documento. Não é o mesmo que gravar null: depois do
//   $unset o campo deixa de existir e é encontrado por { email: { $exists: false } },
//   enquanto null continuaria existindo como campo de valor nulo.
//   O $set é obrigatório: sem ele, updateOne({nome:"Ana Costa"}, {idade:24})
//   SUBSTITUIRIA o documento inteiro, apagando nome e curso.
//
// O retorno de cada update traz matchedCount (quantos casaram com o filtro) e
// modifiedCount (quantos realmente mudaram). Divergem quando o valor novo é igual
// ao antigo. Nos updateMany abaixo, espere matchedCount: 5.
// =====================================================================

use('dbNoSQLBD');

// Parte 7 — atualiza um documento específico
db.alunos.updateOne(
    { nome: "Carlos Silva" },
    { $set: { idade: 23 } }
);

// RESPOSTA EX 7.1 — Ana Costa para 24
db.alunos.updateOne(
    { nome: "Ana Costa" },
    { $set: { idade: 24 } }
);

// RESPOSTA EX 7.2 — o filtro {} atinge TODOS os documentos
db.alunos.updateMany(
    {},
    { $set: { email: "sem_email@labmongo.com" } }
);

console.log("--- com o campo email ---");
console.log(db.alunos.find().toArray());

// RESPOSTA EX 7.3 — o valor "" é ignorado pelo $unset, só a chave importa
db.alunos.updateMany(
    {},
    { $unset: { email: "" } }
);

db.alunos.find().toArray();
