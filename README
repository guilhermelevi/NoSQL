#primeiro up
$sudo docker compose down && sudo docker compose build --no-cache && sudo docker compose up -d

//to SSH into the container
docker exec -it mongodb_contaner bash

mongod --version

//Check admin db connection is working or not
mongosh admin -u root -p

// check default database with newly created by init-mongo.js
show dbs