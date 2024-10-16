import os
import api.database.dbquery as dbq
import json
import datetime
from sqlalchemy import text
import threading
from sqlalchemy.orm import Session
from api.lib.classResponseMessage import responseMessage


class JsonSaveDB():
    # класс сохранения в базу json ответа от ИНС

    def __init__(self, dir_json):
        self.message = responseMessage()
        self.dir_json = dir_json # директория с файлами json от ИНС
        self.parse_error = False # метка критической ошибки в процессе
        self.query_size = 1000 # количество добавлений в одном блоке insert
        self.start = str(datetime.datetime.now()) # начало работы скрипта
        self.end = '' # окончание работы скрипта

    def setError(self, text):
        self.parse_error = True # error mark
        self.message.setError(text)\
        

    def resetError(self):
        self.parse_error = False
        self.message.set('')


    def thread_runner_batch(self, connection, stmt):
        try:
            with Session(connection) as session:
                session.execute( text(stmt) )
                session.commit()
        finally:
            # closes the connection, i.e. the socket etc.
            connection.close()


    def tread_insert_batch(self, stmt):
        # connection from the regular pool
        engine = dbq.create_engine(dbq.get_connection_string())
        connection = engine.connect()
        # detach it! now this connection has nothing to do with the pool.
        connection.detach()
        # pass the connection to the thread.  
        threading.Thread(target=self.thread_runner_batch, args=(connection, stmt)).start()

    def insert_chains_init(self):
        return """INSERT INTO public.chains( id, name ) 
                  VALUES """

    def insert_markups_init(self):
        return """INSERT INTO public.markups( id, previous_id, dataset_id, file_id, parent_id, 
                        mark_time, mark_path, vector, description, author_id,  dt_created, is_deleted ) 
                  VALUES """

    def insert_markups_chains_init(self):
        return """INSERT INTO public.markups_chains( chain_id, markup_id, npp ) 
                  VALUES """
    
    def add_markups_values(self, values):
        return f"(\'{values[0]}\', null, null, null, null, 99, \'{values[1]}\', \'{values[1]}\', \'tread\', "\
                f"null, \'2024-10-08 12:42:00\', false)"
    
    def add_chain_markup_values(self, values):
        return f"(\'{values[0]}\', \'{values[1]}\', null)"
    
    def add_chain_values(self, values):
        return f"(\'{values[0]}\', \'test\')"


    def insert_markups_new(self, query_values):
        return self.insert_markups_init() + ",".join(query_values)


    def insert_markups_chains_new(self, query_values):
        return self.insert_markups_chains_init() + ",".join(query_values)


    def insert_chains_new(self, query_values):
        return self.insert_chains_init() + query_values
    
    def set_insert_chains(self, chain_id):
        self.tread_insert_batch( self.insert_chains_new( self.add_chain_values([chain_id]) ))

    # делаем обход записей блоков files в json , берем значения их chains, для каждого chains сохраняем отдельно все записи 
    # в таблицы: chains (обязательно 1, т.к. есть зависимость в базе) и markups и в связующую таблицу markups_chains
    def ann_out_db_save(self, content):
        count_values = 0 # values counter
        markups_values = []
        chains_markups_values = []
        for f in content['files']:
            file_id = dbq.getUuid()
            for chain in f['file_chains'] :
                chain_id = dbq.getUuid()
                self.set_insert_chains(chain_id)
                for chains_markups in chain['chain_markups']:
                    mdata = json.dumps(chains_markups["markup_path"]) # json в колонку markups.mark_path
                    markup_id = dbq.getUuid()
                    markups_values.append(self.add_markups_values([markup_id, mdata, file_id])) # добавляем в таблицу markups
                    chains_markups_values.append(self.add_chain_markup_values([chain_id, markup_id]))# добавляем в таблицу markups_chains
                    count_values += 1 
            #         break
            #     break
            # break
                    if(count_values % self.query_size == 0 ): # формируем блок запросов размером = query_size
                        self.tread_insert_batch( self.insert_markups_new(markups_values))
                        self.tread_insert_batch( self.insert_markups_chains_new(chains_markups_values))
                        markups_values.clear()
                        chains_markups_values.clear()
        if(len(markups_values) > 0): # сохраняем значения из последнего набора, в котором кол-во строк меньше query_size
            self.tread_insert_batch( self.insert_markups_new(markups_values))
            self.tread_insert_batch( self.insert_markups_chains_new(chains_markups_values))
        
        return self.message.get()
    

    def load_json(self, filepath):
        content = {}
        with open(filepath, "r") as file:
            try:
                content = json.load(file)
            except Exception as e:
                self.setError(f"Cannot load json from {file}")
        return content
    
    def tread_file(self, filename, id):
            content = self.load_json(f"{self.dir_json}/{filename}")
            if( not self.parse_error): # если json файл загружен без ошибок
                self.ann_out_db_save(content) # оформить в поток
                # threading.Thread(target=self.ann_out_db_save, args=(content)).start()
            else:
                print(self.message.get()) # print error message and go to next file
                self.resetError()

    
    # обходим список json файлов
    def loop_files(self, files):
        for filename in files:
            threading.Thread(target=self.tread_file, args=(filename, "1234")).start()
        self.end =  str(datetime.datetime.now())
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


    def start_parser(self):
        if not os.path.isdir(self.dir_json):
            self.message.setError("Ошибка: указанная директория не сущестует или не доступна")
        else:
            files = self.get_files(['json'])
            if len(files) == 0 : 
                self.message.setError("Ошибка: в указанной директории json файлы не найдены")
            else:
                self.loop_files(files)
                # self.message.set("Файлы запущены в обработку")

        return self.message.get()
    

if(__name__ == "__main__"):
    resp = JsonSaveDB(os.path.dirname(__file__)+'/json/0009')
    res = resp.start_parser()
    print(res)