// =====================================================================
// BLOCO 10 (respostas) — PARTE 12: Aggregation Framework
// =====================================================================
//
// O pipeline é uma esteira: cada estágio recebe a saída do anterior. O $ antes do
// nome do campo ("$curso") significa "o valor deste campo"; sem o $, seria a string
// literal. O _id do $group é a chave de agrupamento, e _id: null agrupa tudo num
// resultado só.
//
// Ponto importante nos resultados: $avg IGNORA documentos sem o campo, em vez de
// tratá-los como zero. Por isso as médias de nota não são distorcidas por Carlos,
// Ana e Lucas, que não têm nota. Já $sum: 1 conta o documento independentemente dos
// campos que ele tenha.
//
// $lookup sempre devolve um ARRAY no campo "as", mesmo com um único match — por isso
// o $unwind, que transforma cada item num documento próprio e deixa o resultado com
// cara de JOIN. Cuidado: $unwind DESCARTA documentos cujo array veio vazio, salvo
// com preserveNullAndEmptyArrays: true.
//
// RESPOSTA EX 12.5 — $match ANTES do $group filtra documentos brutos e equivale ao
//   WHERE. É a posição preferível: reduz o volume que entra na agregação e pode usar
//   índice, algo impossível depois do agrupamento. $match DEPOIS do $group filtra os
//   resultados já agregados e equivale ao HAVING — só nessa posição dá para filtrar
//   por media_nota, campo que não existia antes. O pipeline 12.10 usa os dois.
//     WHERE:   { $match: { cidade: "Brasília" } }, { $group: {...} }
//     HAVING:  { $group: {...} }, { $match: { media_nota: { $gt: 8 } } }
// =====================================================================

use('dbNoSQLBD');

// RESPOSTA EX 12.1 — nota mínima por curso
console.log("--- EX 12.1: menor nota por curso ---");
console.log(db.estudantes.aggregate([
    { $group: { _id: "$curso", menor_nota: { $min: "$nota" } } }
]).toArray());

// RESPOSTA EX 12.2 — média de nota de São Paulo (resultado: 6.5, de Ricardo Mendes)
console.log("--- EX 12.2: media de Sao Paulo ---");
console.log(db.estudantes.aggregate([
    { $match: { cidade: "São Paulo" } },
    { $group: { _id: "$cidade", media_nota: { $avg: "$nota" } } }
]).toArray());

// RESPOSTA EX 12.3 — conceito A / B / C com $switch.
// A ordem dos branches é decisiva: o primeiro case verdadeiro vence e os demais nem
// são avaliados. Invertendo as linhas, a nota 9.7 cairia em "B". Quem não tem nota
// cai no default: "C".
console.log("--- EX 12.3: conceito ---");
console.log(db.estudantes.aggregate([
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
]).toArray());

// RESPOSTA EX 12.4 — total de estudantes e maior nota na mesma passada.
// O $facet executa vários pipelines independentes sobre a MESMA entrada.
db.estudantes.aggregate([
    { $facet: {
        total_estudantes: [ { $count: "total" } ],
        maior_nota: [ { $group: { _id: null, maximo: { $max: "$nota" } } } ]
    } }
]).toArray();


// ---------------------------------------------------------------------
// 12.6 com $out — materializa o resultado numa coleção.
// $out precisa ser o ÚLTIMO estágio e SUBSTITUI a coleção de destino inteira a cada
// execução: não acrescenta.
// ---------------------------------------------------------------------

use('dbNoSQLBD');

db.estudantes.aggregate([
    { $project: {
        nome: 1,
        curso: 1,
        nota: 1,
        aprovado: {
            $cond: { if: { $gte: ["$nota", 7] }, then: "Sim", else: "Não" }
        }
    } },
    { $out: "resultado" }
]);

db.resultado.find().toArray();
