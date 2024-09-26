from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from sqlalchemy import text, insert, update, select, delete
import uuid, json
from typing import List
from sqlalchemy import bindparam, text
from configparser import ConfigParser

def load_config(filename='database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    # get section, default to postgresql
    config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            config[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return config


def get_connection_string():
   config = load_config()
   cs = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
   return cs


def make_session():
   engine = create_engine(get_connection_string())
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


def select_wrapper(stmt, params={}):
   resp = {}
   with db_conn() as session:
      resp = session.execute(stmt, params).mappings().all()
   return resp



def q_project_select_by_project_id(id):
   stmt = text("SELECT u.id, u.name FROM project_users pu \
   JOIN users u ON pu.user_id=u.id \
   WHERE pu.project_id = :project_id")
   resp = select_wrapper(stmt, {"project_id" : id} )
   return resp


def q_project_select_by_user_id(id):
   stmt = text("SELECT * FROM project_users pu \
   JOIN projects p ON pu.project_id=p.id \
   JOIN users u ON pu.user_id=u.id \
   WHERE pu.user_id = :user_id")
   resp = select_wrapper(stmt, {"user_id" : id} )
   return resp



   


# if(__name__ == "__main__"):
#    print(get_connection_string())
#    print("Ok")