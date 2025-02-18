import os
import sys
import json
import threading
import time
import traceback
from api.lib.func_datetime import *
import api.sets.const as C
import api.database.dbquery as dbq
from sqlalchemy import text

class DatasetMarkupsExportOld:
    def __init__(self, project_id, dataset_id): 
        self.data_files = {}
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.status = {}
        self.errors = {}
        self.stop_event = threading.Event()
        self.threads = []
        self.monitor_thread = None
        self.wait_thread = None
        self.dir_json = f"/projects_data/{project_id}/{dataset_id}/markups_in" # директория с файлами json от ИНС
        self.logname = get_dt_now_noms()

    def log_info(self, mes):
        with open(C.LOG_PATH + f"/{self.logname}", "a") as file:
            file.write(f'{get_dt_now_noms()} {mes}\n')
    

    def prepare_json_data(self, file_id):
        datasets = self.get_linked_datasets(self.dataset_id)
      
        #self.log_info(datasets)
        processed_data = {}
        # for item in data:
        #   for key, value in item.items():
        #     if isinstance(value, uuid.UUID):
        #       processed_data[key] = str(value)
        #     if isinstance(value, datetime):
        #       processed_data[key] = value.isoformat()
        
        # Преобразование в JSON
        json_data = json.dumps(processed_data, ensure_ascii=False)
      
        self.log_info(json_data)

        return json_data

    def create_json_file(self, file_data):
        path_to_file = self.dir_json #'json/0018/'
        self.log_info(f"путь к файлу: {path_to_file}/{file_data['name']}")
        data = self.prepare_json_data(file_data['id'])

        try:
            # проверка на наличие markup_in , если нет - создать
            os.makedirs(path_to_file, exist_ok=True) 
            with open(f"{path_to_file}/{file_data['name']}.json", 'w', encoding='utf-8') as f:
                #json.dump(data, f, indent=4, ensure_ascii=False)
                f.write(data)
            self.status[file_data['name']] = "Success"
            self.log_info(self.status[file_data['name']])
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
                    all_finished = False
                elif state is not None:
                    #print(f"{state} - {filename}")
                    self.status[filename] = None  # Чтобы не дублировать вывод
            
            if all_finished:
                self.stop_event.set()
                break  

        print("\nSummary:")
        for filename, state in self.status.items():
            if state is None:
                state = "Success"
            print(f"{filename}: {state}")

        if self.errors:
            print("\nErrors:")
            for filename, error in self.errors.items():
                print(f"{filename} failed with error:\n{error}")

    def wait_for_threads(self):
        # Ожидание завершения всех потоков. 
        for thread in self.threads:
            thread.join()
        self.stop_event.set()
        self.monitor_thread.join()
        print("Monitoring thread has finished.") # START DOCKER CREATE CONTAINER

    def run(self):
        self.log_info("Start process")
        self.data_files = self.get_dataset_files(self.dataset_id)
        self.log_info(len(self.data_files))
        # Запуск потоков создания файлов
        self.status = {filename: "In Progress" for filename in self.data_files}
        # print(f"{resp[0]['id']}", file=sys.stderr)
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
        self.log_info( message )
        
        return message


    def get_linked_datasets(self, dataset_id):
        # получим корневой dataset id
        stmt = text("WITH RECURSIVE dataset_hierarchy AS ( SELECT id, parent_id, name, type_id, project_id, source, nn_original_id, nn_online_id, nn_teached_id, description, author_id, dt_created, dt_calculated, is_calculated, is_deleted  FROM public.datasets WHERE id = :dataset_id UNION ALL SELECT d.id, d.parent_id, d.name, d.type_id, d.project_id, d.source,d.nn_original_id,d.nn_online_id,  d.nn_teached_id,d.description,d.author_id,d.dt_created,d.dt_calculated,d.is_calculated,d.is_deleted FROM public.datasets d JOIN dataset_hierarchy dh ON d.id = dh.parent_id ) SELECT * FROM dataset_hierarchy")
        resp = dbq.select_wrapper(stmt, {"dataset_id" : dataset_id } )  
        return resp
    

    def get_dataset_files(self, dataset_id):
        # получим корневой dataset id
        stmt = text("SELECT d2.id FROM datasets d1 , datasets d2 where d1.project_id = d2.project_id and d2.parent_id is null and d1.id = :dataset_id")
        parent_dataset_id = dbq.select_wrapper(stmt, {"dataset_id" : dataset_id } )
        self.log_info(f'dataset_id = {dataset_id}')
        self.log_info(f'parent_dataset_id = {parent_dataset_id[0]["id"]}')

        stmt = text("SELECT * FROM files f  WHERE f.dataset_id = :dataset_id")
        resp = dbq.select_wrapper(stmt, {"dataset_id" : parent_dataset_id[0]['id']} )
        #print(f"{resp}", file=sys.stderr)
        return resp

if __name__ == "__main__":
    project_id='fc3108a6-7b57-11ef-b77b-0242ac140002'
    dataset_id='03dfeb68-7cb5-11ef-84e7-0242ac140002'
    manager = DatasetMarkupsExportOld(project_id, dataset_id)
    manager.run()
