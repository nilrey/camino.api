# Остановка и удаление контейнеров
echo "Stopping and removing containers..."
cd ../../
sudo docker compose down

# Удаление старого образа
echo "Removing old Docker image..."
sudo docker image rm idockerapi

# Пересборка образа
echo "Building new Docker image..."
cd back/camino.api
sudo docker build -t idockerapi -f Dockerfile .

# Запуск контейнеров
echo "Starting containers..."
cd ../../
sudo docker compose up --build -d

echo "Update completed successfully!"