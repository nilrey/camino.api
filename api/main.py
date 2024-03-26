#  # python3 -m venv venv
#  source venv/bin/activate
#  uvicorn app.main:app --reload
from fastapi import FastAPI, Form, UploadFile, Request
from api.lib.func_request import get_request_params
from api.manage.manage import *
from api.logg import *


app = FastAPI()


# Users 
@app.post("/users/create")
async def api_create_user(request: Request, 
                          name:str,
                          login:str,
                          password:str,
                          role:str,
                          description:str = None,
                          ):
   return mng_create_user(**get_request_params(request))

# select one record by id        # fa33e1e7-0474-446c-9284-6ebda3f14fa0
@app.get("/users/{userId}")
async def api_single_user(userId):
   output = mng_single_user(userId)
   return output

# delete record by id
@app.delete("/users/{userId}")
async def api_delete_user(userId):
   output = mng_delete_user(userId)
   return output


# update record by id
@app.put("/users/{userId}")
async def api_update_user(userId, 
                          name:str = None,
                          login:str = None ,
                          password:str = None ,
                          role:str = None ,
                          description: str = None 
                          ):
   fields = {'name':name, 'login':login, 'password':password, 'role_code':role, 'description':description }
   logger.info(fields)
   output = mng_update_user(userId, **fields)
   return output


# Roles
@app.post("/roles/create")
async def api_create_role(code:str = None,
                          name:str = None
                          ):
   return mng_create_role(name = name, code=code)


# Projects
@app.post("/projects/create")
async def api_create_project(
                              name:str, 
                              type_id:str = None,
                              description:str = None, 
                              author_id:str = None, 
                              dt_created:str = None, 
                              is_deleted:str = None):
   fields = {'name':name, 'type_id':type_id, 'description':description, 'author_id':author_id, 'dt_created':dt_created, 'is_deleted':is_deleted}
   return mng_create_project(**fields)


# select one record by id 
@app.get("/projects/{projectId}")
async def api_single_project(projectId):
   output = mng_single_project(projectId)
   return output


# delete record by id
@app.delete("/projects/{projectId}")
async def api_delete_project(projectId):
   output = mng_delete_project(projectId)
   return output


# update record by id
@app.put("/projects/{projectId}")
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


# Docker 
@app.get("/docker/info")
async def api_docker_get_info():
   return mng_docker_get_info()


#TEST
@app.post("/test/{id}")
async def api_data(request: Request, id:str, name:str | None = None, desc:str | None = None):
    params = get_request_params(request)
    return (params)