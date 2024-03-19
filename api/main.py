#  # python3 -m venv venv
#  source venv/bin/activate
#  uvicorn app.main:app --reload
from typing import Annotated
from fastapi import FastAPI, Form
from api.manage.manage import *
from api.bin.doc import getDockerInfo

app = FastAPI()

@app.post("/users/create")
async def api_create_user(name: Annotated[str, Form()],
                          login: Annotated[str, Form()],
                          password: Annotated[str, Form()],
                          role: Annotated[str, Form()],
                          description: Annotated[str, Form()]
                          ):
   return mng_create_user(name, login, password, role, description)

# fa33e1e7-0474-446c-9284-6ebda3f14fa0
@app.get("/users/{userId}")
async def api_single_user(userId):
   res = mng_single_user(userId)
   return res


@app.post("/roles/create")
async def api_create_role(code: Annotated[str, Form()],
                          name: Annotated[str, Form()]
                          ):
   return mng_create_role(name = name, code=code)


@app.get("/docker/info")
async def docker_get_info():
   return getDockerInfo()

