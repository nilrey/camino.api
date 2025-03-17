#!/bin/bash

set -e  # Остановить выполнение при ошибке

echo "Обновление репозитория"
sudo git pull origin main

echo "Остановка и удаление контейнеров..."
cd ../../
sudo docker compose down

echo "Удаление старого образа..."
# sudo docker rm -f camino-back
sudo docker image rm idockerapi

echo "Пересборка образа..."
cd back/camino.api
sudo docker build -t idockerapi -f Dockerfile .

echo "Запуск контейнеров..."
cd ../../
sudo docker compose up --build -d

echo "Изменения внесены."
