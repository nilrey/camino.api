import docker

class DockerManager:
    def __init__(self):
        # Подключение к Docker
        self.client = docker.from_env()

    def list_containers(self, all_containers=False):
        """
        Получить список контейнеров.
        :param all_containers: True — все, False — только запущенные
        :return: список словарей с информацией о контейнерах
        """
        containers = self.client.containers.list(all=all_containers)
        container_list = []

        for container in containers:
            container_info = {
                "name": container.name,
                "id": container.short_id,
                "status": container.status,
                "image": container.image.tags,
                "ports": container.attrs['NetworkSettings']['Ports']
            }
            container_list.append(container_info)

        return container_list

    def print_containers(self, all_containers=False):
        """
        Печать информации о контейнерах
        """
        containers = self.list_containers(all_containers)
        for c in containers:
            print(f"Имя: {c['name']}, ID: {c['id']}, Статус: {c['status']}, "
                  f"Образ: {c['image']}, Порты: {c['ports']}")

    def start_container(self, container_name):
        """
        Запуск контейнера по имени или ID
        """
        try:
            container = self.client.containers.get(container_name)
            container.start()
            print(f"Контейнер '{container.name}' запущен.")
        except docker.errors.NotFound:
            print(f"Контейнер '{container_name}' не найден.")
        except Exception as e:
            print(f"Ошибка запуска: {e}")

    def stop_container(self, container_name):
        """
        Остановка контейнера по имени или ID
        """
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            print(f"Контейнер '{container.name}' остановлен.")
        except docker.errors.NotFound:
            print(f"Контейнер '{container_name}' не найден.")
        except Exception as e:
            print(f"Ошибка остановки: {e}")

    def remove_container(self, container_name):
        """
        Удаление контейнера по имени или ID
        """
        try:
            container = self.client.containers.get(container_name)
            container.remove(force=True)
            print(f"Контейнер '{container.name}' удалён.")
        except docker.errors.NotFound:
            print(f"Контейнер '{container_name}' не найден.")
        except Exception as e:
            print(f"Ошибка удаления: {e}")

    def get_logs(self, container_name):
        """
        Получение логов контейнера
        """
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs().decode('utf-8')
            print(f"Логи контейнера '{container.name}':\n{logs}")
        except docker.errors.NotFound:
            print(f"Контейнер '{container_name}' не найден.")
        except Exception as e:
            print(f"Ошибка получения логов: {e}")
