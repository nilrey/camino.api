import os
import sys
import api.database.dbquery as dbq
import json
from api.lib.func_datetime import *
# import datetime
from sqlalchemy import text
import threading
from sqlalchemy.orm import Session
from api.lib.classResponseMessage import responseMessage


class ParseJsonToDB():
    # класс сохранения в базу json ответа от ИНС

    def __init__(self, project_id, dataset_id, files):
        self.message = responseMessage()
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.dir_json = f"/projects_data/{project_id}/{dataset_id}/markups_out" # директория с файлами json от ИНС
        self.files = files # массив названий файлов для обработки
        self.parse_error = False # метка критической ошибки в процессе
        self.query_size = 1000 # количество добавлений в одном блоке insert
        self.start = get_dt_now_noms() # начало работы скрипта
        self.end = '' # окончание работы скрипта
        self.qparams = self.set_new_qparams()
        self.color_set = {
            "olivedrab" : "6b8e23",
            "sienna" : "a0522d",
            "lime" : "00ff00",
            "lightslategray" : "778899",
            "mediumspringgreen" : "00fa9a",
            "navy" : "000080",
            "aqua" : "00ffff",
            "red" : "ff0000",
            "orange" : "ffa500",
            "yellow" : "ffff00",
            "blue" : "0000ff",
            "fuchsia" : "ff00ff",
            "dodgerblue" : "1e90ff",
            "deeppink" : "ff1493",
            "moccasin" : "ffe4b5"
        }


    def set_new_qparams(self)->dict:
        return {
            "project_id" : self.project_id,
            "dataset_id" : self.dataset_id,
            "file_id" : "",
            "chain_id" : "",
            "chain_orig_id" : "",
            "cur_datetime" : get_dt_now(),
            "author_id" : "",
            "markup_id" : "",
            "markup_path" : "",
            "markup_time" : ""
        }

    def set_error(self, text):
        self.parse_error = True # error mark
        self.message.setError(text)
        

    def reset_error(self):
        self.parse_error = False
        self.message.set('')

    
    def getValueIfExists(self, key, lst, value = 'null'):
        if( key in lst.keys() ):
            value = f"'{lst[key]}'"
        return value

    
    def get_file_id_by_name(self, fname):
        # получим корневой dataset id
        stmt = text("SELECT d2.id FROM datasets d1 , datasets d2 where d1.project_id = d2.project_id and d2.parent_id is null and d1.id = :dataset_id")
        dataset_id = dbq.select_wrapper(stmt, {"dataset_id" : self.dataset_id } )

        stmt = text("SELECT f.id FROM files f  WHERE f.dataset_id = :dataset_id and f.label = :fname")
        lable = fname.replace('.mp4', '').replace('.json', '')
        # print(f"{lable}", file=sys.stderr)
        resp = dbq.select_wrapper(stmt, {"dataset_id" : dataset_id[0]['id'], "fname" : lable} )
        # print(f"{resp[0]['id']}", file=sys.stderr)
        return resp[0]['id'] 
    

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

    def get_foo_vector(self):
        return '["0.116042", "-4.554680", "-1.862837", "-5.750429", "-0.454754", "-2.522960", "-0.725157", "-2.806483", "-1.563497", "-0.694797", "-1.983297", "-4.366373", "-0.981786", "-2.109066", "-2.173160", "-1.538690", "-2.162211", "-2.810481", "-0.770217", "1.129247", "-0.384295", "-0.289850", "-1.706230", "-0.026655", "-0.698680", "1.391937", "-1.128524", "-1.699184", "0.197050", "0.225844", "-0.365390", "2.624454", "2.205503", "1.234172", "-1.713398", "-3.221918", "1.048727", "-1.720429", "-2.609614", "-2.234915", "-4.320556", "-2.607154", "-1.494452", "-1.427774", "-2.968949", "-1.121514", "-1.350918", "-0.859946", "-2.248292", "-1.855603", "1.431867", "0.304567", "-0.512907", "1.236301", "-2.602892", "0.600495", "-2.790122", "-0.993832", "2.530886", "2.251848", "0.995347", "4.317902", "0.190066", "0.455789", "0.682259", "2.780439", "0.859293", "2.811572", "0.836380", "2.156464", "0.677944", "0.894499", "-0.453031", "-1.520394", "0.666892", "2.303484", "2.592246", "1.484719", "2.274570", "1.714708", "0.851308", "3.679554", "-0.699476", "3.236506", "-0.936165", "0.507164", "1.695917", "0.269416", "5.602341", "1.637749", "1.132531", "0.271580", "-1.023239", "-1.201301", "-1.423335", "0.536225", "0.958369", "1.957854", "1.889585", "2.588964", "4.553710", "2.008711", "1.172196", "2.801171", "-2.838225", "1.539892", "3.385830", "-0.094048", "1.673603", "-0.197045", "-1.177830", "-0.428138", "3.139174", "0.404254", "1.924672", "0.748128", "-1.099999", "1.641606", "-1.094444", "-4.832273", "-2.495924", "-1.822001", "-2.580733", "-1.281448", "0.461648", "2.656320", "-3.874641", "0.379173"]'

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
    
    def add_markups_values(self, mp):
        return f"(\'{mp['id']}\', null, \'{mp['dataset_id']}\', \'{mp['file_id']}\', {mp['parent_id']}, {mp['mark_time']}, \'{mp['mark_path']}\', \'{mp['vector']}\', \'{mp['description']}\', \'{mp['author_id']}\', \'{mp['dt_created']}\', false)"
    
    def add_markups_chains_values(self, chain_id, markup_id):
        return f"(\'{chain_id}\', \'{markup_id}\', 12345)"
    
    def collect_chain_query_values(self, cp):
        return f"(\'{cp['id']}\', \'{cp['name']}\', \'{cp['dataset_id']}\', \'{cp['vector']}\', \'{cp['description']}\', \'{cp['author_id']}\', \'{cp['dt_created']}\', false, \'{cp['file_id']}\', \'{cp['color']}\', {cp['origin_id']})"


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
        # comment from Ura - take author_id from table datasets by dataset_id
        return "a020402a-1cd1-11ef-8883-fb5e6546fceb"
    
    
    def set_insert_chains(self, query_values):
        self.tread_insert_batch( self.insert_chains_new( query_values ) )

    def set_params(self)->dict:
        return {"file_id" : "",
                "dt_created" : get_dt_now(),
                "author_id" : self.get_author_id(),
                "chain_uuid":"",
                "chain_name":""
                }
    
    
    # def prepare_chain_params(self, params, chain)->dict:
    #     return {"id" : params["chain_uuid"], "name" : chain["chain_name"], "dataset_id" : self.dataset_id, "vector" : json.dumps(chain["chain_vector"]), 
    #                 "description" : "ann_output_json", "author_id" : params['author_id'], "dt_created" : params['dt_created'], 
    #                 "is_deleted" : False, "file_id" : params["file_id"], "color" : "", "origin_id" : "1"
    #             }
    
    
    def prepare_chain_params(self, params, chain)->dict:
        return {"id" : params["chain_uuid"], "name" : chain["chain_name"], "dataset_id" : self.dataset_id, "vector" : json.dumps(self.get_foo_vector()), 
                    "description" : "ann_output_json", "author_id" : params['author_id'], "dt_created" : params['dt_created'], 
                    "is_deleted" : False, "file_id" : params["file_id"], "color" : "", "origin_id" : "1"
                }
    
    # def prepare_markup_params(self, params, cm)->dict:
    #     return {"id" : cm['markup_id'], "previous_id" : '', "dataset_id" : self.dataset_id, "file_id" : params["file_id"], 
    #                 "parent_id" : cm['markup_parent_id'], "mark_time" : cm['markup_time'], "mark_path" : json.dumps(cm["markup_path"]), 
    #                 "vector" : json.dumps(cm["markup_vector"]), "description" : "ann_output_json", "author_id" : params['author_id'], 
    #                 "dt_created" : params['dt_created'], "is_deleted" : False 
    #             }
    
    def prepare_markup_params(self, params, cm)->dict:
        return {"id" : cm['markup_id'], "previous_id" : '', "dataset_id" : self.dataset_id, "file_id" : params["file_id"], 
                    "parent_id" : cm['markup_parent_id'], "mark_time" : cm['markup_time'], "mark_path" : json.dumps(cm["markup_path"]), 
                    "vector" : json.dumps(self.get_foo_vector()), "description" : "ann_output_json", "author_id" : params['author_id'], 
                    "dt_created" : params['dt_created'], "is_deleted" : False 
                }
    

    # делаем обход записей блоков files в json , берем значения их chains, для каждого chains сохраняем отдельно все записи 
    # в таблицы: chains (обязательно 1, т.к. есть зависимость в базе) и markups (обязательно 2) и в связующую таблицу markups_chains
    def parse_content(self, content, filename):
        params = self.set_params()
        counter = 0 
        markups_q_values = [] # список строк со значениями, отформатированных под insert в markups
        chains_markups_q_values = [] # список строк со значениями, отформатированных под insert в chains_markups
        for f in content['files']:
            params['file_id'] = self.get_file_id_by_name(filename)
            for chain in f['file_chains'] :
                chain_query_values = []
                # chain['chain_id'] = self.getValueIfExists("chain_id", chain)
                params["chain_uuid"] = dbq.getUuid(counter)
                params['dt_created'] = get_dt_now()
                # добавляем элемент списка - строка с добавленными параметрами
                chain_query_values.append(
                    self.collect_chain_query_values(
                        self.prepare_chain_params(params, chain)
                    )
                )
                # выполняем запрос, перед этим проведя конкатенацию
                self.set_insert_chains(chain_query_values)
                for cm in chain['chain_markups']:
                    params['dt_created'] = get_dt_now()
                    cm['markup_id'] = dbq.getUuid(counter)
                    cm['markup_parent_id'] = self.getValueIfExists("markup_parent_id", cm)
                    markups_q_values.append(
                        self.add_markups_values(
                            self.prepare_markup_params(params, cm)# добавляем строку в список markups_q_values
                        )
                    ) 
                    chains_markups_q_values.append(self.add_markups_chains_values(params["chain_uuid"], cm['markup_id'])) # добавляем в таблицу markups_chains
                    counter += 1
                    if(counter % self.query_size == 0 ): # формируем блок запросов размером = query_size
                        threading.Thread(name=self.sequence_insert_markups_markups_chains(markups_q_values, chains_markups_q_values))
                        markups_q_values.clear()
                        chains_markups_q_values.clear()
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
            # self.set_file_id(filename)
            content = self.load_json(f"{self.dir_json}/{filename}")
            if( not self.parse_error): # если json файл загружен без ошибок
                self.parse_content(content, filename)  
            else:
                print(self.message.get()) # print error message and go to next file
                self.reset_error()

    
    # обходим список json файлов
    def loop_files(self, files):
        errFiles = []
        for filename in files:
            if os.path.isfile(f'{self.dir_json}/{filename}') :
                threading.Thread(target=self.proceed_file, args=(filename,)).start()
            else:
                errFiles.append(filename)
        if len(errFiles) > 0 :
            self.message.setError("Ошибка: "+(",".join(errFiles) )+" не найден")
        else:
            self.message.set(f"Файлы отправлены в обработку. Всего: {len(files)}" )
        
        self.end =  get_dt_now_noms()


    # смотрим в директорию, фильтруем по расширению файлов (по умолчанию фильтр пуст - берем все файлы)
    # формат фильтра - последовательность названий расширений, например: ["json", "txt", "xml"]
    # def get_files(self, filter = []):
    #     # сфорируем список из названий json файлов
    #     files = []
    #     for fl in os.listdir(self.dir_json):
    #         #print(f'{self.dir_json}/{fl}', file=sys.stderr)
    #         if os.path.isfile(f'{self.dir_json}/{fl}') :
    #             f, ext = os.path.splitext(fl)
    #             if( len(filter) == 0 or ext[1:] in filter ): # ext[1:] точку в начале расширения убираем
    #                 files.append(fl)
    #     return files


    def start_parser(self):
        # проведем проверку: доступ к директории, наличие файлов json
        if not os.path.isdir(self.dir_json):
            self.message.setError(f"Ошибка: {self.dir_json} указанная директория не сущестует или не доступна")
        else:
            files = self.files #self.get_files(['json'])
            if len(files) == 0 : 
                self.message.setError(f"Ошибка: получен пустой список json файлов")
            else:
                self.loop_files(files)

        return self.message.get()
    

if(__name__ == "__main__"):
    projectId = datasetId = "fc33c712-7b57-11ef-b77b-0242ac140002"
    parser = ParseJsonToDB(projectId, datasetId, os.path.dirname(__file__)+'/json/0009')
    res = parser.start_parser()
    print(res)