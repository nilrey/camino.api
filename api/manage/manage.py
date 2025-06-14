import os.path, json
from api.database.ormquery import *
import api.services.base as dkr
from api.services.monitor import *
import api.format.response_objects as ro # Response Objects
import api.format.response_teplates as rt # Response Template
import api.sets.config as C
import time 
from api.lib.func_ann_out_db_save import ann_out_db_save as save_output
import api.lib.func_utils as fu
from api.lib.classExportDBToAnnJson import *
from api.lib.classImportAnnJsonToDB import *
import requests

from  api.format.logger import logger


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

def mng_image_run(post_data):
   resp = DatasetMarkupsExport({"dataset_id": post_data['dataset_id'], "only_verified_chains": post_data['only_verified_chains'], "only_selected_files": post_data['only_selected_files']}, post_data)
   res = resp.run()
   return res


def mng_containers():
   response = dkr.dkr_containers()
   resp_cmd_json_img = dkr.dkr_images()
   if (not response['error']): response = ro.dkr_containers({'containers':response['response'], 'images':resp_cmd_json_img['response']})
   return response


def mng_containers_stats():
   response = dkr.dkr_containers_stats()
   if dkr.isJson(response):
      logger.info("mng_containers_stats, dkr_containers_stats - response:")
      logger.info(response) 

   if (not response['error']): response = ro.containers_stats(response['response'])
   return response


def mng_container(container_id):
   response = dkr.dkr_container(container_id)
   resp_cmd_json_img = dkr.dkr_images()
   if (not response['error']): response = ro.container({'container': response['response'], 'images': resp_cmd_json_img['response']})
   return response


def mng_container_stats(container_id):
   response = ro.container_stats(container_id, mng_containers_stats())
   return response
   

def mng_container_monitor(container_id):
   monitor = Monitor()
   result = monitor.create_json(container_id)
   return result


def mng_container_start(container_id):
   response = dkr.dkr_container_start(container_id) # UID as response 
   if (not response['error']): response = mng_container(response['response'][0])
   return response


def mng_container_stop(container_id, dataset_id):
   url = f"{C.HOST_RESTAPI}/containers/{container_id}/on_stop"
   is_error, message, container_host = docker_service.stop_container(container_id)
   response = {'dataset_id' : dataset_id, "host" : container_host, "error": is_error, "message" : message}
   logger.info(f"response: {response}" )
   logger.info(f"Url on_stop: {response}" )
      
   requests.post(url, json = response)

def mng_import_json_to_db(projectId, datasetId, parse_data):

   resp = ImportAnnJsonToDB(projectId, datasetId, parse_data.files)
   res = resp.run()
   return res


def mng_export_db_to_json(post_data):
   resp = DatasetMarkupsExport(post_data , {})
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