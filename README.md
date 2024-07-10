#Docker run image and container
docker build -t idockerapi .
docker run -d --rm --name cdockerapi -p 8002:80 -v //var/run/docker.sock:/var/run/docker.sock idockerapi

# camino.api
python api of web stage  

## sqlacodegen
sqlacodegen postgresql://postgres:postgres@127.0.0.1:5432/camino_db1  --outfile sqlmodels.py --schema common 