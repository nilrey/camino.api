#  # python3 -m venv venv
#  source venv/bin/activate
#  uvicorn api.main:app --reload
from fastapi import FastAPI, Request, HTTPException
from api.lib.func_request import get_request_params
from api.sets.metadata_fastapi import *
from api.manage.manage import *
# from api.logg import *
from api.lib.reqest_classes import *
from api.format.exceptions import http_exception_handler, NotFoundError
import datetime as dt
from api.lib.classExportDBToAnnJson import *
import requests


app = FastAPI(openapi_tags=tags_metadata)

app.add_exception_handler(HTTPException, http_exception_handler)


# USERS


@users.get("", summary="Получение списка пользователей")
async def api_all_users():
   output = mng_all_users()
   return output


@users.post("/create", summary="Создание пользователя")
async def api_create_user(request: Request, 
      name:str,
      login:str,
      password:str,
      role_code:str,
      description:str = None
   ):
   return mng_create_user(**get_request_params(request))


@users.get("/{userId}", summary="Получение информации пользователя")
async def api_single_user(userId):
   output = mng_single_user(userId)
   return output


@users.put("/{userId}", summary="Обновление информации пользователя")
async def api_update_user(request: Request,
      userId:str,
      name:str,
      login:str,
      password:str,
      role_code:str,
      description:str = None
   ):
   return mng_update_user(userId, **get_request_params(request, True, False))


@users.delete("/{userId}", summary="Удаление пользователя")
async def api_delete_user(userId):
   output = mng_delete_user(userId)
   return output


# ROLES


@roles.post("/create", tags=["Роли"], summary="Создание роли")
async def api_create_role(code:str = None,
      name:str = None
   ):
   return mng_create_role(name = name, code=code)


# PROJECTS


@projects.get("/", tags=["Проекты"], summary="Получение списка проектов")
async def api_all_projects():
   output = mng_all_projects()
   return output


@projects.post("/create", tags=["Проекты"], summary="Создание проекта")
async def api_create_project( request: Request, 
      name:str, 
      type_id:int = 1,
      description:str = None, 
      author_id:str = None
   ):
   return mng_create_project(**get_request_params(request))


@projects.get("/{projectId}", tags=["Проекты"], summary="Получение информации о проекте")
async def api_single_project(projectId):
   output = mng_single_project(projectId)
   return output


@projects.get("/ext/{projectId}", tags=["Проекты"], summary="Получение информации о проекте")
async def api_single_project_ext(projectId:str):
   output = mng_single_project_ext(projectId)
   return output


@projects.put("/{projectId}", tags=["Проекты"], summary="Обновление информации о проекте")
async def api_update_project(projectId,
      name:str = None, 
      type_id:str = None,
      description:str = None, 
      author_id:str = None, 
      dt_created:str = None, 
      is_deleted:bool = None
   ):
   fields = {'name':name, 'type_id':type_id, 'description':description, 'author_id':author_id, 'dt_created':dt_created, 'is_deleted':is_deleted}
   output = mng_update_project(projectId, **fields)
   return output


@projects.delete("/{projectId}", tags=["Проекты"], summary="Удаление проекта")
async def api_delete_project(projectId):
   output = mng_delete_project(projectId)
   return output


@projects.post("/{projectId}/datasets/{datasetId}/import", summary="Загрузка датасета из JSON файлов")
async def api_import_json_to_db(request: Request,
      projectId:str,
      datasetId:str,
      parse_data:ANNParseOutput
   ):
   return mng_import_json_to_db(projectId, datasetId, parse_data)


# DOCKER


@docker.get("/", tags=["Docker"], summary="Получение информации о состоянии Docker")
async def api_docker_info():
   return mng_docker_info()


# IMAGES


@docker_images.get("/", tags=["Docker-образы"], summary="Получение списка Docker-образов на сервере")
async def api_docker_images():
   return mng_images()


@docker_images.get("/{imageId}", tags=["Docker-образы"], summary="Получение информации о Docker-образе на сервере")
async def api_docker_image(imageId):
   return mng_image(imageId)


@docker_images.put("/{imageId}/create", tags=["Docker-образы"], summary="Создание Docker-контейнера из Docker-образа")
async def api_docker_image_create(request: Request,
      imageId:str,
      ContCreate: ContainerCreate
   ):
   return mng_container_create(imageId, ContCreate.getAllParams() )


# @docker_images.post("/{imageId}/run/old", tags=["Docker-образы"], summary="Создание Dockеr-контейнера из Docker-образа и его запуск")
# async def api_docker_image_run2(request: Request,
#       imageId:str,
#       imrun: ImageRun
#    ):
#    return mng_image_run2(imageId, imrun.getAllParams() )


@docker_images.post("/{imageId}/run", tags=["Docker-образы"], summary="Создание Dockеr-контейнера из Docker-образа и его запуск")
async def api_docker_image_run(request: Request,
      imageId:str,
      imrun: ImageRun
   ):
   return mng_image_run(imageId, imrun.getAllParams() )


# ANN


@ann.post("/{annId}/archive/save", tags=["ИНС"], summary="Выгрузка ИНС (Docker-образа и файла весов) в архив")
async def api_docker_ann_export(request: Request,
      annId:str,
      export: ANNExport ):
   return mng_ann_export(export.image_id, export.weights, export.export, annId)


# CONTAINERS


@docker_containers.get("/", tags=["Docker-контейнеры"], summary="Получение списка Docker-контейнеров на сервере")
async def api_docker_containers():
   return mng_containers()


@docker_containers.get("/stats", tags=["Docker-контейнеры"], summary="Получение списка состояний Docker-контейнеров на сервере")
async def api_docker_containers_stats():
   return mng_containers_stats()


@docker_containers.get("/{containerId}", tags=["Docker-контейнеры"], summary="Получение информации о Docker-контейнере на сервере")
async def api_docker_container(containerId):
   return mng_container(containerId)


@docker_containers.get("/{containerId}/stats", tags=["Docker-контейнеры"], summary="Получение состояния Docker-контейнера на сервере")
async def api_docker_container_stats(containerId):
   return mng_container_stats(containerId)


@docker_containers.get("/{containerId}/monitor", tags=["Docker-контейнеры"], summary="Получение списка виджетов для мониторинга состояния Docker-контейнера")
async def api_docker_container_monitor(containerId):
   return mng_container_monitor(containerId)


@docker_containers.put("/{containerId}/start", tags=["Docker-контейнеры"], summary="Запуск Docker-контейнер на сервере")
async def api_docker_container_start(containerId ):
   return mng_container_start(containerId)


@docker_containers.put("/{containerId}/stop", tags=["Docker-контейнеры"], summary="Остановка Docker-контейнер на сервере")
async def api_docker_container_stop(containerId ):
   return mng_container_stop(containerId)


# EVENTS


@events.post("/{containerId}/before_start", summary="Мок-обработчик - Событие начала обработки данных")
async def api_docker_events_before_start(request: Request,
      containerId:str,
      event: ANNEventBeforeRun
   ):
   return {"result":"ok", "conainerId":containerId}


#   event  on_progress
@events.post("/{containerId}/on_progress", summary="Мок-обработчик - Событие в процессе обработки данных")
async def api_docker_events_on_progress(request: Request,
      containerId:str,
      event: ANNEventBeforeRun
   ):
   return {"result":"ok", "status":"on_progress", "conainerId":containerId}


#   event  before_end
@events.post("/{containerId}/before_end", summary="Мок-обработчик - Событие в конце обработки данных")
async def api_docker_events_before_end(request: Request,
      containerId:str,
      event: ANNEventBeforeRun
   ):
   return {"result":"ok", "status":"before_end", "conainerId":containerId}


app.include_router(auth)
app.include_router(projects)
app.include_router(proj_users)
app.include_router(proj_datasets)
app.include_router(proj_dts_files)
app.include_router(proj_dts_primitives)
app.include_router(proj_dts_prim_chains)
app.include_router(proj_dts_ann)
app.include_router(users)
app.include_router(roles)
app.include_router(docker)
app.include_router(docker_registry)
app.include_router(docker_images)
app.include_router(docker_containers)
app.include_router(events)
app.include_router(ann)