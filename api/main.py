#  # python3 -m venv venv
#  source venv/bin/activate
#  uvicorn app.main:app --reload
from typing import List, Annotated
from fastapi import FastAPI, Form
import psycopg2
import json
import uuid
from api.config import load_config
from api.manage import mng_create_user
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from api.models.models import *
from api.bin.doc import getDockerInfo

app = FastAPI()

def make_session():
   engine = create_engine('postgresql://postgres:postgres@127.0.0.1/camino_db1')
   session_maker = sessionmaker(bind=engine)
   return session_maker
   
def db_conn():
   session_maker = make_session()
   db: Session = session_maker()
   return db

def getUuid():
   return str(uuid.uuid4())

def insert_new(ClassName, newRecord, returnId = True):
   session_factory = make_session()
   with db_conn() as session:
      session.add(newRecord)
      session.commit()
      session.refresh(newRecord)
   if returnId == True:
      nRecord: List[ClassName] = db_conn().query(ClassName).filter_by(id=newRecord.id)
      resp = nRecord[0]
   else:
      resp = newRecord
   return resp

@app.post("/users/create")
async def orm_create_user(name: Annotated[str, Form()],
                          login: Annotated[str, Form()],
                          password: Annotated[str, Form()],
                          role: Annotated[str, Form()],
                          description: Annotated[str, Form()]
                          ):
   
   return mng_create_user(name, login, password, role, description)

# 978bb79f-d2d9-4cb2-94c9-3a75c8960729
@app.get("/users/{userId}")
async def orm_single_user(userId):
   all_users: List[User] = db_conn().query(User).filter_by(id=userId)
   return  [ {"id": ln.id, "name": ln.name, "role_code": ln.role_code,  "login": ln.login, "password": ln.password, "description": ln.description,  "is_deleted": ln.is_deleted} for ln in all_users ] 


@app.post("/roles/create")
async def orm_create_role(code: Annotated[str, Form()],
                          name: Annotated[str, Form()]
                          ):
   newRole = insert_new (Role, Role( name = name, code=code ) , False)
   return newRole


@app.get("/docker/info")
async def docker_get_info():
   return getDockerInfo()


# @app.post("/projects/create")
# async def set_project(project_id):
#     return {"project_id": project_id}

# @app.get("/projects")]
# async def list_projects():
#     return {"project_id": {11111111111111111}}

# @app.post("/projects/create")
# async def set_project(project_id):
#     return {"project_id": {22222222222222222}}

# @app.get("/projects/{project_id}")
# async def get_project(project_id):
#     return {
#       "id": "550e8400-e29b-41d4-a716-446655440001",
#       "name": "Проект 1",
#       "type": "teach",
#       "description": "Описание проекта 1",
#       "author": {
#          "id": "550e8400-e29b-41d4-a716-446655440001",
#          "name": "Петров Иван Иванович"
#       },
#       "dt_created": "2023-12-26 15:00:00"
#       }