from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from api.models.models import *
import uuid

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


def mng_create_user( name, login, password, role, description):
    newUser = insert_new (User, User( id=getUuid(), name = name, login=login, role_code=role, password=password, description=description, is_deleted=False) )

    return newUser