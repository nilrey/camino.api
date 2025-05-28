import os
import docker
from docker.types import DeviceRequest
from docker.errors import NotFound, APIError
import socket
from datetime import datetime
from typing import List, Dict
from docker.errors import NotFound, APIError
import api.sets.config as C
from docker.types import DeviceRequest
import requests
from  api.format.logger import logger
from docker.models.containers import Container as DockerContainer 
import time


def get_docker_images() -> List[Dict]:
    logger.info("Start get_docker_images")
    images_info = []
    vm = C.HOST_VM # берем только ВМ , где располагается репозиторий образов ИНС
    # for vm in C.VIRTUAL_MACHINES_LIST:
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
    logger.info("Start find_image_by_id")
    try:
        images = get_docker_images()
        for image in images:
            # logger.info(f'{image.get("id")} {image_id}')
            if image.get("id") == image_id:
                logger.info(f"Image {image.get('id')} found on VM: {image.get('location')}")
                return image
    except Exception as e:
        logger.error(f"Ошибка при обработке списка образов из списка ВМ : {e}")
    return None


def get_docker_containers() -> List[Dict]:
    logger.info("Start get_docker_containers")
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

                command = container.attrs['Config']['Cmd']
                command_str = " ".join(command) if isinstance(command, list) else str(command)

                ports = container.attrs['NetworkSettings']['Ports']
                ports_str = ", ".join([
                    f"{container_port}" for container_port in ports.keys() if ports
                ]) if ports else ""

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
                    "status": container.attrs['State'].get('Status', '') # container.status
                }
                containers_info.append(container_info)
        except Exception as e:
            logger.error(f"Error connecting to {vm['host']}: {str(e)}")
    logger.info(f"Найдено {len(containers_info)}")
    return containers_info

def find_container_by_id(container_id: str):
    try:
        containers = get_docker_containers()
        for container in containers:
            logger.info(f'{container.get("id")} {container_id}')
            if container.get("id") == container_id:
                logger.info(f"Container {container_id} found on VM: {container.get('host')}")
                return container
    except Exception as e:
        logger.error(f"Ошибка в поиске контейнера: {e}")
    return None

# def run_container(params): 
#     logger.info("Start run_container")
#     vm_host, is_error = get_available_vm() 
#     container_id = None
#     if is_error:
#         message = f'Ошибка при просмотре списка VM: {vm_host}'
#     elif vm_host:
#         logger.info(f'params: {params}')
#         client = docker.DockerClient(base_url=f'tcp://{vm_host}:2375', timeout=5) 
#         image_info = find_image_by_id(params["image_id"]) 
#         logger.info(f'image_info: {image_info}')
#         if image_info.get('name', False) :
#             logger.info(f'Формирование запроса')
#             name = params["name"]
#             command = [
#                 "--input_data", params['hyper_params'],
#                 "--host_web", C.HOST_ANN
#             ]
#             command.append('--work_format_training') if params['ann_mode'] == 'teach' else None

#             volumes = {
#                 f'/family{params["video_storage"]}': {"bind": "/family/video", "mode": "rw"},
#                 f'/family{params["out_dir"]}': {"bind": "/output", "mode": "rw"},
#                 f'/family{params["in_dir"]}': {"bind": "/input_videos", "mode": "rw"},
#                 f'/family{params["weights"]}': {"bind": "/weights/", "mode": "rw"},
#                 f'/family{params["markups"]}': {"bind": "/input_data", "mode": "rw"},
#                 "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"},
#                 "/family/projects_data": {"bind": "/projects_data", "mode": "rw"}
#             }

#             # Формируем строку запуска для лога
#             volume_args = ' '.join([f'-v {host}:{opt["bind"]}:{opt["mode"]}' for host, opt in volumes.items()])
#             command_str = f"docker run --gpus all --shm-size=20g --name {name} {volume_args} {image_info.get('name')} {' '.join(command)}"
#             logger.info(f"{command_str}")

#             # Используем device_requests для GPU
#             device_requests = []
#             if not C.DEBUG_MODE:
#                 device_requests = [
#                     DeviceRequest(count=-1, capabilities=[['gpu']])
#                 ]

#             # Запуск контейнера
#             logger.info(f'Container run command')
#             container = client.containers.run(
#                 image=image_info.get('name'),
#                 name=name,
#                 command=command,
#                 device_requests=device_requests,
#                 shm_size="20g",
#                 volumes=volumes,
#                 remove=True,
#                 detach=True,
#                 tty=True
#             )

#             logger.info(f'Контейнер запущен на: {vm_host}')
#             message = container.id
#             container_id = container.id
#     else:
#         message = 'Error: Нет свободных VM.'
#         logger.info(message)
    
#     if not params['dataset_id']:
#         params['dataset_id'] = "empty_dataset_id"

#     # Отправить сообщение о запуске с указанием хоста и container_id 
#     if container_id:
#         url = f"{C.HOST_RESTAPI}/containers/{container_id}/on_start"
#     else:
#         url = f"{C.HOST_RESTAPI}/containers/{container_id}/on_error"
    
#     response = { 'host' : vm_host, 'dataset_id' : params['dataset_id']}
#     logger.info(f'Send post: Url: {url} , body: {response}')

#     requests.post(url, json = response)
    
#     return {"error": is_error, "container_id" : container_id}


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
            command_str = f"docker run --gpus all --shm-size=20g --name {name} {volume_args} {image} {' '.join(command)}"
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
                    # auto_remove=True,                 
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
                logger.info(f'Контейнер успешно запущен, host:{vm_host} id:{container.id}') 
            except Exception as e:
                logger.error(f"Ошибка запуска контейнера host: {vm_host} : {e}")

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
            message = f"Контейнер {container_id} успешно остановлен."
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
    """ проверяем если вирт. машина доступна, доп. ставим таймаут 
    """
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