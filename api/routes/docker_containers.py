# from fastapi import APIRouter, Response, Request, Path, Body, HTTPException, status
from . import router, Request, Path, Body, HTTPException, logger, endpoints_internal as ep
import threading
from api.lib.posted_data_classes import *
from api.services import docker_services
from api.services.monitor import Monitor

router_containers = router(prefix="/containers", tags=["Docker-контейнеры"])

@router_containers.get("/", tags=["Docker-контейнеры"], summary="Получение списка Docker-контейнеров на сервере") 
async def get_containers():
    logger.info("Получение списка Docker-контейнеров на сервере")
    try:
        containers = docker_services.get_vms_containers()
        return { "pagination": { "totalItems": len(containers) },
                 "items": containers }
    except Exception as e:
        logger.info(f"Ошибка при получении списка Docker-контейнеров: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router_containers.get("/stats", tags=["Docker-контейнеры"], summary="Получение списка состояний Docker-контейнеров на сервере")
async def api_docker_containers_stats():
   logger.info("Получение списка состояний Docker-контейнеров на сервере")
   containers = docker_services.get_vms_containers_stats()
   return {"items": containers}


@router_containers.get("/{containerId}", tags=["Docker-контейнеры"], summary="Получение информации о Docker-контейнере на сервере")
async def api_docker_container(container_id: str = Path(..., alias="containerId")):
    try:
        container = docker_services.find_container_by_id(container_id)
        if container:
            return container

        logger.error(f"Контейнер не найден: {container_id}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при получении контейнера {container_id}: {e}")
        return False


@router_containers.get("/{containerId}/stats", tags=["Docker-контейнеры"], summary="Получение состояния Docker-контейнера на сервере")
async def api_docker_container_stats(container_id: str = Path(..., alias="containerId")):    
    try:
        container = docker_services.find_container_by_id(container_id, 'stats')
        if container:
            return container

        logger.error(f"Контейнер не найден: {container_id}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при получении контейнера {container_id}: {e}")
        return False
   

@router_containers.put("/{containerId}/start", tags=["Docker-контейнеры"], summary="Запуск Docker-контейнер на сервере")
async def api_docker_container_start(container_id: str = Path(..., alias="containerId") ):
    return docker_services.start_container(container_id)


@router_containers.put("/{containerId}/stop", tags=["Docker-контейнеры"], summary="Остановка Docker-контейнер на сервере")
async def api_docker_container_stop(request: Request,
      data:PostedDataContainerStop,
      container_id: str = Path(..., alias="containerId") ):
   logger.info("Остановка Docker-контейнер на сервере")
   try:
      thread = threading.Thread(target=docker_services.stop_container, args=(container_id, data.dataset_id))
      thread.start()
      # resp = mng_container_stats(containerId)
      return {"message": "Запрос на остановку отправлен"}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))


@router_containers.get("/{containerId}/monitor", tags=["Docker-контейнеры"], summary="Получение списка виджетов для мониторинга состояния Docker-контейнера")
async def api_docker_container_monitor(container_id: str = Path(..., alias="containerId")):
    monitor = Monitor()
    result = monitor.create_json(container_id)
    return result