from fastapi import FastAPI, Request, Body, HTTPException
from api.lib.func_request import get_request_params
from api.sets.metadata_fastapi import *
from api.manage.manage import *
from api.lib.reqest_classes import *
from api.format.exceptions import http_exception_handler, NotFoundError
import datetime as dt
from api.lib.classExportDBToAnnJson import *
from api.lib.VideoConverter import VideoConverter
from api.lib.AnnExport import ANNExporter
from fastapi import Response, status, Path

from fastapi.responses import JSONResponse
from api.services import docker_service
from  api.format.logger import logger

from pathlib import Path as PathLib

app = FastAPI(openapi_tags=tags_metadata)

app.add_exception_handler(HTTPException, http_exception_handler)

# PROJECTS

@projects.post("/{projectId}/datasets/{datasetId}/import", summary="Загрузка датасета из JSON файлов")
async def api_import_json_to_db(request: Request,
      projectId:str,
      datasetId:str,
      import_data:DatasetImport
   ):
   logger.info(f"Requested url: /{projectId}/datasets/{datasetId}/import")
   res = mng_import_json_to_db(projectId, datasetId, import_data)
   logger.info(f"Результат import: {res}")
   return res


@projects.post("/{projectId}/datasets/{datasetId}/export", summary="Запускает процесс формирования JSON файлов разметки датасета и возвращает признак успешного начала операции. По окончании операции вызывается соотв. роут export on_save")
async def api_export_db_to_json(request: Request,
      project_id:str = Path(..., alias="projectId"),
      dataset_id:str = Path(..., alias="datasetId"),
      exparams:DbExportParams = Body(...),
   ):
   post_data = exparams.getAllParams()
   post_data['project_id'] = project_id
   post_data['dataset_id'] = dataset_id
   return mng_export_db_to_json(post_data)


# DOCKER


@docker.get("/", tags=["Docker"], summary="Получение информации о состоянии Docker")
async def api_docker_info(): 
   return mng_docker_info()


# IMAGES


@docker_images.get("/", tags=["Docker-образы"], summary="Получение списка Docker-образов на сервере")
async def api_docker_images():
   #  logger.info("Получение списка Docker-образов на сервере")
    try:
        images = docker_service.get_docker_images()
        response = JSONResponse(content={
            "pagination": {"totalItems": len(images)},
            "items": images
        })
        logger.info(f"Результат images: {response}")
        return response
    except Exception as e:
        response = JSONResponse(status_code=500, content={
            "code": 500,
            "message": str(e)
        })
        logger.info(f"Ошибка status_code=500: {response}")
        return 


@docker_images.get("/{imageId}", tags=["Docker-образы"], summary="Получение информации о Docker-образе на сервере") 
async def get_docker_image(image_id: str = Path(..., alias="imageId")):
   #  logger.info("Получение информации о Docker-образе на сервере")
    try:
        image = docker_service.find_image_by_id(image_id)
        logger.info(f"Результат поиска: {image}")
        if image:
            logger.info(f"Response на запрос: {image} ")
            return image
        else:
            logger.info(f"Response на запрос: status_code=404 , Ошибка: образ не найден {image_id} ")
            raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        logger.info(f"Response на запрос: status_code=500 , Ошибка: {image_id} Описание: {str(e)} ")
        return {
            "code": 500,
            "message": str(e)
        }

@docker_images.post("/{imageId}/run", tags=["Docker-образы"], summary="Создание Dockеr-контейнера из Docker-образа и его запуск")
async def api_docker_image_run(request: Request,
      imageId:str,
      imrun: ImageRun
   ):
   logger.info("Создание Dockеr-контейнера из Docker-образа и его запуск")
   post_data = imrun.getAllParams()
   post_data['image_id'] = imageId
   return mng_image_run( post_data)


# ANN


@ann.post("/{annId}/archive/save", tags=["ИНС"], summary="Выгрузка ИНС (Docker-образа и файла весов) в архив")
async def api_docker_ann_export(request: Request,
      annId:str,
      export: ANNExport ):
   logger.info("Выгрузка ИНС (Docker-образа и файла весов) в архив")
   exporter = ANNExporter(ann_id=annId, export_data=export)
   exporter.run()
   return {"status":"running"}


# CONTAINERS
    

@docker_containers.get("/vm/check")
async def get_vm_without_ann():
    result, is_error = docker_service.get_available_vm() 
    if is_error:
        message = f'Ошибка при просмотре VM: {result}'
    elif result: 
        message = f'Свободная VM: {result}'
    else:
        message = 'Нет свободных VM.'            

    return {"message": message}    


@docker_containers.get("/", tags=["Docker-контейнеры"], summary="Получение списка Docker-контейнеров на сервере") 
async def get_containers():
    logger.info("Получение списка Docker-контейнеров на сервере")
    try:
        containers = docker_service.get_docker_containers()
        return {
            "pagination": {
                "totalItems": len(containers)
            },
            "items": containers
        }
    except Exception as e:
        docker_service.logger.error(f"Error retrieving containers: {str(e)}")
        return Response(
            content={
                "code": 500,
                "message": str(e)
            },
            media_type="application/json",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@docker_containers.get("/stats", tags=["Docker-контейнеры"], summary="Получение списка состояний Docker-контейнеров на сервере")
async def api_docker_containers_stats():
   logger.info("Получение списка состояний Docker-контейнеров на сервере")
   containers = docker_service.get_docker_containers_stats()
   return {"items": containers}


@docker_containers.get("/{containerId}", tags=["Docker-контейнеры"], summary="Получение информации о Docker-контейнере на сервере")
async def api_docker_container(container_id: str = Path(..., alias="containerId")):
    try:
        container = docker_service.find_container_by_id(container_id)
        if container:
            return container

        logger.error(f"Контейнер не найден: {container_id}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при получении контейнера {container_id}: {e}")
        return False


@docker_containers.get("/{containerId}/stats", tags=["Docker-контейнеры"], summary="Получение состояния Docker-контейнера на сервере")
async def api_docker_container_stats(container_id: str = Path(..., alias="containerId")):    
    try:
        container = docker_service.find_container_by_id(container_id, 'stats')
        if container:
            return container

        logger.error(f"Контейнер не найден: {container_id}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при получении контейнера {container_id}: {e}")
        return False


@docker_containers.get("/{containerId}/monitor", tags=["Docker-контейнеры"], summary="Получение списка виджетов для мониторинга состояния Docker-контейнера")
async def api_docker_container_monitor(containerId):
   return mng_container_monitor(containerId)


@docker_containers.put("/{containerId}/start", tags=["Docker-контейнеры"], summary="Запуск Docker-контейнер на сервере")
async def api_docker_container_start(containerId ):
   return mng_container_start(containerId)


@docker_containers.put("/{containerId}/stop", tags=["Docker-контейнеры"], summary="Остановка Docker-контейнер на сервере")
async def api_docker_container_stop(request: Request,
      data:ContainerOnStopPostData,
      container_id: str = Path(..., alias="containerId") ):
   logger.info("Остановка Docker-контейнер на сервере")
   try:
      threading.Thread(target=mng_container_stop, args=(container_id, data.dataset_id)).start()
      # resp = mng_container_stats(containerId)
      return {"message": "Запрос на остановку отправлен"}
   except Exception as e:
      raise HTTPException(status_code=500, detail=str(e))
   

# VIDEO CONVERTER


@app.post("/video/converter")
async def api_video_convert(req: VideoConverterParams):
    source_dir = PathLib(req.source_dir)
    target_dir = PathLib(req.target_dir)
    if not source_dir.exists() or not source_dir.is_dir():
        raise HTTPException(status_code=400, detail="Указанная директория не существует или не является директорией")

    converter = VideoConverter(source_dir, target_dir)
    message = converter.run()
    return {"message": message}

app.include_router(projects)
app.include_router(proj_datasets)
app.include_router(proj_dts_files)
app.include_router(proj_dts_primitives)
app.include_router(proj_dts_prim_chains)
app.include_router(proj_dts_ann)
app.include_router(docker)
app.include_router(docker_images)
app.include_router(docker_containers)
app.include_router(events)
