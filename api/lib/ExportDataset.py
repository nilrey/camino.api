import os
import sys
import json
import requests
import threading
import time
import traceback
import shutil
# from pathlib import Path
from sqlalchemy import text
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import create_engine, text
from configparser import ConfigParser
from api.utils.datetime import *
import api.settings.config as C
from api.services import docker_services 
from  api.services.logger import LogManager
from concurrent.futures import ThreadPoolExecutor 


class DatasetMarkupsExport:
    # выгрузка данных из БД в json и запуск контейнера из образа 
    # В результате работы get_binded_datasets, получим:
    # dataset_id - текущий датасет, в случае ИНС - тот в пространстве которого будет работать ИНС - загрузка данных из markups_in, выгрузка в markups_out
    # parent_dataset_id - родительский датасет текущего датасета, с этим параметром идет запрос в БД на выгрузку chains & markups
    # init_dataset_id - начальный датасет, к которому идет привязка видео файлов 

    BATCH_SIZE = 10
    DATASET_STATE_PROCEED = 1
    
    def __init__(self, exp_params, img_params): 
        self.params = exp_params
        self.img_params = img_params
        self.image_id = self.img_params.get('image_id', None)
        self.dataset_id = self.params['dataset_id']
        self.datasets = []
        self.project_id = None # self.get_param_project_id(self.params, self.img_params)
        self.parent_dataset_id = None
        self.init_dataset_id = None
        self.only_verified_chains = self.params.get('only_verified_chains', False)
        self.only_selected_files = self.params.get('only_selected_files', [])        
        self.time_start = time.time()
        self.time_end = time.time()
        self.monitor_thread = None
        self.wait_thread = None
        self.output_dir = ''
        self.ann_output_dir = ''
        self.engine = create_engine(self.get_connection_string())
        self.logname = get_dt_now_noms()+'_db_export_json.log'
        self.data_files = {}
        # self.status = {}
        self.errors = {}
        self.files_res = {}
        self.stop_event = threading.Event()
        self.threads = []
        self.dataset_state = -1
        self.do_stop_export = False
        self.logger = LogManager("export_json")    

    def get_param_dataset_id(self, params, img_params):
        if ( img_params.get('markups', None)):
            resp = img_params['markups'].split('/')[-2]
        else:
            resp = params.get('dataset_id', None)
        return resp

    def get_param_project_id(self, params, img_params):
        if ( img_params.get('markups', None)):
            resp = img_params['markups'].split('/')[-3]
        else:
            resp = params.get('project_id', None)
        return resp

    def get_param_output_dir(self, params, output_dir):
        if ( params.get('target_dir', None)):
            output_dir = params['target_dir']
        self.output_dir = output_dir 


    def load_config(self, filename=C.POSTGRES_CONNECT, section='postgresql'):
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
      
        self.logger.info(f"file_id: {file['id']}" ) 
        chains = self.prepare_chains(file) # [{"id":1}, {"id":2}]
        return {'file_name' : file['name'],
                'file_id' : file['id'],
                'file_subset': 'teach',
                'file_chains' : self.convert_to_serializable(chains),
                }
    
    def check_dataset_state(self):
        try:
            dataset_state = self.exec_query(self.stmt_dataset_state(), {"dataset_id":self.dataset_id} )
            self.dataset_state = dataset_state[0]["state_id"]
            self.logger.info(f'Dataset state: {self.dataset_state}')
            if self.dataset_state != self.DATASET_STATE_PROCEED :
                self.do_stop_export = True
                
        except Exception as e:
            self.logger.info(f'ОШИБКА: Dataset state: {e}')

    def prepare_chains(self, file): 
        # при экспорте без запуска ИНС нужно брать chains из текущего датасета
        # в случае если идет запуск ИНС берем из родительского датасета (текущий датасет еще не имеет записей)
        chains = self.get_chains(self.parent_dataset_id if self.image_id else self.dataset_id , file['id'])
        chains_cnt = len(chains)
        markups_cnt = 0
        self.logger.info(f'Chains: {chains_cnt}' ) 
        # Заполняем словарь
        for idx, chain in enumerate(chains, start=1): 
            if( idx > 0 and idx % self.BATCH_SIZE == 0):
                # проверим в базе данных метку на прерывание процесса выгрузки для dataset_id
                self.check_dataset_state()
                if self.do_stop_export :
                    break

            markups = self.get_markups(chain['chain_id']) 
            self.logger.info(f"File id:{file['id']}; Chain_id: {chain['chain_id']}; {idx} of {chains_cnt}; Chain markups: {len(markups)})")
            chain["chain_markups"] = markups
            markups_cnt += len(markups)

        self.files_res[file['id']] = {'name': file['name'], 'file_id': file['id'], 'chains_count':chains_cnt, 'markups_count':markups_cnt }
        return chains


    def get_json_data(self, file_data):
        # datasets = self.get_binded_datasets()
        file = self.prepare_file(file_data)
        return {'datasets': self.datasets, 'files': [file] }
    

    def create_json_file(self, file_data):  
        json_data = self.get_json_data(file_data)

        # Если обнаружен сигнал о прерывании - остановить выгрузку
        if self.do_stop_export :
            mes = f'Получен сигнал в БД на прерывание процесса выгрузки self.dataset_state: {self.dataset_state}.'
            self.status[file_data['name']] = "Failed"
            self.errors[file_data['name']] = mes
            self.logger.info(mes)
        else:
            try:
                os.makedirs(self.output_dir, exist_ok=True)  # Создаем каталог, если его нет
                file_path = os.path.join(self.output_dir, f"IN_{file_data['name']}.json")

                self.logger.info(f"путь к файлу: {file_path}")
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False)
                    self.message = 'Success'
                if os.path.isfile(file_path) :
                    self.status[file_data['name']] = "Success"
                    self.logger.info(f"{file_data['name']} файл успешно создан. ")
                else:
                    self.status[file_data['name']] = "Failed"
                    self.logger.info(f"{file_data['name']} файл не создан. ")

            except Exception as e:
                self.status[file_data['name']] = "Failed"
                self.errors[file_data['name']] = traceback.format_exc()
                self.logger.info(self.status[file_data['name']])
                self.logger.info(self.errors[file_data['name']])

    def monitor_threads(self):
        # Менеджер потоков - для отслеживания состояния других потоков
        while not self.stop_event.is_set():
            all_finished = True
            for filename, state in list(self.status.items()):
                if state not in ["Success", "Failed"]: 
                    all_finished = False
                elif state is not None: 
                    self.status[filename] = None  # Чтобы не дублировать вывод
            
            if all_finished:
                self.stop_event.set()
                break  

        #print("\nSummary:")
        for filename, state in self.status.items():
            if state is None:
                state = "Success"
            self.logger.info(f"{filename}: {state}")

        if self.errors:
            self.logger.info("Errors while files proceed:")
            for filename, error in self.errors.items():
                self.logger.info(f"{filename} failed with error: {error}")

    def wait_for_threads(self):
        # Ожидание завершения всех потоков. 
        for thread in self.threads:
            thread.join()
        self.stop_event.set()
        self.monitor_thread.join()
        self.after_export_done()

    def after_export_done(self):
        # создаем симлинки для pkl файлов из директории dataset_parent_id, только если родительский датасет не является начальным
        if self.parent_dataset_id != self.init_dataset_id :
            self.create_simlinks()
        self.logger.info("Работа с файлами закончена")
        self.send_on_export()

        if self.do_stop_export : 
            self.logger.info('Запуск контейнера отменен')        
        elif(self.image_id): # Используем наличие image_id, в качестве признака запуска контейнера
            # DOCKER RUN CONTAINER
            self.before_container_run()
            self.logger.info('Начало запуска контейнера')
            res =  docker_services.create_start_container(self.img_params)
            self.logger.info(f'Результат запуска контейнера: {res}')

    def send_on_export(self):
        try:
            # /export/on_error
            ds_id = self.img_params.get('dataset_id', self.dataset_id)
            url = f"{C.HOST_RESTAPI}/projects/{self.project_id}/datasets/{ds_id}/on_export" 
            self.logger.info(f'prepare Url on_export: {url}')
            files_post = list(self.files_res.values())
            self.logger.info(f'Данные отправленные on_export "files": {files_post}')
            headers = { "Content-Type": "application/json" }
            data = { "files": files_post }

            response = requests.post(url, json=data, headers=headers) 
            self.logger.info(f'on_export response: {response}')
        except Exception as e:
            self.logger.info(f'on_export response error: {e}')
        finally:
            self.logger.info(f'Выгрузка данных из БД в Json закончена.')

        
    def before_container_run(self):
            self.logger.info('Удаление директории "markups_out"')
            self.clear_directory(self.ann_output_dir)
            self.logger.info('Создание директории "markups_out" перед запуском контейнера')
            os.makedirs(self.ann_output_dir, exist_ok=True)


    def get_dataset_files(self, init_dataset_id): 
        self.logger.info(f'get_dataset_files: init_dataset_id = {init_dataset_id}')
        if(init_dataset_id):
            stmt = text("SELECT * FROM files f  WHERE f.dataset_id = :dataset_id AND f.is_deleted = false")
            files = self.exec_query(stmt, {"dataset_id" : init_dataset_id})
            self.logger.info(f'найдено всех файлов корневого датасета = {len(files)}')
            # проверка на only_selected_files
            # self.logger.info(files)
            if(len(self.only_selected_files) > 0 ):
                self.logger.info("начата фильтрация по only_selected_files")
                files = [f for f in files if f['id'] in self.only_selected_files] 
                        
        else:
            self.logger.info(f'Error: parent_dataset_id is null')
            files = []
        #print(f"{resp}", file=sys.stderr)
        return files
    
    def stmt_chains(self):
        return text("""SELECT c.id as chain_id, c.name as chain_name, c.vector as chain_vector , c.confidence as chain_confidence 
                    FROM chains c WHERE c.dataset_id = :dataset_id AND c.file_id = :file_id AND c.is_deleted = false """)
    
    def stmt_chains_verified(self):
        return text("""SELECT c.id as chain_id, c.name as chain_name, c.vector as chain_vector , c.confidence as chain_confidence 
                    FROM chains c WHERE c.dataset_id = :dataset_id AND c.file_id = :file_id AND c.is_deleted = false AND is_verified = true """)
        
    def get_chains(self, dataset_id, file_id):
        stmt = self.stmt_chains()
        params = {'dataset_id': dataset_id, 'file_id': file_id}
        self.logger.info(f"Get chains query params: {params}")
        if (self.only_verified_chains):
            stmt = self.stmt_chains_verified()

        chains = self.exec_query( stmt, params)
        return chains

    def stmt_markups(self):
        return text("""
            SELECT m.id as markup_id, m.mark_frame as markup_frame, m.mark_time as markup_time, m.vector as markup_vector, m.parent_id as markup_parent_id, m.mark_path as markup_path, m.confidence as markup_confidence 
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
        # self.logger.info(f'markups: {len(markups)}')
        return markups
    

    def stmt_binded_datasets(self):
        return text("""
            WITH RECURSIVE dataset_hierarchy AS (
                SELECT id as dataset_id, parent_id as dataset_parent_id, name as dataset_name, type_id as dataset_type, project_id
                FROM public.datasets
                WHERE id = :dataset_id
                UNION ALL
                SELECT d.id as dataset_id, d.parent_id as dataset_parent_id, d.name, d.type_id, d.project_id
                FROM public.datasets d
                JOIN dataset_hierarchy dh ON d.id = dh.dataset_parent_id
            )
            SELECT * FROM dataset_hierarchy;
        """)

    def stmt_dataset_state(self):
        return text("""SELECT state_id FROM datasets where id = :dataset_id""")
    

    def get_binded_datasets(self):
        self.datasets = self.exec_query( self.stmt_binded_datasets(), {"dataset_id": self.dataset_id })
        self.logger.info(f"datasets: {self.datasets}")


    def set_datasets_hierarchy(self):
        if (len(self.datasets) > 0):
            for dataset in self.datasets:
                if (self.dataset_id == dataset['dataset_id']):
                    self.parent_dataset_id = dataset['dataset_parent_id']
                    self.project_id = dataset['project_id']
                    if(dataset['dataset_parent_id'] == None): # если текущий датасет является начальным, т.е. у него нет parent & init 
                        self.parent_dataset_id = dataset['dataset_id']
                        self.init_dataset_id = dataset['dataset_id']
                elif(dataset['dataset_parent_id'] == None):
                    self.init_dataset_id = dataset['dataset_id']


    def close_idle(self):
        stmt = text('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = \'idle\' AND pid <> pg_backend_pid()')
        self.exec_query(stmt, {}, True)
        return True 


    def clear_directory(self, dir):
        if ( not os.path.exists(dir)):
            self.logger.info(f"Удаление директории. Директория не существует: '{dir}'")
        else:
            shutil.rmtree(dir)
            if ( not os.path.exists(dir)):
                self.logger.info(f"Удаление директории. Директория удалена: '{dir}'")
            else:
                self.logger.info(f"Удаление директории. Ошибка: директория не удалена: '{dir}'")
        # создаем директорию снова уже пустую
        os.makedirs(dir, exist_ok=True) 


    def create_simlinks(self):
        try:
            source_dir = f"/projects_data/{self.project_id}/{self.parent_dataset_id}/markups_out"
            target_dir = self.output_dir

            # Получаем список всех файлов с расширением .pkl
            for filename in os.listdir(source_dir):
                if filename.endswith(".pkl"):
                    source_file = os.path.join(source_dir, filename)
                    target_link = os.path.join(target_dir, filename)
                    try:
                        # Удаляем существующий файл или ссылку, если есть
                        if os.path.exists(target_link) or os.path.islink(target_link):
                            os.remove(target_link)

                        # Создаем символическую ссылку
                        os.symlink(os.path.abspath(source_file), target_link)
                        fsize = os.path.getsize(target_link)
                        self.logger.info(f"Создана ссылка: source_file:'{source_file}', target_link:'{target_link}', размер исходного файла: {fsize} байт")

                    except Exception as e:
                        self.logger.info(f"Ошибка при создании ссылки для source_file:{source_file}: {e}")
        except Exception as e:
            self.logger.info(f"Ошибка при создании создании симлинк для pkl: {e}")

    def run_monitor_thread(self):
        # Запуск обработки файлов в нескольких потоках
        self.logger.info("Запуск обработки файлов в нескольких потоках")
        with ThreadPoolExecutor(max_workers=C.SET_MAX_WORKERS) as executor:
            executor.map(self.create_json_file, self.data_files)

        self.after_export_done()

        self.time_end = time.time()
        self.logger.info(f"Окончание работы. Время работы скрипта {self.time_end - self.time_start:.2f} сек")
           

    def run(self):
        message = "Выгрузка данных из БД в json и запуск контейнера из образа"
        if(not self.image_id):
            message = "Выгрузка данных из БД в json без запуска контейнера"

        self.logger.info(message)
        self.logger.info(f'exp_params: {self.params}')
        self.logger.info(f'img_params: {self.img_params}')

        self.get_binded_datasets()
        self.set_datasets_hierarchy()

        if(self.project_id and self.dataset_id):
            self.get_param_output_dir(self.params, f"/projects_data/{self.project_id}/{self.dataset_id}/markups_in") # директория где создаются файлы json
            self.ann_output_dir = f"/projects_data/{self.project_id}/{self.dataset_id}/markups_out"
            
            self.logger.info(f'image_id: {self.image_id}')
            self.logger.info(f'project_id: {self.project_id}')
            self.logger.info(f'dataset_id: {self.dataset_id}')
            self.logger.info(f'parent_dataset_id: {self.parent_dataset_id}')
            self.logger.info(f'init_dataset_id: {self.init_dataset_id}')
            self.logger.info(f'only_verified_chains: {self.only_verified_chains}')
            self.logger.info(f'only_selected_files: {self.only_selected_files}')

            self.data_files = self.get_dataset_files(self.init_dataset_id)
            self.logger.info(f'Files found: {len(self.data_files)} ')
            # очистка директории перед выгрузкой из базы
            if (self.image_id):
                self.clear_directory(self.output_dir)

            self.monitor_thread = threading.Thread(target=self.run_monitor_thread)
            self.monitor_thread.start()

            files_count = len(self.data_files)
            message = {'message': 'Файлы отправлены в обработку', 'files_count' : {files_count} }
            self.logger.info( f'Response json: {message} ')
        else:
            message = {'message': f'Ошибка: project_id:\'{self.project_id}\', dataset_id: \'{self.dataset_id}\'', 'files_count' : 0 }
            self.logger.info( f'Response json: {message} ')

        
        return message