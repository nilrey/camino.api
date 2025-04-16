# Docker run image and container
docker build -t idockerapi .
docker run -d --rm --name cdockerapi -p 8002:80 -v //var/run/docker.sock:/var/run/docker.sock idockerapi

# camino.api
python api of web stage  

## sqlacodegen
sqlacodegen postgresql://postgres:postgres@127.0.0.1:5432/camino_db1  --outfile sqlmodels.py --schema common 

# Рабочая директория: /home/ubuntu/Documents/trackers-inevm (в ней лежит Dockerfile)

# Создание образа (из рабочей директории)
    sudo docker build -t bytetracker-image .

# Формат старта контейнера:
    sudo docker run --rm -v $(pwd)/bytetracker/bytetracker_markup:/output -v /home/ubuntu/Desktop/citms:/input -it --name bytetracker bytetracker-image --input_data '{"datasets":[{"dataset_name": "video"}]}'

# в каталоге /home/ubuntu/Desktop/citms находится датасет метро video. в json строке input_data я указываю название этого датасета


http://10.0.0.1/index.php?r=teach%2Fupdate&id=4e0e4e28-0f0e-11f0-b6ef-0242ac140002&dataset_id=c25120b2-0f0e-11f0-9333-0242ac140002