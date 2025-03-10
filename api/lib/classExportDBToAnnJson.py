import os
import sys
import json
import requests
import threading
import time
import traceback
from sqlalchemy import text
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, text
from configparser import ConfigParser
from collections import defaultdict
from api.lib.func_datetime import *
import api.sets.const as C

import api.manage.manage as mng

class DatasetMarkupsExport:
    # выгрузка данных из БД в json и запуск контейнера из образа 
    def __init__(self, image_id, params): 
        self.data_files = {}
        self.image_id = image_id
        self.params = params
        self.dataset_id = self.params['markups'].split('/')[-2]
        self.project_id = self.params['markups'].split('/')[-3]
        self.status = {}
        self.errors = {}
        self.stop_event = threading.Event()
        self.threads = []
        self.monitor_thread = None
        self.wait_thread = None
        self.output_dir = f"/projects_data/{self.project_id}/{self.dataset_id}/markups_in" # директория с файлами json от ИНС
        self.engine = create_engine(self.get_connection_string())
        self.logname = get_dt_now_noms()+'_datasets_import.log'
        self.files_res = {}


    def log_info(self, mes):
        with open(C.LOG_PATH + f"/{self.logname}", "a") as file:
            file.write(f'{get_dt_now_noms()} {mes}\n')


    def load_config(self, filename='/code/api/database/database.ini', section='postgresql'):
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


    def get_connection_string(self):
        config = self.load_config()
        cs = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        return cs


    def exec_query(self, query, params={}, convert = True):
        with self.engine.connect() as connection:
            result = connection.execute(query, params).mappings().all()
            if(convert):
                res = [self.convert_to_serializable(dict(row)) for row in result]
            else:
                res = result
        return res
    

    def convert_exec_response(self, exec_response):
        result = [self.convert_to_serializable(dict(row)) for row in exec_response]
        return result
    
    @staticmethod
    def convert_to_serializable(obj):
        # Преобразует объекты, которые не поддерживаются JSON (UUID, datetime, Decimal, JSON-строки).
        if isinstance(obj, uuid.UUID):
            return str(obj)  # UUID -> строка
        elif isinstance(obj, datetime):
            return obj.isoformat()  # Дата -> ISO 8601
        elif isinstance(obj, Decimal):
            return float(obj)  # Decimal -> float
        elif isinstance(obj, str):  
            try:
                return json.loads(obj)  # Пробуем распарсить JSON-строку
            except (json.JSONDecodeError, TypeError):
                return obj  # Оставляем как есть, если это не JSON
        elif isinstance(obj, list):  
            return [DatasetMarkupsExport.convert_to_serializable(i) for i in obj]
        elif isinstance(obj, dict):  
            return {k: DatasetMarkupsExport.convert_to_serializable(v) for k, v in obj.items()}
        return obj  # Остальное оставляем без изменений
    

    def prepare_file(self, file_data):
        file = self.convert_to_serializable(dict(file_data)) 
      
        self.log_info(f"file_id: {file['id']}" ) 
        chains = self.prepare_chains(self.dataset_id , file) # [{"id":1}, {"id":2}]
        return {'file_name' : C.CNTR_BASE_01_DIR_IN + '/' + file['name'],
                'file_id' : file['id'],
                'file_subset': 'teach',
                'file_chains' : self.convert_to_serializable(chains),
                }
    

    def prepare_chains(self, dataset_id, file): 
        chains = self.get_chains(dataset_id, file['id'])
        chains_cnt = len(chains)
        markups_cnt = 0
        self.log_info(f'Chains: {chains_cnt}' ) 
        # Заполняем словарь
        for idx, chain in enumerate(chains, start=1): 
            markups = self.get_markups(chain['chain_id']) 
            self.log_info(f"File id:{file['id']}; Chain_id: {chain['chain_id']}; {idx} of {chains_cnt}; Chain markups: {len(markups)})")
            chain["chain_markups"] = markups
            markups_cnt += len(markups)

        self.files_res[file['id']] = {'name': file['name'], 'chains_count':chains_cnt, 'markups_count':markups_cnt }
        return chains


    def get_json_data(self, file_data):
        datasets = self.get_binded_datasets()
        file = self.prepare_file(file_data)
        return {'datasets': datasets, 'files': [file] }
    

    def create_json_file(self, file_data):  
        json_data = self.get_json_data(file_data)

        try:
            os.makedirs(self.output_dir, exist_ok=True)  # Создаем каталог, если его нет
            file_path = os.path.join(self.output_dir, f"IN_{file_data['name']}.json")

            self.log_info(f"путь к файлу: {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False)
                self.message = 'Success'
                # else:
                #     self.message = 'Error: dataset_parent_id is not found '

            self.status[file_data['name']] = "Success"
            self.log_info(f"{file_data['name']} is success done. ")
        except Exception as e:
            self.status[file_data['name']] = "Failed"
            self.errors[file_data['name']] = traceback.format_exc()
            self.log_info(self.status[file_data['name']])
            self.log_info(self.errors[file_data['name']])

    def monitor_threads(self):
        # Менеджер потоков - для отслеживания состояния других потоков
        while not self.stop_event.is_set():
            all_finished = True
            for filename, state in list(self.status.items()):
                if state not in ["Success", "Failed"]:
                    #self.log_info(f'Error: state not in Success or Failed: {state}')
                    all_finished = False
                elif state is not None:
                    #print(f"{state} - {filename}")
                    self.status[filename] = None  # Чтобы не дублировать вывод
            
            if all_finished:
                self.stop_event.set()
                break  

        #print("\nSummary:")
        for filename, state in self.status.items():
            if state is None:
                state = "Success"
            self.log_info(f"{filename}: {state}")

        if self.errors:
            self.log_info("\nErrors:")
            for filename, error in self.errors.items():
                self.log_info(f"{filename} failed with error:\n{error}")

    def wait_for_threads(self):
        # Ожидание завершения всех потоков. 
        for thread in self.threads:
            thread.join()
        self.stop_event.set()
        self.monitor_thread.join()
        self.log_info("Работа с файлами закончена") 
        self.close_idle()
        # self.log_info(self.files_res)
        # print("Работа с файлами закончена.", file=sys.stderr)
        try:
            url = f"{C.HOST_RESTAPI}/projects/{self.project_id}/datasets/{self.dataset_id}/on_export" 
            self.log_info(f'prepare Url on_export: {url}')
            files_post = list(self.files_res.values())
            self.log_info(f'Данные отправленные on_export "files": {files_post}')
            headers = { "Content-Type": "application/json" }
            data = { "files": files_post }

            response = requests.post(url, json=data, headers=headers) 
            self.log_info(f'on_export response: {response}')
        except Exception as e:
            self.log_info(f'on_export response error: {e}')
        
        # START DOCKER CREATE CONTAINER
        self.log_info('Начало запуска контейнера')
        res = mng.mng_image_run2(self.image_id, self.params)
        self.log_info('Окончание запуска контейнера. Результат')
        self.log_info(res)

    def run(self):
        self.log_info("Start process")
        self.data_files = self.get_dataset_files(self.dataset_id)
        self.log_info(f'Files found: {len(self.data_files)} ')
        self.status = {filename["name"]: "In Progress" for filename in self.data_files}
        # print(f"{resp[0]['id']}", file=sys.stderr)
        # Запуск потоков создания файлов
        for file in self.data_files:
            thread = threading.Thread(target=self.create_json_file, args=(file,))
            thread.start()
            self.threads.append(thread)

        # Запуск мониторинга
        self.monitor_thread = threading.Thread(target=self.monitor_threads)
        self.monitor_thread.start()

        # Запуск ожидания завершения в отдельном потоке
        self.wait_thread = threading.Thread(target=self.wait_for_threads)
        self.wait_thread.start()
        files_count = len(self.data_files)
        message = {'message': 'Файлы отправлены в обработку', 'files_count' : {files_count} }
        self.log_info( f'Response json: {message} ' )
        
        return message

    def get_dataset_files(self, dataset_id):
        # получим корневой dataset id
        stmt = text("SELECT d2.id FROM datasets d1 , datasets d2 where d1.project_id = d2.project_id and d2.parent_id is null and d1.id = :dataset_id")
        parent_dataset_id = self.exec_query(stmt, {"dataset_id" : dataset_id } )
        self.log_info(f'dataset_id = {dataset_id}')
        if(parent_dataset_id):
            self.log_info(f'parent_dataset_id = {parent_dataset_id[0]["id"]}')
            stmt = text("SELECT * FROM files f  WHERE f.dataset_id = :dataset_id AND f.is_deleted = false")
            files = self.exec_query(stmt, {"dataset_id" : parent_dataset_id[0]['id']} , False)
        else:
            self.log_info(f'Error: parent_dataset_id is null')
            files = []
        #print(f"{resp}", file=sys.stderr)
        return files
    
    def stmt_chains(self):
        return text("""SELECT c.id as chain_id, c.name as chain_name, c.vector as chain_vector 
                    FROM chains c WHERE c.dataset_id = :dataset_id AND c.file_id = :file_id AND c.is_deleted = false""")
        
    def get_chains(self, dataset_id, file_id):
        chains = self.exec_query( self.stmt_chains(), {'dataset_id':dataset_id, 'file_id': file_id})
        return chains

    def stmt_markups(self):
        return text("""
            SELECT m.id as markup_id, m.mark_frame as markup_frame, m.mark_time as markup_time, m.vector as markup_vector, m.mark_path as markup_path 
            FROM markups_chains mc
            JOIN markups m ON mc.markup_id = m.id 
            WHERE mc.chain_id = :chain_id
            AND m.is_deleted = false
            AND NOT EXISTS (
                SELECT 1 FROM markups m2 WHERE m2.previous_id = m.id 
            )
        """)
        
    def get_markups(self, chain_id):
        markups = self.exec_query( self.stmt_markups(), {"chain_id": chain_id })
        # self.log_info(f'markups: {len(markups)}')
        return markups
    

    def stmt_binded_datasets(self):
        return text("""
            WITH RECURSIVE dataset_hierarchy AS (
                SELECT id as dataset_id, parent_id as dataset_parent_id, name as dataset_name, type_id as dataset_type
                FROM public.datasets
                WHERE id = :dataset_id
                UNION ALL
                SELECT d.id as dataset_id, d.parent_id as dataset_parent_id, d.name, d.type_id
                FROM public.datasets d
                JOIN dataset_hierarchy dh ON d.id = dh.dataset_parent_id
            )
            SELECT * FROM dataset_hierarchy;
        """)

    def get_binded_datasets(self):
        datasets = self.exec_query( self.stmt_binded_datasets(), {"dataset_id": self.dataset_id }) 
        return datasets
    
    
    def close_idle(self):
        stmt = text('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = \'idle\' AND pid <> pg_backend_pid()')
        self.exec_query(stmt, {}, True)
        return True 