#  # python3 -m venv venv
#  source venv/bin/activate
#  uvicorn api.main:app --reload
from fastapi import FastAPI, Request
from api.lib.func_request import get_request_params
from api.sets.metadata_fastapi import *
from api.manage.manage import *
from api.logg import *


app = FastAPI(openapi_tags=tags_metadata)


# Users 
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



# Roles
@roles.post("/create", tags=["Роли"], summary="Создание роли")
async def api_create_role(code:str = None,
                          name:str = None
                          ):
   return mng_create_role(name = name, code=code)


# Projects
@app.get("/projects", tags=["Проекты"], summary="Получение списка проектов")
async def api_all_projects():
   output = mng_all_projects()
   return output


@app.post("/projects/create", tags=["Проекты"], summary="Создание проекта")
async def api_create_project( request: Request, 
                              name:str, 
                              type_id:int = 1,
                              description:str = None, 
                              author_id:str = None):
   return mng_create_project(**get_request_params(request))


@app.get("/projects/{projectId}", tags=["Проекты"], summary="Получение информации о проекте")
async def api_single_project(projectId):
   output = mng_single_project(projectId)
   return output


@app.get("/projects/ext/{projectId}", tags=["Проекты"], summary="Получение информации о проекте")
async def api_single_project_ext(projectId:str):
   output = mng_single_project_ext(projectId)
   return output


@app.put("/projects/{projectId}", tags=["Проекты"], summary="Обновление информации о проекте")
async def api_update_project(projectId,
                              name:str = None, 
                              type_id:str = None,
                              description:str = None, 
                              author_id:str = None, 
                              dt_created:str = None, 
                              is_deleted:bool = None):
   fields = {'name':name, 'type_id':type_id, 'description':description, 'author_id':author_id, 'dt_created':dt_created, 'is_deleted':is_deleted}
   output = mng_update_project(projectId, **fields)
   return output


@app.delete("/projects/{projectId}", tags=["Проекты"], summary="Удаление проекта")
async def api_delete_project(projectId):
   output = mng_delete_project(projectId)
   return output


# Docker info
@app.get("/docker", tags=["Docker"], summary="Получение информации о состоянии Docker")
async def api_docker_get_info():
   return mng_docker_get_info()


@app.get("/images", tags=["Docker-образы"], summary="Получение списка Docker-образов на сервере")
async def api_docker_images():
   return mng_images()


@app.get("/images/{imageId}", tags=["Docker-образы"], summary="Получение информации о Docker-образе на сервере")
async def api_docker_image(imageId):
   return mng_image(imageId)


# # Create container from Docker image
# @app.get("/images/{imageId}/run", tags=["Docker-образы"], summary="Создание Dockеr-контейнера из Docker-образа и его запуск")
# async def api_docker_image_run(imageId):
#    return mng_docker_image_run(imageId)


# Create container from Docker image
@docker_images.post("/{imageId}/run", tags=["Docker-образы"], summary="Создание Dockеr-контейнера из Docker-образа и его запуск")
async def api_docker_image_run(request: Request,
                          imageId:str,
                          name:str = None,
                          weights:str = None,
                          hyper_params:str = None,
                          in_dir:str = None,
                          out_dir:str = None
                          ):
   return mng_docker_image_run(imageId, **get_request_params(request, True, False))


@app.get("/containers", tags=["Docker-контейнеры"], summary="Получение списка Docker-контейнеров на сервере")
async def api_docker_containers():
   return mng_containers()

@app.get("/containers/stats", tags=["Docker-контейнеры"], summary="Получение списка состояний Docker-контейнеров на сервере")
async def api_docker_containers_stats():
   return mng_containers_stats()

@app.get("/containers/{containerId}", tags=["Docker-контейнеры"], summary="Получение информации о Docker-контейнере на сервере")
async def api_docker_container(containerId):
   return mng_container(containerId)

@app.get("/containers/{containerId}/stats", tags=["Docker-контейнеры"], summary="Получение состояния Docker-контейнера на сервере")
async def api_docker_container_stats(containerId):
   return mng_container_stats(containerId)


# #TEST
# @app.post("/test/{id}")
# async def api_data(request: Request, id:str, name:str | None = None, desc:str | None = None):
#     params = get_request_params(request)
#     return (params)





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