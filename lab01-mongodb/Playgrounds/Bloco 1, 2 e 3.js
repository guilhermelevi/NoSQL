// =====================================================================
// BLOCO 1 — PARTES 1, 2 e 3: ambiente, conexão e navegação
// =====================================================================
//
// No terminal:
//   docker compose up -d
//   docker ps
//   docker exec -it mongodb-container mongosh -u admin -p 123456
//
// RESPOSTA EX 1.1 — Container "mongodb-container", porta 0.0.0.0:27017->27017/tcp.
//   O nome vem de container_name no docker-compose.yml. O mapeamento faz a porta
//   27017 do Mac encaminhar para a 27017 do container.
//
// RESPOSTA EX 1.2 — Com -d (detached) o container sobe em segundo plano e o terminal
//   é devolvido. Sem a flag, o log ocupa o terminal e Ctrl+C derruba o serviço.
//
// RESPOSTA EX 1.3 — Limpar ./data/mongodb_data/* garante ambiente idêntico ao de
//   todos e faz o entrypoint executar o init-mongo.js, que só roda com o dbpath
//   VAZIO. Com dados presentes o script é ignorado em silêncio e o usuário admin
//   não é criado. Aqui houve um terceiro motivo: arquivos WiredTiger de uma versão
//   não são lidos por outra, e a imagem foi trocada de 4.4 para 8.2.
//
// RESPOSTA EX 2.1 — Servidor 8.2.12 (mongosh 2.9.2).
//   NOTA DE AMBIENTE: o roteiro pede mongo:4.4, mas nem 4.4 nem 8.0 iniciam em
//   kernel Linux >= 6.19 (SERVER-121912), e o OrbStack usa kernel 7.0.14. A imagem
//   foi trocada para mongo:8.2, que já traz o patch e embarca o mongosh — por isso
//   a Parte 2 (instalação via apt) foi dispensada.
//
// RESPOSTA EX 2.2 — Sem a senha, o mongosh abre prompt oculto. Com a senha na URI a
//   conexão é imediata e não interativa: serve a scripts e CI, mas registra a senha
//   no histórico do shell e em logs. Em uso real, prefira o prompt.
//
// RESPOSTA EX 2.3 — admin, config e local. São bancos internos: admin guarda
//   usuários e permissões, config metadados de sharding e sessões, local o oplog.
//
// RESPOSTA EX 3.1 — dbExercicio NÃO aparece em show dbs. O use apenas aponta a
//   variável db para o nome; o MongoDB cria banco e coleção de forma preguiçosa,
//   só quando o primeiro documento é gravado.
//
// RESPOSTA EX 3.2 — use dbNoSQLBD          (mongosh)
//                   use('dbNoSQLBD');      (playground: é JavaScript puro, então os
//                                           atalhos do shell não existem)
//
// RESPOSTA EX 3.3 — db (sozinho) no mongosh, ou db.getName() no playground.
// =====================================================================

use('dbNoSQLBD');

db.version();
db.getName();


// =====================================================================
// BLOCO 2 — PARTE 4: criação de coleções
// =====================================================================
//
// RESPOSTA EX 4.1 — db.createCollection("professores");
// RESPOSTA EX 4.2 — db.createCollection("disciplinas");
// RESPOSTA EX 4.3 — show collections (mongosh) / db.getCollectionNames()
//   Resultado: alunos, cursos, disciplinas, professores.
//
// RESPOSTA EX 4.4 — NÃO exige. Um insertOne numa coleção inexistente a cria
//   automaticamente; o mesmo vale para o banco. O createCollection só é necessário
//   para definir opções na criação: validação de schema, coleção capped (tamanho
//   fixo, sobrescreve o mais antigo) ou time-series.
// =====================================================================

use('dbNoSQLBD');

db.createCollection("alunos");
db.createCollection("cursos");
db.createCollection("professores");   // EX 4.1
db.createCollection("disciplinas");   // EX 4.2

db.getCollectionNames();              // EX 4.3


// =====================================================================
// BLOCO 3 — PARTE 5: inserção de documentos
// =====================================================================
//
// RESPOSTA EX 5.4 — insertOne grava um documento e retorna insertedId; insertMany
//   recebe um array e retorna insertedIds. A diferença que pesa é desempenho:
//   insertMany envia o lote inteiro numa única ida ao servidor, enquanto n chamadas
//   de insertOne custam n viagens de rede. Por padrão insertMany é ordenado e para
//   no primeiro erro; com { ordered: false } segue inserindo os demais.
// =====================================================================

use('dbNoSQLBD');

db.alunos.insertMany([
    { nome: "Carlos Silva", idade: 22, curso: "Engenharia de Dados" },
    { nome: "Mariana Souza", idade: 25, curso: "Business Intelligence" },
    { nome: "Rafael Lima", idade: 21, curso: "Data Science" }
]);

// O campo nome daqui casa com o campo curso de alunos. Não existe chave estrangeira
// no MongoDB: essa ligação é convenção, e é ela que o $lookup da Parte 12 usa.
db.cursos.insertMany([
    { nome: "Engenharia de Dados", duracao: "6 meses", modalidade: "EAD" },
    { nome: "Business Intelligence", duracao: "4 meses", modalidade: "Presencial" },
    { nome: "Data Science", duracao: "8 meses", modalidade: "Híbrido" }
]);

db.alunos.insertOne({ nome: "Ana Costa", idade: 23, curso: "Engenharia de Dados" });

// RESPOSTA EX 5.1
db.professores.insertMany([
    { nome: "Raul Carvalho", especialidade: "Bancos NoSQL", anos_experiencia: 12 },
    { nome: "Helena Dias", especialidade: "Engenharia de Dados", anos_experiencia: 8 },
    { nome: "Marcos Prado", especialidade: "Machine Learning", anos_experiencia: 5 }
]);

// RESPOSTA EX 5.2 — carga_horaria é número e obrigatoria é booleano, não strings.
// "60" e 60 são valores distintos no BSON, e $gt só compara corretamente números.
db.disciplinas.insertMany([
    { nome: "Bancos de Dados Não Relacionais", carga_horaria: 60, obrigatoria: true },
    { nome: "Tópicos em Big Data", carga_horaria: 40, obrigatoria: false }
]);

// RESPOSTA EX 5.3 — este documento tem um campo (cidade) que nenhum outro tem, e o
// banco aceita: é a flexibilidade de schema. Consequência na Parte 10: ao agrupar
// por cidade, todos os documentos sem o campo caem num grupo _id: null.
db.alunos.insertOne({ nome: "Lucas Moreira", idade: 26, curso: "Data Science", cidade: "Brasília" });

db.alunos.countDocuments();   // esperado: 5
