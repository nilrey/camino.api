#  # python3 -m venv venv
#  source venv/bin/activate
#  uvicorn app.main:app --reload
from fastapi import FastAPI, Form, UploadFile
from api.manage.manage import *
from api.logg import *
import json


logger.info("Main is started")
app = FastAPI()

# Users 
@app.post("/users/create")
async def api_create_user(name:str,
                          login:str,
                          password:str,
                          role:str,
                          description:str = None,
                          ):
   return mng_create_user(name, login, password, role, description)

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


# Docker functions 
@app.get("/docker/info")
async def api_docker_get_info():
   return mng_docker_get_info()
