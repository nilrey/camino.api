import api.database.dbquery as dbq
import json
import datetime
from sqlalchemy import text
import threading 
from sqlalchemy.orm import Session


def tread_mark_insert_batch(stmt):
    # connection from the regular pool
    engine = dbq.create_engine(dbq.get_connection_string())
    connection = engine.connect()

    # detach it! now this connection has nothing to do with the pool.
    connection.detach()

    # pass the connection to the thread.  
    threading.Thread(target=thread_runner_batch, args=(connection, stmt)).start()


def thread_runner_batch(connection, stmt):
    try:
        with Session(connection) as session:
            resp = session.execute( text(stmt) )
            session.commit()
    finally:
        # closes the connection, i.e. the socket etc.
        connection.close()
        

def ann_out_db_save(filepath):
    # print('Start ' + str(datetime.datetime.now()))
    start =  str(datetime.datetime.now())
    with open(filepath, "r") as file:
        nn_output = json.load(file)
    if(nn_output['files']):
        nn_output['files'] = nn_output['files'][:3]
        count_inserts = total_inserts = 0
        stmt = f'INSERT INTO public.markups( id, previous_id, dataset_id, file_id, parent_id, mark_time, mark_path, vector, description, author_id, dt_created, is_deleted ) VALUES '
        query = ''
        for f in nn_output['files']:
            for chain in f['file_chains'] :
                for  chain_markup in chain['chain_markups']:
                    mdata = json.dumps(chain_markup["markup_path"])
                    mid = dbq.getUuid()
                    fid = 0
                    query += f'(\'{mid}\', null, null, null, null, 99, \'{mdata}\', \'{mdata}\', \'tread\', null, \'2024-09-16 12:00:00\', false),'
                    count_inserts += 1 
                    if(count_inserts == 1000 ):
                        total_inserts += count_inserts
                        tread_mark_insert_batch( stmt+query[:-1])
                        count_inserts = 0
                        query = ''
            # break
        if(query):
            total_inserts += count_inserts
            tread_mark_insert_batch( stmt+query[:-1])

    end =  str(datetime.datetime.now())
        
    return {f"'start': {start}, 'end': {end}"}