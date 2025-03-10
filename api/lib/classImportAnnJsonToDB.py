import os
import sys
import threading
import api.sets.const as C  
from api.lib.func_datetime import *
from api.lib.classResponseMessage import responseMessage
import json
import ijson
import requests
import psycopg2
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
import logging
import gc

class ImportAnnJsonToDB:

    def __init__(self, project_id, dataset_id, files):

        self.LOG_FNAME = f"{datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')}_import_json.log"
        self.LOG_FILE = f'{C.LOG_PATH}/{self.LOG_FNAME}'

        self.project_id = project_id
        self.dataset_id = dataset_id    # dataset_id текущего датасета
        self.files = files
        self.dataset_parent_id = None
        self.author_id = None
        self.dir_json = f"/projects_data/{self.project_id}/{self.dataset_id}/markups_out" # директория импорта - файлы json от ИНС 
        self.color_set = [ "6b8e23", "a0522d", "00ff00", "778899", "00fa9a", "000080", "00ffff", "ff0000", "ffa500", "ffff00", "0000ff", "ff00ff", "1e90ff", "ff1493", "ffe4b5"]
        self.files_res = {}
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

    def get_color(self, i):
        color_count = len(self.color_set)
        return self.color_set[ i % color_count ]

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
    
    def get_connect(self, premessage = ''):
        # Подключение к PostgreSQL
        config = self.load_config()

        conn = psycopg2.connect(
            dbname=config['database'],
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port'],
        )
        # self.logger.info(f"Данные подключения: хост: {config['host']},  название БД: {config['database']}")
        return conn 
        
    def close_idle(self):
        conn = self.get_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = \'idle\' AND pid <> pg_backend_pid()")
    
    def insert_chain_query(self):
        return "INSERT INTO chains ( dataset_id, file_id, name, vector, author_id, color, confidence ) VALUES ( %s, %s, %s, %s, %s, %s, %s) RETURNING id"

    def insert_markup_query(self):
        return "INSERT INTO markups ( dataset_id, file_id, mark_frame, mark_time, vector, mark_path, author_id, confidence) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id "

    def insert_chain_markup_query(self):
        return "INSERT INTO markups_chains (chain_id, markup_id) VALUES (%s, %s) RETURNING markup_id"

    def stmt_dataset_parent_id(self):
        return "SELECT d2.id FROM datasets d1 , datasets d2 where d1.project_id = d2.project_id and d2.parent_id is null and d1.id = %s"

    def stmt_file_id(self):
        return "SELECT f.id FROM files f  WHERE f.dataset_id = %s and f.name = %s"

    def stmt_author_id(self):
        return "SELECT u.id FROM users u  WHERE u.login = %s"

    def get_dataset_parent_id(self):
        self.logger.info(f'Поиск dataset_parent_id. Подключение к базе.' )
        conn = self.get_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(self.stmt_dataset_parent_id(), (self.dataset_id,))
            dataset_parent_id = cursor.fetchone() 
            if(dataset_parent_id):
                self.dataset_parent_id = dataset_parent_id[0]
                self.logger.info(f'dataset_parent_id = {self.dataset_parent_id}')
            else:
                self.logger.error(f'dataset_parent_id не найден . Параметры поиска: dataset_id={self.dataset_id}')
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Поиск dataset_parent_id. Ошибка базы данных: {e}") 
        finally:
            cursor.close()
            conn.close()

        return True

    def get_author_id(self, user_login):
        self.logger.info(f'Поиск author_id. Подключение к базе.' )
        conn = self.get_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(self.stmt_author_id(), (user_login,))
            author = cursor.fetchone()
            if(author):
                self.author_id = author[0]
                self.logger.info(f'author_id = {self.author_id}')
            else:
                self.logger.error(f'author_id не найден . Параметры поиска: user_login={user_login}')
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Поиск author_id. Ошибка базы данных: {e}") 
        finally:
            cursor.close()
            conn.close()

        return True
    
    def get_file_id_by_name(self, cursor, file_name):
        file_id = None
        self.logger.info(f'{file_name}: Начинаем поиск file_id ' )
        fname = file_name.replace('.json', '') 
        cursor.execute(self.stmt_file_id(), (self.dataset_parent_id, fname))
        file = cursor.fetchone()
        if(len(file) > 0):
            file_id = file[0]
            self.logger.info(f'{file_name}: file_id = {file_id}')
        else:
            self.log(f'{file_name}: file_id не найден . Параметры поиска: dataset_parent_id={self.dataset_parent_id}, fname={fname}')
            self.logger.info( cursor.mogrify(f'{file_name}: {self.stmt_file_id()}', (self.dataset_parent_id, fname) ).decode('utf-8'))

        return file_id  
    
    def exec_insert(self, cursor, method_name, query_params, count_success = 0):
        result_id = 0
        try:
            cursor.execute("SAVEPOINT sp1;") 
            cursor.execute(method_name, query_params)
            result = cursor.fetchone()
            result_id = result[0] if result else 0
            count_success += 1
        except psycopg2.IntegrityError as e:
            cursor.execute("ROLLBACK TO SAVEPOINT sp1;")   # Очищаем состояние транзакции после ошибки
            self.logger.error(f"Ошибка целостности данных: {e}") 
        except psycopg2.DatabaseError as e:
            cursor.execute("ROLLBACK TO SAVEPOINT sp1;") 
            self.logger.error(f"Ошибка базы данных: {e}") 
        finally:
            cursor.execute("RELEASE SAVEPOINT sp1;") 

        return result_id


    def process_json_file(self, file_name):
        chain_success = markup_success = 0  
        start_time = time.time()
        file_path = f'{self.dir_json}/{file_name}'
        try:
            # self.logger.info(f"Начало обработки {file_path}")
            with open(file_path, "r", encoding="utf-8") as file: 
                self.logger.info(f'{file_name}: Подключение к БД ' )
                conn = self.get_connect()
                cursor = conn.cursor()

                file_id = self.get_file_id_by_name(cursor, file_name)
                
                # Обрабатываем файлы
                if (file_id):
                    parser = ijson.items(file, "files.item.file_chains.item")  # Извлекаем цепочки напрямую
                    for cnt, chain in enumerate(parser):
                        # self.logger.info(f'Chain: {cnt}')              
                        chain_id = self.exec_insert( cursor, self.insert_chain_query(), 
                            (
                                self.dataset_id, 
                                file_id, 
                                chain.get("chain_name", None),
                                chain.get("chain_vector", None),
                                self.author_id,
                                self.get_color(cnt),
                                chain.get("chain_confidence", None),
                            )
                        ) 
                        # self.logger.info(f'chain_id: {chain_id}')

                        if( chain_id ):
                            chain_success += 1
                            for cnt2, markup in enumerate(chain.get("chain_markups", [])):
                                # self.logger.info(f'markup {cnt2}')
                                markup_id = self.exec_insert(cursor, self.insert_markup_query(), 
                                    (
                                        self.dataset_id, 
                                        file_id, 
                                        markup.get("markup_frame", None),
                                        markup.get("markup_time", None),
                                        markup.get("markup_vector", None),
                                        json.dumps(markup.get("markup_path", None)),
                                        self.author_id,
                                        markup.get("markup_confidence", None)
                                    )
                                ) 
                                # self.logger.info(f'markup_id: {markup_id}')
                                if( markup_id ):
                                    markup_success += 1
                                    self.exec_insert(cursor, self.insert_chain_markup_query(), ( chain_id, markup_id))
                        if( cnt > 0 and cnt % 10 == 0):
                            self.logger.info(f'{file_name} Обработано: Chains: {cnt}')
                        del chain  # Удаляем обработанный объект, чтобы освободить память
                        gc.collect() 
                else:
                    self.logger.error(f"{file_name} file_id NOT passed : {file_id}")
                # Фиксация транзакции
                self.logger.info(f'chain_success: {chain_success}')
                if ( chain_success > 0 ) :
                    try:
                        conn.commit()
                        self.logger.info(f"{file_name} добавлено записей: Chains = {chain_success}. Markups: {markup_success}")
                        self.files_res[file_id] = {'name': file_name, 'chains_count':chain_success, 'markups_count':markup_success }
                    except psycopg2.DatabaseError as e:
                        conn.rollback()
                        self.logger.error(f"Ошибка при commit(): {e}")
                else:
                    self.logger.error("Данные не добавлены.")

                cursor.close()
                conn.close()                   
            
        except Exception as e:
            print(f"Произошла ошибка при открытии файла {file_name}: {e}")
            
        end_time = time.time()
        self.logger.info(f"{file_name} обработан за {end_time - start_time:.2f} сек")
        

    def run_monitor_thread(self):
        # Запуск обработки файлов в нескольких потоках
        with ThreadPoolExecutor(max_workers=C.SET_MAX_WORKERS) as executor:  # 5 потоков (можно увеличить)
            executor.map(self.process_json_file, self.files)

        try:
            url = f"{C.HOST_RESTAPI}/projects/{self.project_id}/datasets/{self.dataset_id}/on_import" 
            self.logger.info(f'prepare Url on_import: {url}')
            files_post = list(self.files_res.values())
            self.logger.info(f'Данные отправленные on_import "files": {files_post}')
            headers = { "Content-Type": "application/json" }
            data = { "files": files_post }

            response = requests.post(url, json=data, headers=headers) 
            self.logger.info(f'on_import response: {response}')
        except Exception as e:
            self.logger.info(f'on_import response error: {e}')

        self.close_idle()
        self.time_end = time.time()
        self.logger.info(f"Окончание работы. Время работы скрипта {self.time_end - self.time_start:.2f} сек")
            

    def run(self):
        self.logger.info(f"Начало работы. Чтение файлов имопрта из директории: {self.dir_json}")
        self.time_start = time.time()
        if not os.path.isdir(self.dir_json):
            self.log(f"Ошибка: {self.dir_json} указанная директория не сущестует или не доступна", True)
        else:
            if len(self.files) == 0 : 
                self.log(f"Ошибка: получен пустой список json файлов", True)
            else:
                # Запуск мониторинга
                self.get_dataset_parent_id()
                self.get_author_id('manager')
                if(self.dataset_parent_id and self.author_id):
                    self.monitor_thread = threading.Thread(target=self.run_monitor_thread)
                    self.monitor_thread.start()
                    self.log(f"Данные получены. Файлов в обработке: {len(self.files)}")

        return self.message.get()
    
    def __del__(self):
        # закрываем логгер, иначе с открытым дескриптором - писать будет в один файл
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close()
