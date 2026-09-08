use('dbNoSQLBD');

// 12.1 — estudantes com nota e cidade, para permitir análise estatística
db.estudantes.insertMany([
    { nome: "Bruno Alves", idade: 28, curso: "Data Science", nota: 8.5, cidade: "Brasília" },
    { nome: "Fernanda Rocha", idade: 30, curso: "Business Intelligence", nota: 9.2, cidade: "Goiânia" },
    { nome: "Juliana Martins", idade: 27, curso: "Engenharia de Dados", nota: 7.8, cidade: "Brasília" },
    { nome: "Ricardo Mendes", idade: 35, curso: "Data Science", nota: 6.5, cidade: "São Paulo" },
    { nome: "Patrícia Lima", idade: 29, curso: "Engenharia de Dados", nota: 9.7, cidade: "Brasília" }
]);

db.estudantes.countDocuments();


use('dbNoSQLBD');

// 12.2 — contagem por curso  (GROUP BY curso)
console.log("--- total por curso ---");
console.log(db.estudantes.aggregate([
    { $group: { _id: "$curso", total_alunos: { $sum: 1 } } }
]).toArray());

// 12.3 — média de idade por curso
console.log("--- media de idade por curso ---");
console.log(db.estudantes.aggregate([
    { $group: { _id: "$curso", media_idade: { $avg: "$idade" } } }
]).toArray());

// 12.4 — média de nota, da maior para a menor
console.log("--- media de nota por curso (DESC) ---");
console.log(db.estudantes.aggregate([
    { $group: { _id: "$curso", media_nota: { $avg: "$nota" } } },
    { $sort: { media_nota: -1 } }
]).toArray());

// 12.5 — $match antes do $group = WHERE
console.log("--- alunos de Brasilia por curso ---");
console.log(db.estudantes.aggregate([
    { $match: { cidade: "Brasília" } },
    { $group: { _id: "$curso", total_brasilia: { $sum: 1 } } }
]).toArray());

// 12.6 — $project cria campo calculado
console.log("--- aprovado sim/nao ---");
console.log(db.estudantes.aggregate([
    { $project: {
        nome: 1,
        curso: 1,
        nota: 1,
        aprovado: {
            $cond: { if: { $gte: ["$nota", 7] }, then: "Sim", else: "Não" }
        }
    } }
]).toArray());

// 12.7 — $lookup = LEFT JOIN
console.log("--- lookup com cursos ---");
console.log(db.estudantes.aggregate([
    { $lookup: {
        from: "cursos",
        localField: "curso",
        foreignField: "nome",
        as: "dados_curso"
    } }
]).toArray());

// 12.8 — $unwind achata o array do lookup
console.log("--- lookup + unwind ---");
console.log(db.estudantes.aggregate([
    { $lookup: { from: "cursos", localField: "curso", foreignField: "nome", as: "curso_info" } },
    { $unwind: "$curso_info" },
    { $project: {
        nome: 1,
        curso: 1,
        modalidade: "$curso_info.modalidade",
        duracao: "$curso_info.duracao"
    } }
]).toArray());

// 12.9 — maior nota por curso
console.log("--- maior nota por curso ---");
console.log(db.estudantes.aggregate([
    { $group: { _id: "$curso", maior_nota: { $max: "$nota" } } }
]).toArray());

// 12.10 — WHERE + GROUP BY + HAVING + ORDER BY
console.log("--- pipeline completo ---");
console.log(db.estudantes.aggregate([
    { $match: { cidade: "Brasília" } },
    { $group: { _id: "$curso", media_nota: { $avg: "$nota" } } },
    { $match: { media_nota: { $gt: 8 } } },
    { $sort: { media_nota: -1 } }
]).toArray());

// 12.11 — $facet: duas agregações na mesma passada
db.estudantes.aggregate([
    { $facet: {
        total_alunos: [ { $count: "total" } ],
        media_geral: [ { $group: { _id: null, media: { $avg: "$nota" } } } ]
    } }
]).toArray();
