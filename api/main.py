#  # python3 -m venv venv
#  source venv/bin/activate
#  uvicorn app.main:app --reload
from fastapi import FastAPI, Form, UploadFile, Request
from api.lib.func_request import get_request_params
from api.manage.manage import *
from api.logg import *



tags_metadata = [
    {
        "name": "Аутентификация",
        "description": "API для аутентификации",
    },
    {
        "name": "Проекты",
        "description": "API для работы с проектами",
    },
    {
        "name": "Проект / Пользователи",
        "description": "API для работы с пользователями проекта",
    },
    {
        "name": "Проект / Датасеты",
        "description": "API для работы с датасетами проекта",
    },
    {
        "name": "Проект / Датасет / Файлы",
        "description": "API для работы с файлами датасета проекта",
    },
    {
        "name": "Проект / Датасет / Цепочки примитивов",
        "description": "API для работы с цепочками примитивов",
    },
    {
        "name": "Проект / Датасет / Примитивы",
        "description": "API для работы с примитивами",
    },
    {
        "name": "Проект / Датасет / ИНС",
        "description": "API для работы с ИНС датасета проекта",
    },
    {
        "name": "Пользователи",
        "description": "API для работы с пользователями",
    },
    {
        "name": "Роли",
        "description": "API для работы с ролями пользователей",
    },
    {
        "name": "Docker",
        "description": "API для Docker",
    },
    {
        "name": "Docker-реестр",
        "description": "API для Docker-реестра",
    },
    {
        "name": "Docker-образы",
        "description": "API для работы Docker-образами",
    },
    {
        "name": "Docker-контейнеры",
        "description": "API для работы с Docker-контейнерами",
    }
]

app = FastAPI(openapi_tags=tags_metadata)


# Users 
@app.post("/users/create", tags=["Пользователи"], summary="Создание пользователя")
async def api_create_user(request: Request, 
                          name:str,
                          login:str,
                          password:str,
                          role_code:str,
                          description:str = None,
                          ):
   return mng_create_user(**get_request_params(request))


@app.get("/users/{userId}", tags=["Пользователи"], summary="Получение информации пользователя")
async def api_single_user(userId):
   output = mng_single_user(userId)
   return output


@app.put("/users/{userId}", tags=["Пользователи"], summary="Обновление информации пользователя")
async def api_update_user(request: Request, 
                          userId:str,
                          name:str,
                          login:str ,
                          password:str ,
                          role_code:str ,
                          description: str = None 
                          ):
   return mng_update_user(userId, **get_request_params(request, True, False))


@app.delete("/users/{userId}", tags=["Пользователи"], summary="Удаление пользователя")
async def api_delete_user(userId):
   output = mng_delete_user(userId)
   return output


# Roles
@app.post("/roles/create", tags=["Роли"], summary="Создание роли")
async def api_create_role(code:str = None,
                          name:str = None
                          ):
   return mng_create_role(name = name, code=code)


# Projects
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