#  # python3 -m venv venv
#  source venv/bin/activate
#  uvicorn app.main:app --reload
from fastapi import FastAPI, Request, APIRouter
from api.lib.func_request import get_request_params
from api.sets.metadata_fastapi import *
from api.manage.manage import *
from api.logg import *


users = APIRouter(
   prefix="/users",
   tags=["Пользователи"],
)

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


app.include_router(users)


# Roles
@app.post("/roles/create", tags=["Роли"], summary="Создание роли")
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


# # Docker 
# @app.get("/docker/info")
# async def api_docker_get_info():
#    return mng_docker_get_info()


# #TEST
# @app.post("/test/{id}")
# async def api_data(request: Request, id:str, name:str | None = None, desc:str | None = None):
#     params = get_request_params(request)
#     return (params)