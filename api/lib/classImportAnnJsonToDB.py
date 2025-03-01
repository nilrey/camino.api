import os
import sys
import threading
import api.sets.const as C  
from api.lib.func_datetime import *
from api.lib.classResponseMessage import responseMessage
import json
import psycopg2
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
import logging

class ImportAnnJsonToDB:

    def __init__(self, project_id, dataset_id, files):

        self.LOG_FNAME = f"{datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')}_import_json.log"
        self.LOG_FILE = f'{C.LOG_PATH}/{self.LOG_FNAME}'

        self.project_id = project_id
        self.dataset_id = dataset_id    # dataset_id текущего датасета
        self.files = files
        self.dir_json = f"/projects_data/{self.project_id}/{self.dataset_id}/markups_out" # директория импорта - файлы json от ИНС 
        self.logname = get_dt_now_noms()
        self.message = responseMessage()
        self.logger = self.init_logger()
        self.time_start = time.time()
        self.time_end = time.time()


    def init_logger(self, type = 'file'):
        os.makedirs(C.LOG_PATH, exist_ok=True)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG) 
        if(type == 'console'):    
            # вывод в консоль
            handler = logging.StreamHandler()
        else:
            # вывод в файл
            handler = logging.FileHandler(f"{self.LOG_FILE}", encoding="utf-8")
        
        handler.setLevel(logging.DEBUG)
        # Определяем формат сообщений
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Добавляем обработчик к логгеру (если он ещё не добавлен)
        if not logger.hasHandlers():
            logger.addHandler(handler)

        return logger

    def log(self, m, is_error = False): # save log message to log & prepare as response message
        if( not is_error ):
            self.logger.info(m)
            self.message.set(m)
        else:
            self.logger.error(m)
            self.message.setError(m)



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
    
    def insert_chain_query(self):
        return """
            INSERT INTO chains (id, dataset_id, file_id, name, vector )
            VALUES (%s, %s, %s, %s, %s)
            """

    def insert_markup_query(self):
        return """
            INSERT INTO markups (id, dataset_id, file_id, mark_frame, mark_time, vector, mark_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

    def insert_chain_markup_query(self):
        return "INSERT INTO markups_chains (chain_id, markup_id) VALUES (%s, %s)"

    def stmt_dataset_parent_id(self):
        return "SELECT d2.id FROM datasets d1 , datasets d2 where d1.project_id = d2.project_id and d2.parent_id is null and d1.id = %s"

    def stmt_file_id(self):
        return "SELECT f.id FROM files f  WHERE f.dataset_id = %s and f.name = %s"


    
    def get_file_id_by_name(self, cursor, fname):
        # получим корневой dataset id
        cursor.execute(self.stmt_dataset_parent_id(), (self.dataset_id,))
        dataset_parent_id = cursor.fetchone() 
        
        cursor.execute(self.stmt_file_id(), (dataset_parent_id[0], fname))
        file_info = cursor.fetchone()
        # self.logger.info(file_info[0])

        return file_info[0]
    
    def exec_query(self, cursor, method_name, query_params, count_success = 0):
        try:
            cursor.execute("SAVEPOINT sp1;")
            cursor.execute(method_name, query_params)
            count_success += 1
        except psycopg2.IntegrityError as e:
            cursor.execute("ROLLBACK TO SAVEPOINT sp1;")   # Очищаем состояние транзакции после ошибки
            self.logger.error(f"Ошибка целостности данных: {e}") 
        except psycopg2.DatabaseError as e:
            cursor.execute("ROLLBACK TO SAVEPOINT sp1;") 
            self.logger.error(f"Ошибка базы данных: {e}") 
        finally:
            cursor.execute("RELEASE SAVEPOINT sp1;") 

        return count_success

    
    def process_json_file(self, file_name):
        chain_total = markup_total = chain_success = markup_success = 0  
        start_time = time.time()

        file_path = f'{self.dir_json}/{file_name}'
        self.logger.info(f"Начало обработки {file_path}")
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

            data_files = data.get("files", [])
            if data_files:
                file_chains = data_files[0].get("file_chains", [])
                chain_total = len(file_chains)
                markup_total = sum(len(chain.get("chain_markups", [])) for chain in file_chains)

            self.logger.info(f'Chains in file {chain_total}')
            # Подключение к PostgreSQL
            config = self.load_config()

            conn = psycopg2.connect(
                dbname=config['database'],
                user=config['user'],
                password=config['password'],
                host=config['host'],
                port=config['port'],
            )
            cursor = conn.cursor()
            
            file_id = self.get_file_id_by_name(cursor, file_name[0:-5])

            self.logger.info(f'{file_name} Id = {file_id}')
            
            # Обрабатываем файлы
            for file_entry in data_files:
                for cnt, chain in enumerate(file_entry.get("file_chains", [])): 
                    chain_result = self.exec_query( cursor, self.insert_chain_query(), 
                        (
                            chain["chain_id"], 
                            self.dataset_id, 
                            file_id, 
                            chain["chain_name"], 
                            json.dumps(chain["chain_vector"])
                        )
                    ) 

                    if( chain_result > 0 ):
                        chain_success += 1
                        for markup in chain.get("chain_markups", []):  
                            # Вставляем в таблицу markups 
                            markup_result = self.exec_query(cursor, self.insert_markup_query(), 
                                (
                                    markup["markup_id"], 
                                    self.dataset_id, 
                                    file_id, 
                                    markup["markup_frame"], 
                                    markup["markup_time"], 
                                    json.dumps(markup["markup_vector"]), 
                                    json.dumps(markup["markup_path"])
                                )
                            ) 
                            if(markup_result > 0 ):
                                markup_success += 1
                                self.exec_query(cursor, self.insert_chain_markup_query(), (chain["chain_id"], markup["markup_id"]))
        
        # Фиксация транзакции
        if ( chain_success > 0 and markup_success >  0  ) :
            try:
                conn.commit()
                self.logger.info(f"Файл {file_name} обработан. Добавлено записей: Chains = {chain_success} из {chain_total}. Markups: {markup_success} из {markup_total}")
            except psycopg2.DatabaseError as e:
                conn.rollback()
                self.logger.error(f"Ошибка при commit(): {e}")
        else:
            self.logger.error("Все операции завершились ошибками, ничего не добавлено.")    

        cursor.close()
        conn.close()
        self.time_end = time.time()
        self.logger.info(f"File: {file_name} done in {self.time_end - self.time_start:.2f} сек")
        

    def run_monitor_thread(self):
        # Запуск обработки файлов в нескольких потоках
        with ThreadPoolExecutor(max_workers=2) as executor:  # 5 потоков (можно увеличить)
            executor.map(self.process_json_file, self.files)
            

    def run(self):
        self.logger.info(f"Read import files from: {self.dir_json}")
        self.time_start = time.time()
        if not os.path.isdir(self.dir_json):
            self.log(f"Ошибка: {self.dir_json} указанная директория не сущестует или не доступна", True)
        else:
            if len(self.files) == 0 : 
                self.log(f"Ошибка: получен пустой список json файлов", True)
            else:
                # Запуск мониторинга
                self.monitor_thread = threading.Thread(target=self.run_monitor_thread)
                self.monitor_thread.start()
                self.log(f"Данные получены. Файлов в обработке: {len(self.files)}")

        return self.message.get()
    
    def __del__(self):
        # закрываем логгер, иначе с открытым дескриптором - писать будет в один файл
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close()
