import os.path, json
from api.database.ormquery import *
import api.docker.base as dkr
from api.docker.monitor import *
import api.format.response_objects as ro # Response Objects
import api.format.response_teplates as rt # Response Template
import api.sets.const as C
import time 
from api.lib.func_ann_out_db_save import ann_out_db_save as save_output
import api.lib.func_utils as fu
from api.lib.classDatasetMarkupsExport import *
from api.lib.classImportAnnJsonToDB import *
import requests

# Users
def mng_create_user(**kwargs):
   return mngdb_create_user(**kwargs)


def mng_all_users():
   return mngdb_all_users()


def mng_single_user(id):
   return mngdb_single_user(id)


def mng_update_user(id, **kwargs):
   return mngdb_update_user(id, **kwargs)


def mng_delete_user(id):
   return mngdb_delete_user(id)


# Projects
def mng_create_project(**kwargs):
   return mngdb_create_project(**kwargs)


def mng_all_projects():
   return mngdb_all_projects()


def mng_single_project(id):
   return mngdb_single_project(id)


def mng_single_project_ext(id):
   return mngdb_single_project_ext(id)


def mng_update_project(id, **kwargs):
   return mngdb_update_project(id, **kwargs)


def mng_delete_project(id):
   return mngdb_delete_project(id)

def mng_parse_ann_output(target_dir):
   if not os.path.isdir(target_dir):
      res = '{"error": True, "mes": "Ошибка: указанная директория не сущестует или не доступна"}'
   else:
      files = fu.get_files(target_dir, ['json'])
      if len(files) == 0 : 
         res = '{"error": True, "mes": "Ошибка: в указанной директории json файлы не найдены"}'
      else:
         for f in files:
            save_output(f"{target_dir}/{f}")
         res = '{"error": False, "mes": "Файлы запущены в обработку"}'

   return res


# Roles
def mng_create_role(name, code):
   return mngdb_create_role(name, code)


# Docker
def mng_docker_info():
   response = dkr.dkr_docker_info()
   if (not response['error']): response = ro.docker_info(response['response'])
   return response


def mng_images():
   response = dkr.dkr_images()
   if (not response['error']): response = ro.docker_images(response['response'])
   return response


def mng_image(image_id):
   response = dkr.dkr_images()
   if (not response['error']): response = ro.docker_image(image_id, response['response'])
   return response


def mng_container_create(image_id, params):
   resp_cmd_json_img = dkr.dkr_images()
   image = ro.getImageById(image_id, resp_cmd_json_img['response'] )
   if( image["name"] ):
      response = dkr.dkr_container_create(image["name"], params)
      # if (not response['error']): response = mng_container(response['response'][0])
   else: 
      response['error'] = True
      response['error_descr'] = 'По данному Id образ не найден'
   return response


def mng_image_run2(image_id, params):
   response = mng_container_create(image_id, params)
   if (not response['error']): 
      response = mng_container_start(response['response'][0])
      # регистрация контейнера
      if (not response['error']): 
         url = f"{C.HOST_RESTAPI}/containers/{response['id']}/on_run"
         response['dataset_id'] = params['out_dir'].split('/')[-2]
         requests.post(url, json = response)
      else:
         print(f"{response['error_descr']}", file=sys.stderr)

   return response


def mng_image_run(image_id, params):
   resp = DatasetMarkupsExport(image_id, params)
   res = resp.run()
   return res


def mng_containers():
   response = dkr.dkr_containers()
   resp_cmd_json_img = dkr.dkr_images()
   if (not response['error']): response = ro.dkr_containers({'containers':response['response'], 'images':resp_cmd_json_img['response']})
   return response


def mng_containers_stats():
   response = dkr.dkr_containers_stats()
   if (not response['error']): response = ro.containers_stats(response['response'])
   return response


def mng_container(container_id):
   response = dkr.dkr_container(container_id)
   resp_cmd_json_img = dkr.dkr_images()
   if (not response['error']): response = ro.container({'container': response['response'], 'images': resp_cmd_json_img['response']})
   return response


def mng_container_stats(container_id):
   response = dkr.dkr_containers_stats()
   if (not response['error']): response = ro.container_stats(container_id, response['response'])
   return response
   

def mng_container_monitor(container_id):
   monitor = Monitor()
   result = monitor.create_json(container_id)
   return result


def mng_container_start(container_id):
   response = dkr.dkr_container_start(container_id) # UID as response 
   if (not response['error']): response = mng_container(response['response'][0])
   return response


def mng_container_stop(container_id):
   response = dkr.dkr_container_stop(container_id) # UID as response 
   if (not response['error']): response = mng_container(response['response'][0])
   # if (not response['error']): response = ro.container_stop(container_id, response['response'])
   return response  

def mng_import_json_to_db(projectId, datasetId, parse_data):

   resp = ImportAnnJsonToDB(projectId, datasetId, parse_data.files)
   res = resp.run()
   return res

def mng_ann_export(imageId, weights, export, annId):
   weights = weights.replace("/projects_data/weights/", "")
   export = export.replace("/projects_data/export/", "")
   export_name = os.path.basename(export).replace(".tar.gz", "")

   response = dkr.dkr_ann_export(imageId, export_name, annId)
   if(response):
      response = dkr.prepare_ann_archive(imageId, weights, export_name, annId)
   return response