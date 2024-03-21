#  # python3 -m venv venv
#  source venv/bin/activate
#  uvicorn app.main:app --reload
from typing import Annotated
from fastapi import FastAPI, Form
from api.manage.manage import *
from api.logg import *


logger.info("Main is started")
app = FastAPI()

# Users 
# create new
@app.post("/users/create")
async def api_create_user(name: Annotated[str, Form()],
                          login: Annotated[str, Form()],
                          password: Annotated[str, Form()],
                          role: Annotated[str, Form()],
                          description: Annotated[str, Form()]
                          ):
   return mng_create_user(name, login, password, role, description)

# select one record by id        # fa33e1e7-0474-446c-9284-6ebda3f14fa0
@app.get("/users/{userId}")
async def api_single_user(userId):
   output = mng_single_user(userId)
   return output

# delete record by id
@app.delete("/users/{userId}")
async def api_single_user(userId):
   output = mng_single_user(userId)
   return output


# update record by id
@app.patch("/users/{userId}")
async def api_update_user(name: Annotated[str, Form()],
                          login: Annotated[str, Form()],
                          password: Annotated[str, Form()],
                          role: Annotated[str, Form()],
                          description: Annotated[str, Form()]
                          ):
   output = mng_update_user(name, login, password, role, description)
   return output



# Roles
@app.post("/roles/create")
async def api_create_role(code: Annotated[str, Form()],
                          name: Annotated[str, Form()]
                          ):
   return mng_create_role(name = name, code=code)

# Projects


# Docker functions 
@app.get("/docker/info")
async def api_docker_get_info():
   return mng_docker_get_info()

