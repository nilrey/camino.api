
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
import uuid
from typing import List


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

def parseDbException():
   resp = {
      "error" : True,
      "text" : ""
   }
   return resp


def insert_new(ClassName, newRecord, returnId = True):
   try:
      
      with db_conn() as session:
         session.add(newRecord)
         session.commit()
         session.refresh(newRecord)
      if returnId == True:
         nRecord: List[ClassName] = db_conn().query(ClassName).filter_by(id=newRecord.id)
         resp = nRecord[0]
      else:
         resp = newRecord
   except Exception as e:
      resp = {'error':True, 'message':str(e)}
   return resp


def select_byid(ClassName, recordId):
   all_rec: List[ClassName] = db_conn().query(ClassName).filter_by(id=recordId)
   return all_rec.first()