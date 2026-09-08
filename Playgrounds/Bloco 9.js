// =====================================================================
// BLOCO 9 — PARTE 11: controle de usuários
// =====================================================================
//
// O usuário é criado NO BANCO EM QUE VOCÊ ESTÁ, e esse banco vira o authSource dele,
// o lugar onde o servidor procura as credenciais ao autenticar. É por isso que a
// conexão do admin, criado no banco admin, exige ?authSource=admin.
// Rodar duas vezes dá "User already exists"; para refazer, db.dropUser("novo_user").
// A senha não é armazenada em texto: o servidor guarda só o hash SCRAM-SHA-256.
//
// RESPOSTA EX 11.2 — no terminal:
//   docker exec -it mongodb-container mongosh "mongodb://leitura_user:senha123@localhost:27017/dbNoSQLBD"
//   db.estudantes.find()                        -> funciona
//   db.estudantes.insertOne({ nome: "Teste" })  -> falha
//   Erro: MongoServerError: not authorized on dbNoSQLBD to execute command insert
//   A role read concede apenas comandos de leitura, e a autorização é verificada NO
//   SERVIDOR, A CADA OPERAÇÃO — não no momento da conexão. Conectar com sucesso não
//   significa poder fazer tudo: o usuário entra normalmente e só descobre o limite
//   ao tentar escrever.
//
// RESPOSTA EX 11.3 — read x readWrite:
//   find, count, aggregate                    -> read: sim   | readWrite: sim
//   insert, update, delete                    -> read: não   | readWrite: sim
//   createCollection, createIndex, drop       -> read: não   | readWrite: sim
//   Nenhuma das duas permite criar usuários, alterar permissões ou acessar outros
//   bancos: isso exige roles administrativas como dbAdmin, userAdmin ou root, que é
//   a do admin do container. O princípio é o do menor privilégio — um serviço que só
//   gera relatório recebe read, e assim um bug ou credencial vazada não apaga dados.
// =====================================================================

use('dbNoSQLBD');

// Parte 11 — usuário com leitura e escrita
db.createUser({
    user: "novo_user",
    pwd: "senha123",
    roles: [ { role: "readWrite", db: "dbNoSQLBD" } ]
});

// RESPOSTA EX 11.1 — usuário somente leitura
db.createUser({
    user: "leitura_user",
    pwd: "senha123",
    roles: [ { role: "read", db: "dbNoSQLBD" } ]
});

db.getUsers();
