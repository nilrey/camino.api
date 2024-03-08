#  python3 -m venv venv
#  source venv/bin/activate
from typing import List
from fastapi import FastAPI
import psycopg2
import json
from api.config import load_config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from api.models.models import Role


app = FastAPI()
engine = create_engine('postgresql://postgres:postgres@127.0.0.1/camino_db1')

@app.get("/api/roles/{role_id}")
async def read_item(role_id):
   config  = load_config()
   with psycopg2.connect(**config) as conn:
      with conn.cursor() as cur:
         table  = "common.roles"
         uid = "operator"
         query = f"SELECT * FROM {table} where code='{uid}'"
         with open('logfile1.log', 'w') as f:
            f.write(query)
         cur.execute(query)
   return {"role_count": cur.rowcount}

@app.get("/roles")
async def orm_get_roles():
   session_maker = sessionmaker(bind=engine)
   db: Session = session_maker()
   all_roles: List[Role] = db.query(Role).all()
   return json.dumps( {'results': [ {"name":rl.name, "code":rl.code} for rl in all_roles ] } )


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