import os
from datetime import datetime
import socket
import docker
import logging
from docker.errors import NotFound, APIError
import api.sets.const as C
from docker.types import DeviceRequest
from typing import List, Dict
import requests
from  api.format.logger import logger

# client = docker.DockerClient(base_url=f'tcp://{C.VIRTUAL_MACHINES_LIST[0]["host"]}:2375')

# def list_images(): 
#     return client.images()

# def list_containers(all=True): 
#     return client.containers(all=all)


def get_docker_images() -> List[Dict]:
    logger.info("Start get_docker_images")
    images_info = []
    for vm in C.VIRTUAL_MACHINES_LIST:
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
                        
                        images_info.append({
                            "id": image.id.replace("sha256:", ""),
                            "name": name,
                            "tag": tag_part,
                            "location": vm["name"],
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
            logger.info(f'{image.get("id")} {image_id}')
            if image.get("id") == image_id:
                logger.info(f"Image {image.get('id')} found on VM: {image.get('location')}")
                return image
    except Exception as e:
        logger.error(f"Error retrieving images from VM {image.get('location')}: {e}")
    return None

def run_container(params): 
    logger.info("Start run_container")
    vm_ip, is_error = find_vm_without_ann_images() 
    container_id = None
    if is_error:
        message = f'Ошибка при просмотре списка VM: {vm_ip}'
    elif vm_ip:
        logger.info(f'params: {params}')
        client = docker.DockerClient(base_url=f'tcp://{vm_ip}:2375', timeout=5) 
        image_info = find_image_by_id(params["image_id"]) 
        logger.info(f'image_info: {image_info}')
        if image_info.get('name', False) :
            logger.info(f'Формирование запроса')
            name = params["name"]
            command = [
                # "--input_data", params['hyper_params'],
                "--host_web", C.HOST_ANN
            ]
            command.append('--work_format_training') if params['ann_mode'] == 'teach' else None

            volumes = {
                f'/family{params["video_storage"]}': {"bind": "/family/video", "mode": "rw"},
                f'/family{params["out_dir"]}': {"bind": "/output", "mode": "rw"},
                f'/family{params["in_dir"]}': {"bind": "/input_videos", "mode": "rw"},
                f'/family{params["weights"]}': {"bind": "/weights/", "mode": "rw"},
                f'/family{params["markups"]}': {"bind": "/input_data", "mode": "rw"},
                "/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "rw"},
                "/family/projects_data": {"bind": "/projects_data", "mode": "rw"}
            }

            # Формируем строку запуска для лога
            volume_args = ' '.join([f'-v {host}:{opt["bind"]}:{opt["mode"]}' for host, opt in volumes.items()])
            command_str = f"docker run --gpus all --shm-size=20g --name {name} {volume_args} {image_info.get('name')} {' '.join(command)}"
            logger.info(f"{command_str}")

            # Используем device_requests для GPU
            device_requests = []
            if not C.DEBUG_MODE:
                device_requests = [
                    DeviceRequest(count=-1, capabilities=[['gpu']])
                ]

            # Запуск контейнера
            logger.info(f'Container run command')
            container = client.containers.run(
                image=image_info.get('name'),
                name=name,
                command=command,
                device_requests=device_requests,
                shm_size="20g",
                volumes=volumes,
                # remove=True,
                detach=True,
                tty=True
            )

            logger.info(f'Контейнер запущен на: {vm_ip}')
            message = container.id
            container_id = container.id
    else:
        message = 'Error: Нет свободных VM.'
        logger.info(message)
    
    if not params['dataset_id']:
        params['dataset_id'] = "empty_dataset_id"

    # Отправить сообщение о запуске с указанием хоста и container_id 
    if container_id:
        url = f"{C.HOST_RESTAPI}/containers/{container_id}/on_start"
    else:
        url = f"{C.HOST_RESTAPI}/containers/{container_id}/on_error"
    
    response = { 'host' : vm_ip, 'dataset_id' : params['dataset_id']}
    logger.info(f'Send post: Url: {url} , body: {response}')

    requests.post(url, json = response)
    
    return {"error": is_error, "container_id" : container_id}

# def start_container(container_id: str): 
#     try:
#         container = client.containers.get(container_id)
#         container.start()
#         logger.info(f"Контейнер {container_id} успешно запущен.")
#     except NotFound:
#         logger.warning(f"Контейнер с ID {container_id} не найден.")
#     except APIError as e:
#         logger.error(f"Ошибка Docker API: {e.explanation}")
#     except Exception as e:
#         logger.exception(f"Произошла непредвиденная ошибка: {e}")    
#     return {"status": "started"}

# def stop_container(container_id: str, force=True): 
#     try:
#         container = client.containers.get(container_id)
#         container.stop(timeout=0)  # Или container.kill() для жёсткой остановки
#         logger.info(f"Контейнер {container_id} успешно остановлен.")
#     except NotFound:
#         logger.warning(f"Контейнер с ID {container_id} не найден.")
#     except APIError as e:
#         logger.error(f"Ошибка Docker API: {e.explanation}")
#     except Exception as e:
#         logger.exception(f"Произошла непредвиденная ошибка: {e}")
#     return {"status": "stopped"}

def is_host_reachable(ip, port=2375, timeout=3):
    logger.info("Start is_host_reachable")
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False

def check_vm_containers(vm_ip, ann_images):
    logger.info("Start check_vm_containers")
    if not is_host_reachable(vm_ip):
        logger.error(f"{vm_ip} недоступен")
        return True  # превышен таймаут подключение считаем, что VM можно пропустить
        
    try:
        # Подключение к удаленному Docker Engine API
        url = f'tcp://{vm_ip}:2375' 
        logger.info(f"Подключение к удаленной ВМ {url}")
        client = docker.DockerClient(base_url=url, timeout=5) 
        containers = client.containers.list()
        logger.info(f"{vm_ip} containers: {containers}")

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

        logger.info(f"{vm_ip} search result: {has_ann_image}")
        return has_ann_image

    except Exception as e:
        logger.error(f'Ошибка при подключении к {vm_ip}: {e}')
        # Возвращаем True, чтобы не останавливать перебор
        return True 
    

def find_vm_without_ann_images():
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