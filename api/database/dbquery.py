from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from sqlalchemy import text, insert, update, select, delete
import uuid
from typing import List
from api.logg import *


def make_session():
   engine = create_engine('postgresql://postgres:postgres@127.0.0.1:5432/camino_db1')
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


def select_byid(ClassName, recordId):
   all_rec: List[ClassName] = db_conn().query(ClassName).filter_by(id=recordId)
   return all_rec.first()


def records_count(ClassName, recordId):
   all_rec: List[ClassName] = db_conn().query(ClassName).filter_by(id=recordId).all()
   return len(all_rec)


def insert_new(ClassName, newRecord, doReturnId = True):
   try:      
      with db_conn() as session:
         session.add(newRecord)
         session.commit()
         session.refresh(newRecord)
      if doReturnId == True:
         resp = select_byid(ClassName, newRecord.id)
      else:
         resp = newRecord
   except Exception as e:
      resp = {'error':True, 'message':str(e)}
   return resp


def select_all(ClassName):
   all_rec: List[ClassName] = db_conn().query(ClassName).all()
   return all_rec


def update_record(ClassName, recId, **values):
   try:
      with db_conn() as session:
         stmt = update(ClassName).values(**values).filter_by(id=recId)
         session.execute(stmt)
         session.commit()
      resp = select_byid(ClassName, recId)
   except Exception as e:
      resp = {'error':True, 'message':str(e)}

   return resp


def delete_record(ClassName, recId):
   try:
      with db_conn() as session:
         record = session.query(ClassName).filter_by(id=recId).first()
         session.delete(record)
         session.commit()
      resp = {'id':recId, 'count': records_count(ClassName, recId)}

   except Exception as e:
      resp = {'error':True, 'message':str(e)}

   return resp