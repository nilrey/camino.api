import os
import api.database.dbquery as dbq
import json
from api.lib.func_datetime import *
# import datetime
from sqlalchemy import text
import threading
from sqlalchemy.orm import Session
from api.lib.classResponseMessage import responseMessage


class JsonSaveDB():
    # класс сохранения в базу json ответа от ИНС

    def __init__(self, project_id, dataset_id, dir_json):
        self.message = responseMessage()
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.dir_json = dir_json # директория с файлами json от ИНС
        self.parse_error = False # метка критической ошибки в процессе
        self.query_size = 1000 # количество добавлений в одном блоке insert
        self.start = get_dt_now_noms() # начало работы скрипта
        self.end = '' # окончание работы скрипта
        self.qparams = self.set_new_qparams()


    def set_new_qparams(self)->dict:
        return {
            "project_id" : self.project_id,
            "dataset_id" : self.dataset_id,
            "chain_id" : "",
            "cur_datetime" : get_dt_now(),
            "file_id" : "",
            "author_id" : "",
            "markup_id" : "",
            "markup_path" : ""
        }

    def set_qparams(self):
        self.qparams['chain_id'] = dbq.getUuid()
        self.qparams['file_id'] = self.get_file_id("fc33c712-7b57-11ef-b77b-0242ac140002")
        self.qparams['author_id'] = self.get_author_id()

    def set_markup_id(self, value):
        self.qparams['markup_id'] = value

    def set_markup_path(self, value):
        self.qparams['markup_path'] = value


    def set_error(self, text):
        self.parse_error = True # error mark
        self.message.setError(text)
        

    def reset_error(self):
        self.parse_error = False
        self.message.set('')


    def execute_query(self, connection, stmt):
        try:
            with Session(connection) as session:
                session.execute( text(stmt) )
                session.commit()
        finally:
            # closes the connection, i.e. the socket etc.
            connection.close()


    def tread_insert_batch(self, stmt):
        connection = self.create_connection()
        # detach it! now this connection has nothing to do with the pool.
        connection.detach()
        # pass the connection to the thread.  
        threading.Thread(target=self.execute_query, args=(connection, stmt)).start()

    def create_connection(self):
        # connection from the regular pool
        engine = dbq.create_engine(dbq.get_connection_string())
        return engine.connect()


    def insert_chains_init(self):
        return """INSERT INTO public.chains( id, name, dataset_id, vector, description, author_id, dt_created, 
                        is_deleted, file_id, color, origin_id ) 
                  VALUES """

    def insert_markups_init(self):
        return """INSERT INTO public.markups( id, previous_id, dataset_id, file_id, parent_id, 
                        mark_time, mark_path, vector, description, author_id,  dt_created, is_deleted ) 
                  VALUES """

    def insert_markups_chains_init(self):
        return """INSERT INTO public.markups_chains( chain_id, markup_id, npp ) 
                  VALUES """
    
    def add_markups_values(self):
        return f"(\'{self.qparams['markup_id']}\', null, \'{self.qparams['dataset_id']}\', \'{self.qparams['file_id']}\', null, 99, \'{self.qparams['markup_path']}\', "\
                f" \'{self.qparams['markup_path']}\', \'tread\', \'{self.qparams['author_id']}\', \'{self.qparams['cur_datetime']}\', false)"
    
    def add_markups_chains_values(self):
        return f"(\'{self.qparams['chain_id']}\', \'{self.qparams['markup_id']}\', null)"
    
    def collect_chain_query_values(self, values):
        return f"(\'{values[0]}\',\'{values[1]}\',\'{values[2]}\',\'{values[3]}\',\'{values[4]}\',\'{values[5]}\', "\
            f"\'{values[6]}\', false,\'{values[8]}\',\'{values[9]}\',\'{values[10]}\')"


    def insert_markups_new(self, query_values):
        return self.insert_markups_init() + ",".join(query_values)


    def insert_markups_chains_new(self, query_values):
        return self.insert_markups_chains_init() + ",".join(query_values)
    

    def sequence_insert_markups_markups_chains(self, markups_values, chains_markups_values):
        # создаем последовательность вставки insert, т.к. markups_chains зависит от наличия записи в markups
        self.execute_query( self.create_connection() , self.insert_markups_new(markups_values) ) # args(connection, stms_for_execute)
        self.execute_query( self.create_connection() , self.insert_markups_chains_new(chains_markups_values) )


    def insert_chains_new(self, query_values):
        return self.insert_chains_init()+ ",".join(query_values)


    def get_author_id(self):
        return "a020402a-1cd1-11ef-8883-fb5e6546fceb"
    

    def collect_chain_params(self)->list:
        params = [self.qparams['chain_id'], 'nil_test', self.qparams['dataset_id'], 'vector', 'description', self.qparams['author_id'], self.qparams['cur_datetime'], False, self.qparams['file_id'], '', 1]
        return params
    
    
    def set_insert_chains(self, query_values):
        self.tread_insert_batch( self.insert_chains_new( query_values ) )

    # делаем обход записей блоков files в json , берем значения их chains, для каждого chains сохраняем отдельно все записи 
    # в таблицы: chains (обязательно 1, т.к. есть зависимость в базе) и markups (обязательно 2) и в связующую таблицу markups_chains
    def parse_content(self, content):
        count_values = 0 # values counter
        markups_q_values = [] # список строк со значениями, отформатированных под insert в markups
        chains_markups_q_values = [] # список строк со значениями, отформатированных под insert в chains_markups
        for f in content['files']:
            for chain in f['file_chains'] :
                chain_query_values = []
                # добавляем элемент списка - строка с добавленными параметрами
                # NB - оформить в одтельную функцию получение парамтеров и добавление в список
                self.set_qparams()
                chain_query_values.append(  
                    self.collect_chain_query_values(
                        self.collect_chain_params()
                    )
                )
                # выполняем запрос, перед этим проведя конкатенацию
                self.set_insert_chains(chain_query_values)
                for chains_markups in chain['chain_markups']:
                    self.set_markup_id(chains_markups["markup_id"])
                    self.set_markup_path(json.dumps(chains_markups["markup_path"])) # из json получить markups.markup_path
                    markups_q_values.append(self.add_markups_values()) # добавляем в таблицу markups
                    chains_markups_q_values.append(self.add_markups_chains_values()) # добавляем в таблицу markups_chains
                    count_values += 1
                    break
                break
            break
                    # if(count_values % self.query_size == 0 ): # формируем блок запросов размером = query_size
                    #     threading.Thread(name=self.sequence_insert_markups_markups_chains(markups_q_values, chains_markups_q_values))
                    #     markups_q_values.clear()
                    #     chains_markups_q_values.clear()
        if(len(markups_q_values) > 0): # сохраняем значения из последнего набора, в котором кол-во строк меньше query_size
            threading.Thread(name=self.sequence_insert_markups_markups_chains(markups_q_values, chains_markups_q_values))
        del markups_q_values
        del chains_markups_q_values
        
        return self.message.get()
    

    def load_json(self, filepath):
        content = {}
        with open(filepath, "r") as file:
            try:
                content = json.load(file)
            except Exception as e:
                self.set_error(f"Cannot load json from {file}")
        return content
    
    
    def proceed_file(self, filename):
            content = self.load_json(f"{self.dir_json}/{filename}")
            if( not self.parse_error): # если json файл загружен без ошибок
                self.parse_content(content)  
            else:
                print(self.message.get()) # print error message and go to next file
                self.reset_error()

    
    # обходим список json файлов
    def loop_files(self, files):
        for filename in files:
            threading.Thread(target=self.proceed_file, args=(filename,)).start()
        self.end =  get_dt_now_noms()
        self.message.set(f"Все файлы обработаны. 'start': {self.start}, 'end': {self.end} , "\
                         f"'results' : 'Всего:{len(files)}" )


    # смотрим в директорию, фильтруем по расширению файлов (по умолчанию фильтр пуст)
    def get_files(self, filter = []):
        files = []
        for fl in os.listdir(self.dir_json):
            if os.path.isfile(f'{self.dir_json}/{fl}') :
                f, ext = os.path.splitext(fl)
                if( len(filter) == 0 or ext[1:] in filter ): # ext[1:] точку в начале расширения убираем
                    files.append(fl)
        return files
    

    def get_file_id(self, dataset_id):
        return "1ca4627c-7b58-11ef-b565-0242ac140002"


    def start_parser(self):
        if not os.path.isdir(self.dir_json):
            self.message.setError(f"Ошибка: {self.dir_json} указанная директория не сущестует или не доступна")
        else:
            files = self.get_files(['json'])
            if len(files) == 0 : 
                self.message.setError(f"Ошибка: {self.dir_json} в указанной директории json файлы не найдены")
            else:
                self.loop_files(files)

        return self.message.get()
    

if(__name__ == "__main__"):
    projectId = datasetId = "1ca4627c-7b58-11ef-b565-0242ac140002"
    resp = JsonSaveDB(projectId, datasetId, os.path.dirname(__file__)+'/json/0009')
    res = resp.start_parser()
    print(res)