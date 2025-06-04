import os
import sys
import threading
import api.sets.config as C  
from api.lib.func_datetime import *
from api.lib.classResponseMessage import responseMessage
import json
import ijson
import requests
import psycopg2
import uuid
from decimal import Decimal
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from configparser import ConfigParser
# import logger
# from  api.format.logger import logger
import gc

class ImportAnnJsonToDB:

    BATCH_SIZE = 10
    IMPORT_CHAINS_ORIGIN_ID_AUTO = 1
    
    def __init__(self, project_id, dataset_id, files):

        self.LOG_FNAME = f"{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}_import_json.log"
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
        self.time_start = time.time()
        self.time_end = time.time()

        self.init_logger()


    def init_logger(self, type = 'file'):
        self.directory_name = C.LOG_PATH
        self.file_name = f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_import_json.log'
        self.file_path = os.path.join(self.directory_name, self.file_name)
        os.makedirs(self.directory_name, exist_ok=True)
        self.handler = open(self.file_path, 'a+')

    def logger_info(self, content):
        if self.handler :
            self.handler.write(f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")} - {content}\n')
            self.handler.flush()

    def logger_error(self, content):
        if self.handler :
            self.handler.write(f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")} - Ошибка: {content}\n')
            self.handler.flush()

    # def log(self, m, is_error = False): # save log message to log & prepare as response message
    #     if( not is_error ):
    #         self.logger_info(m)
    #         self.message.set(m)
    #     else:
    #         self.logger_error(m)
    #         self.message.setError(m)

    def get_color(self, i):
        color_count = len(self.color_set)
        return self.color_set[ i % color_count ]


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
            return [ImportAnnJsonToDB.convert_to_serializable(i) for i in obj]
        elif isinstance(obj, dict):  
            return {k: ImportAnnJsonToDB.convert_to_serializable(v) for k, v in obj.items()}
        return obj  # Остальное оставляем без изменений
    
    def get_json_file_id(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            parser = ijson.parse(file)
            is_first_file = False
            for prefix, event, value in parser:
                if (prefix == "files.item" and event == "start_map"):
                    is_first_file = True  # Нашли первый элемент списка files
                if (is_first_file and prefix == "files.item.file_id" and event == "string"):
                    return value
        return None     

    def get_json_file_name(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            parser = ijson.parse(file)
            is_first_file = False
            for prefix, event, value in parser:
                if (prefix == "files.item" and event == "start_map"):
                    is_first_file = True  # Нашли первый элемент списка files
                if (is_first_file and prefix == "files.item.file_name" and event == "string"):
                    return value
        return None     
    

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
        self.logger_info(f"Данные подключения: хост: {config['host']},  название БД: {config['database']}")
        return conn 
        
    def close_idle(self):
        conn = self.get_connect()
        cursor = conn.cursor()
        cursor.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = \'idle\' AND pid <> pg_backend_pid()")
    
    def insert_chain_query(self):
        return "INSERT INTO chains ( dataset_id, file_id, name, vector, author_id, origin_id, color, confidence ) VALUES ( %s, %s, %s,  %s, %s, %s, %s, %s) RETURNING id"

    def insert_markup_query(self):
        return "INSERT INTO markups ( dataset_id, file_id, parent_id, mark_frame, mark_time, vector, mark_path, author_id, confidence) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id "

    def insert_chain_markup_query(self):
        return "INSERT INTO markups_chains (chain_id, markup_id) VALUES (%s, %s) RETURNING markup_id"

    def stmt_dataset_parent_id(self):
        return "SELECT d2.id FROM datasets d1 , datasets d2 where d1.project_id = d2.project_id and d2.parent_id is null and d1.id = %s"

    def stmt_dataset_state(self):
        return "SELECT state_id FROM datasets where id = %s"

    def stmt_author_id(self):
        return "SELECT u.id FROM users u  WHERE u.login = %s"

    def get_dataset_parent_id(self):
        self.logger_info(f'Поиск dataset_parent_id. Подключение к базе.' )
        conn = self.get_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(self.stmt_dataset_parent_id(), (self.dataset_id,))
            dataset_parent_id = cursor.fetchone() 
            if(dataset_parent_id):
                self.dataset_parent_id = dataset_parent_id[0]
                self.logger_info(f'dataset_parent_id = {self.dataset_parent_id}')
            else:
                self.logger_error(f'dataset_parent_id не найден . Параметры поиска: dataset_id={self.dataset_id}')
        except psycopg2.DatabaseError as e:
            self.logger_error(f"Поиск dataset_parent_id. Ошибка базы данных: {e}") 
        finally:
            cursor.close()
            conn.close()

        return True

    def get_author_id(self, user_login):
        self.logger_info(f'Поиск author_id. Подключение к базе.' )
        conn = self.get_connect()
        cursor = conn.cursor()
        try:
            cursor.execute(self.stmt_author_id(), (user_login,))
            author = cursor.fetchone()
            if(author):
                self.author_id = author[0]
                self.logger_info(f'author_id = {self.author_id}')
            else:
                self.logger_error(f'author_id не найден . Параметры поиска: user_login={user_login}')
        except psycopg2.DatabaseError as e:
            self.logger_error(f"Поиск author_id. Ошибка базы данных: {e}") 
        finally:
            cursor.close()
            conn.close()

        return True
    

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
            self.logger_error(f"Ошибка целостности данных: {e}") 
        except psycopg2.DatabaseError as e:
            cursor.execute("ROLLBACK TO SAVEPOINT sp1;") 
            self.logger_error(f"Ошибка базы данных: {e}") 
        finally:
            cursor.execute("RELEASE SAVEPOINT sp1;") 

        return result_id

    def stmt_file_id(self):
        return "SELECT f.id FROM files f  WHERE f.dataset_id = %s AND f.name=%s"
    
    def get_dataset_state(self, cursor, file_name):
        cursor.execute(self.stmt_dataset_state(), (self.dataset_id,))
        dataset_state = cursor.fetchone()
        self.logger_info(f'{file_name} Dataset state: {dataset_state}')


    def process_json_file(self, file_name):
        self.logger_info("process_json_file")
        file_id = None
        chain_success = markup_success = 0  
        start_time = time.time()
        file_path = f'{self.dir_json}/{file_name}'
        if (os.path.exists(file_path)):
            file_id = self.get_json_file_id(file_path)
            json_file_name = self.get_json_file_name(file_path)
            self.logger_info(f'{file_name}: files.file.file_id = {file_id}, files.file.file_name = {file_name}')
            conn = self.get_connect()
            cursor = conn.cursor()
            cursor.execute(self.stmt_file_id(), ( self.dataset_parent_id, json_file_name ))
            db_file = cursor.fetchone()
            if( db_file[0] ):
                file_id = db_file[0]
            if(json_file_name):
                file_name = json_file_name
            self.logger_info(f'db_file: {file_id}')
        else:
            self.logger_error(f'Файл не найден: {file_path}')

        if (file_id):
            try:
                self.logger_info(f"Начало обработки {file_path}")
                with open(file_path, "r", encoding="utf-8") as file: 
                    # self.logger_info(f'{file_name}: Подключение к БД ' )
                    # Обрабатываем файлы
                    parser = ijson.items(file, "files.item.file_chains.item")  # Извлекаем цепочки напрямую
                    for cnt, chain in enumerate(parser):
                        chain_vector = json.dumps(self.convert_to_serializable(chain.get("chain_vector", [])))
                        chain_id = self.exec_insert( cursor, self.insert_chain_query(), 
                            (
                                self.dataset_id, 
                                file_id, 
                                chain.get("chain_name", None),
                                chain_vector,
                                self.author_id,
                                self.IMPORT_CHAINS_ORIGIN_ID_AUTO,
                                self.get_color(cnt),
                                chain.get("chain_confidence", None),
                            )
                        ) 
                        # self.logger_info(f'chain_id: {chain_id}')

                        if( chain_id ):
                            chain_success += 1
                            for cnt2, markup in enumerate(chain.get("chain_markups", [])):
                                # self.logger_info(f'markup {cnt2}')
                                markup_vector = json.dumps(self.convert_to_serializable(markup.get("markup_vector", [])))
                                markup_id = self.exec_insert(cursor, self.insert_markup_query(), 
                                    (
                                        self.dataset_id, 
                                        file_id, 
                                        markup.get("markup_parent_id", None),
                                        markup.get("markup_frame", None),
                                        markup.get("markup_time", None),
                                        markup_vector,
                                        json.dumps(self.convert_to_serializable(markup.get("markup_path", {}))),
                                        self.author_id,
                                        markup.get("markup_confidence", None)
                                    )
                                ) 
                                # self.logger_info(f'markup_id: {markup_id}')
                                if( markup_id ):
                                    markup_success += 1
                                    self.exec_insert(cursor, self.insert_chain_markup_query(), ( chain_id, markup_id))
                        if( cnt > 0 and cnt % self.BATCH_SIZE == 0):
                            self.logger_info(f'{file_name} Обработано: Chains: {cnt}')
                            # проверим в базе данных метку на прерывание процесса выгрузки для dataset_id
                            self.get_dataset_state(cursor, file_name)

                        del chain  # Удаляем обработанный объект, чтобы освободить память
                        gc.collect() 
                    # Фиксация транзакции
                    self.logger_info(f'chain_success: {chain_success}')
                    if ( chain_success > 0 ) :
                        try:
                            conn.commit()
                        except psycopg2.DatabaseError as e:
                            conn.rollback()
                            self.logger_error(f"Ошибка при commit(): {e}")
                    else:
                        self.logger_error("Данные не добавлены.")

                    self.logger_info(f"{file_name} добавлено записей: Chains = {chain_success}. Markups: {markup_success}")
                    self.files_res[file_id] = {'name': file_name, 'file_id': file_id, 'chains_count':chain_success, 'markups_count':markup_success }

                    cursor.close()
                    conn.close()                   
                
            except Exception as e:
                self.logger_error(f"Произошла ошибка при открытии файла {file_name}: {e}")
            finally:
                cursor.close()
                conn.close()
                

        else:
            self.logger_error(f"{file_name} file_id not correct : {file_id}")

        end_time = time.time()
        self.logger_info(f"{file_name} обработан за {end_time - start_time:.2f} сек")
        

    def run_monitor_thread(self): 
        self.logger_info("Запуск обработки файлов в нескольких потоках")
        with ThreadPoolExecutor(max_workers=C.SET_MAX_WORKERS) as executor:
            executor.map(self.process_json_file, self.files)

        try:
            url = f"{C.HOST_RESTAPI}/projects/{self.project_id}/datasets/{self.dataset_id}/on_import" 
            self.logger_info(f'prepare Url on_import: {url}')
            files_post = list(self.files_res.values())
            self.logger_info(f'Данные отправленные on_import "files": {files_post}')
            headers = { "Content-Type": "application/json" }
            data = { "files": files_post }

            response = requests.post(url, json=data, headers=headers) 
            self.logger_info(f'on_import response: {response}')
        except Exception as e:
            self.logger_info(f'on_import response error: {e}')

        # self.close_idle()
        self.time_end = time.time()
        self.logger_info(f"Окончание работы. Время работы скрипта {self.time_end - self.time_start:.2f} сек")
            

    def run(self):
        self.logger_info(f"Начало работы. Чтение файлов импорта из директории: {self.dir_json}")
        self.time_start = time.time()
        is_error = True
        mes = 'undefined'
        if not os.path.isdir(self.dir_json):
            mes = f"Ошибка: {self.dir_json} указанная директория не сущестует или не доступна"
            self.logger_info(mes)
        else:
            if len(self.files) == 0 : 
                mes = f"Ошибка: получен пустой список json файлов"
                self.logger_info(mes)
            else:
                # Запуск мониторинга
                self.get_dataset_parent_id()
                self.get_author_id('manager')
                if( not self.dataset_parent_id):
                    mes = f"Ошибка: dataset parent_id: '{self.dataset_parent_id}'"
                    self.logger_info(mes)
                elif( not self.author_id):
                    mes = f"Ошибка: dataset author_id: '{self.author_id}'"
                    self.logger_info(mes)
                else:
                    self.monitor_thread = threading.Thread(target=self.run_monitor_thread)
                    self.monitor_thread.start()
                    mes = f"Данные получены. Файлов в обработке: '{len(self.files)}'"
                    self.logger_info(mes)
                    is_error = False

        return {'error': is_error, 'text': mes}
    
    def __del__(self):
        if self.handler:
            self.handler.close()
