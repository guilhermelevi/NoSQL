db = db.getSiblingDB("admin");

db.createUser({
    user: "admin",
    pwd: "123456",
    roles: [{ role: "root", db: "admin" }]
});

db = db.getSiblingDB("dbtopicosBD");

db.createCollection("alunos");

db.alunos.insertOne({ nome: "Carlos Silva", idade: 22, curso: "Engenharia de Dados" });

print("Banco de dados inicializado com sucesso!");
