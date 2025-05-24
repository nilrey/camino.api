#!/bin/bash

set -e  # Остановить выполнение при ошибке

echo "Обновление репозитория"
sudo git pull origin main

echo "Удаление текущего конейнера..."
sudo docker rm -f camino-back

echo "Удаление старого образа..."
sudo docker image rm idockerapi

echo "Пересборка образа..." 
sudo docker build -t idockerapi -f Dockerfile .

echo "Запуск контейнера..."
sudo docker compose -f docker-compose-back-vm1.yaml up --build -d

echo "Подключение к сети camino-net..."
sudo docker network connect camino-net camino-back

echo "Изменения внесены."
