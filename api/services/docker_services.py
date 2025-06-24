import docker
from docker.types import DeviceRequest
from docker.errors import NotFound, APIError
import socket
from datetime import datetime
from typing import List, Dict 
import api.settings.config as C
from docker.types import DeviceRequest
import requests
from  api.services.logger import LogManager
from docker.models.containers import Container as DockerContainer 
import time

logger = LogManager()


def get_vms_images() -> List[Dict]:
    logger.info("Поиск образов из списка ВМ")
    images_info = []
    vm = C.HOST_VM # берем только ВМ , где располагается репозиторий образов ИНС
    try:
        if is_host_reachable(vm['host']):
            client = docker.DockerClient(base_url=f"tcp://{vm['host']}:{vm['port']}")
            images = client.images.list()
            for image in images:
                image_tags = image.tags if image.tags else ["<none>:<none>"]
                for tag in image_tags:
                    if ":" in tag:
                        name, tag_part = tag.rsplit(":", 1)
                    else:
                        name, tag_part = tag, "<none>"
                    if name in C.BLOCK_LIST_IMAGES:
                        continue
                    location = 'registry'  if C.HOST_REGISTRY in name and vm["name"] else vm["name"]
                    images_info.append({
                        "id": image.id.replace("sha256:", ""),
                        "name": name,
                        "tag": tag_part,
                        "location": location,
                        "created_at": image.attrs.get("Created", ""),
                        "size": image.attrs.get("Size", 0),
                        "comment": image.attrs.get("Comment", ""),
                        "archive": ""
                    })
            client.close()
    except Exception as e:
        logger.error(f"Ошибка при подключении к {vm['name']} ({vm['host']}): {e}")
    return images_info

def find_image_by_id(image_id: str):
    logger.info("Поиск образа по id")
    try:
        images = get_vms_images()
        for image in images:
            # logger.info(f'{image.get("id")} {image_id}')
            if image.get("id") == image_id:
                logger.info(f"Image {image.get('id')} found on VM: {image.get('location')}")
                return image
    except Exception as e:
        logger.error(f"Ошибка при обработке списка образов из списка ВМ : {e}")
    return None


def get_vms_containers() -> List[Dict]:
    logger.info("Поиск конейнеров из списка ВМ")
    containers_info = []
    for vm in C.VIRTUAL_MACHINES_LIST:
        client = None
        try: 
            client = docker.DockerClient(base_url=f"tcp://{vm['host']}:{vm['port']}")
            containers = client.containers.list(all=True)
            for container in containers:
                if not container.attrs:
                    continue
                assert isinstance(container, DockerContainer) 
                if container.name in C.BLOCK_LIST_CONTAINERS:
                    continue

                command = container.attrs['Config']['Cmd']
                command_str = " ".join(command) if isinstance(command, list) else str(command)

                ports = container.attrs['NetworkSettings']['Ports']
                ports_str = ", ".join([
                    f"{container_port}" for container_port in ports.keys() if ports
                ]) if ports else ""

                status = get_uptime_string(container.attrs['Created']) if container.status == 'running' else container.status

                container_info = {
                    "id": container.id,
                    "host": vm['host'],
                    "image": {
                        "id": container.image.id.replace("sha256:", ""),
                        "name": container.image.tags[0].split(":")[0] if container.image.tags else "",
                        "tag": container.image.tags[0].split(":")[1] if container.image.tags else ""
                    },
                    "command": command_str,
                    "names": container.name,
                    "ports": ports_str,
                    "created_at": container.attrs['Created'],
                    "status": status
                }
                containers_info.append(container_info)
        except Exception as e:
            logger.error(f"Error connecting to {vm['host']}: {str(e)}")
        finally:
            if client:
                try:
                    client.close()
                except Exception as close_err:
                    logger.error(f"Ошибка при закрытии Docker клиента {vm['host']}: {close_err}")
        logger.info(f"Найдено {len(containers_info)}")
    return containers_info

def find_container_by_id(container_id: str, format_type: str = ''):
    logger.info("Поиск контейнера по id")
    try:
        if format_type == 'stats':
            containers = get_vms_containers_stats() 
        else:
            containers = get_vms_containers()

        for container in containers:
            logger.info(f'{container.get("id")} {container_id}')
            if container.get("id") == container_id:
                logger.info(f"Container {container_id} found on VM: {container.get('host')}")
                return container
    except Exception as e:
        logger.error(f"Ошибка в поиске контейнера: {e}")
    return None


def get_vms_containers_stats() -> List[Dict]:
    logger.info("Start get_docker_containers_stats")
    containers_info = []
    for vm in C.VIRTUAL_MACHINES_LIST:
        try: 
            client = docker.DockerClient(base_url=f"tcp://{vm['host']}:{vm['port']}")
            containers = client.containers.list(all=True)
            for container in containers:
                if not container.attrs:
                    continue
                assert isinstance(container, DockerContainer) 
                if container.name in C.BLOCK_LIST_CONTAINERS:
                    continue

                try:
                    # Получаем статус контейнера
                    state = container.status
                    cpu_percent = "0.00%"
                    mem_percent = "0.00%"
                    mem_use = "0B / 0B"

                    # Попытка получения stats (может не сработать для created/exited)
                    try:
                        stats = container.stats(stream=False)
                        cpu_stats = stats.get("cpu_stats", {})
                        precpu_stats = stats.get("precpu_stats", {})
                        memory_stats = stats.get("memory_stats", {})

                        cpu_total = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                        precpu_total = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
                        system_cpu = cpu_stats.get("system_cpu_usage", 0)
                        presystem_cpu = precpu_stats.get("system_cpu_usage", 0)

                        cpu_delta = cpu_total - precpu_total
                        system_delta = system_cpu - presystem_cpu

                        if system_delta > 0 and cpu_delta > 0:
                            num_cpus = len(cpu_stats.get("cpu_usage", {}).get("percpu_usage", [])) or 1
                            cpu_percent = f"{(cpu_delta / system_delta) * num_cpus * 100:.2f}%"

                        mem_usage = memory_stats.get("usage", 0)
                        mem_limit = memory_stats.get("limit", 1)
                        mem_percent = f"{(mem_usage / mem_limit) * 100:.2f}%"
                        mem_use = f"{mem_usage}B / {mem_limit}B"

                    except Exception:
                        logger.error(f"Stats not available for container {container.id} on {vm['host']}")

                    # Обновляем и получаем размер
                    container.reload()
                    size = container.attrs.get("SizeRootFs", 0)

                    containers_info.append({
                        "id": container.id,
                        "host": vm['host'],
                        "state": state,
                        "cpu": cpu_percent,
                        "mem": mem_percent,
                        "mem_use": mem_use,
                        "size": size
                    })

                except Exception as inner_e:
                    logger.error(f"Failed to get stats for container {container.id} on {vm['host']}: {str(inner_e)}")
        except Exception as e:
            logger.error(f"Error connecting to {vm['host']}: {str(e)}")
    logger.info(f"Найдено {len(containers_info)}")
    return containers_info

def create_start_container(params): 
    message = 'Before container create'
    vm_host, is_error = get_available_vm() 
    try:
        if is_error:
            message = f'Ошибка при просмотре списка VM: {vm_host}'
        elif vm_host:
            logger.info(f'params: {params}')
            client = docker.DockerClient(base_url=f'tcp://{vm_host}:2375', timeout=5) 
            image = find_image_by_id(params["image_id"])
            logger.info(f"Найден образ: {image}")

            if image:
                name = params["name"]
                command = [
                    "--input_data", params['hyper_params'],
                    "--host_web", C.HOST_ANN
                ]
                if params['ann_mode'] == 'teach':
                    command.append('--work_format_training')

                volumes = {
                    f'/family{params["video_storage"]}': {"bind": "/family/video", "mode": "rw"},
                    f'/family{params["out_dir"]}': {"bind": "/output", "mode": "rw"},
                    f'/family{params["in_dir"]}': {"bind": "/input_videos", "mode": "rw"},
                    f'/family{params["weights"]}': {"bind": "/weights/", "mode": "rw"},
                    f'/family{params["markups"]}': {"bind": "/input_data", "mode": "rw"},
                    "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"},
                    "/family/projects_data": {"bind": "/projects_data", "mode": "rw"}
                }

                # Формируем строку запуска для логирования
                volume_args = ' '.join([f'-v {host}:{opt["bind"]}:{opt["mode"]}' for host, opt in volumes.items()])
                command_str = f"docker create --gpus all --shm-size=20g {volume_args} {image} {' '.join(command)}"
                logger.info(f"{command_str}")

                device_requests = []
                if not C.DEBUG_MODE:
                    device_requests = [DeviceRequest(count=-1, capabilities=[['gpu']])]

                try:
                    container = client.containers.create(
                        image=image['name'],
                        name=name,
                        command=command,
                        tty=True,
                        stdin_open=True,
                        detach=True,
                        auto_remove=True,                 
                        shm_size="20g",                   
                        volumes=volumes,
                        device_requests=device_requests
                    )
                    logger.info(f'Контейнер успешно создан id: {container.id}')
                    message = container.id
                    # Отправить сообщение о создании с указанием хоста и container_id
                    url = f"{C.HOST_RESTAPI}/containers/{container.id}/on_start"
                    send = { 'host' : vm_host, 'dataset_id' : params['dataset_id']}
                    logger.info(f'Send post: Url: {url} , body: {send}')

                    response = requests.post(url, json = send)
                    
                    logger.info(f'response.json() = {response.json()}')
                    time.sleep(3) # таймаут на 3 сек. , для успешной записи в БД сообщения от restapi
                    container.start()
                    logger.info(f"Контейнер успешно запущен на '{vm_host}' id:{container.id}") 
                except Exception as e:
                    message = f"Ошибка запуска контейнера на '{vm_host}': {e}"
                    logger.error(message)

        else:
            message = 'Нет свободных VM.'
            logger.info(message)
    except Exception as e:
        message = f"Произошла непредвиденная ошибка: {e}"
        logger.error(message)
    
    return message

def start_container(container_id: str):
    is_error = True
    message = ""
    container_host = None
    try:
        container_info = find_container_by_id(container_id)
        if container_info :
            client = docker.DockerClient(base_url=f'tcp://{container_info["host"]}:2375', timeout=5) 
            container = client.containers.get(container_id)
            container_host = container_info.get("host", None)
            container.start() 
            message = f"Контейнер {container_id} успешно запущен."
            logger.info(message)
            is_error = False
        else:
            message = f"Контейнер с ID {container_id} не найден."
            logger.info(message)
    except APIError as e:
        message = f"Ошибка Docker API: {e.explanation}" 
        logger.error(message)
    except Exception as e:
        message = f"Произошла непредвиденная ошибка: {e}"
        logger.error(message)
    
    return [is_error, message, container_host]

def stop_container(container_id: str):
    is_error = True
    message = ""
    container_host = None
    try:
        container_info = find_container_by_id(container_id)
        if container_info :
            client = docker.DockerClient(base_url=f'tcp://{container_info["host"]}:2375', timeout=5) 
            container = client.containers.get(container_id)
            container_host = container_info.get("host", None)
            container.stop()  # Или container.kill() для жёсткой остановки
            message = f"Контейнер {container_id} успешно остановлен на {container_host}."
            logger.info(message)
            is_error = False
        else:
            message = f"Контейнер с ID {container_id} не найден."
            logger.info(message)
    except APIError as e:
        message = f"Ошибка Docker API: {e.explanation}" 
        logger.error(message)
    except Exception as e:
        message = f"Произошла непредвиденная ошибка: {e}"
        logger.exception(message)
    
    return [is_error, message, container_host]

def is_host_reachable(ip, port=2375, timeout=3):
    # проверяем если виртуальная машина доступна, дополнительно ставим таймаут на время ожидания 
    logger.info("Start is_host_reachable")
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False

def check_vm_containers(vm_host, ann_images) -> bool:
    """ на виртуальной машине vm_host ищем контейнер созданный из образа в списке ann_images.
    если найдено хоть одно название из ann_images, то выходим из цикла - данная машина занята (True)
    иначе - возвращаем False
    """
    logger.info("Start check_vm_containers")
    if not is_host_reachable(vm_host):
        logger.error(f"{vm_host} недоступен")
        return True  # превышен таймаут подключение считаем, что VM можно пропустить
        
    try:
        # Подключение к удаленному Docker Engine API
        url = f'tcp://{vm_host}:2375' 
        logger.info(f"Подключение к удаленной ВМ {url}")
        client = docker.DockerClient(base_url=url, timeout=5) 
        containers = client.containers.list() # all=True исключаем, ищем только запущенные 
        logger.info(f"{vm_host} containers: {containers}")

        has_ann_image = False

        for container in containers:
            image_tags = container.image.tags or [container.image.short_id]
            for tag in image_tags:
                for ann_image in ann_images:
                    if ann_image in tag:
                        has_ann_image = True
                        break
                if has_ann_image:
                    break   

        client.close()

        logger.info(f"{vm_host} search result: {has_ann_image}")
        return has_ann_image

    except Exception as e:
        logger.error(f'Ошибка при подключении к {vm_host}: {e}')
        # Возвращаем True, чтобы не останавливать перебор
        return True 
    

def get_available_vm():
    is_error = True
    try:
        if not C.VIRTUAL_MACHINES_LIST:
            message = 'Список виртуальных машин пуст.'
        elif not C.ANN_IMAGES_LIST:
            message = 'Список ИНС образов пуст.'
        else:
            logger.info(f"Спискок виртуальных машин {C.VIRTUAL_MACHINES_LIST}")
            for vm in C.VIRTUAL_MACHINES_LIST:
                logger.info(f"Проверка {vm['name']} [{vm['host']}]")
                has_ann_image = check_vm_containers(vm['host'], C.ANN_IMAGES_LIST)
                if not has_ann_image:
                    is_error = False
                    logger.info(f"VM {vm['host']} свободна.")
                    return vm['host'], is_error
            message = 'Все виртуальные машины заняты.'
    except Exception as e:
        message = f'Ошибка find_vm_without_ann_images: {e}'
        
    logger.error(message) if is_error else logger.info(message)

    return message , is_error


def get_uptime_string(created_at):
    # Преобразует время создания контейнера в строку формата 'Up X minutes' 
    created_datetime = datetime.strptime(created_at.split('.')[0], '%Y-%m-%dT%H:%M:%S')
    uptime = datetime.utcnow() - created_datetime
    total_seconds = int(uptime.total_seconds())
    
    if total_seconds < 60:
        return "Up less than a minute"
    
    minutes = total_seconds // 60
    
    if minutes < 60:
        return f"Up {minutes} minute{'s' if minutes != 1 else ''}"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours < 24:
        if remaining_minutes == 0:
            return f"Up {hours} hour{'s' if hours != 1 else ''}"
        return f"Up {hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"
    
    days = hours // 24
    remaining_hours = hours % 24
    
    if remaining_hours == 0:
        return f"Up {days} day{'s' if days != 1 else ''}"
    return f"Up {days} day{'s' if days != 1 else ''} {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"