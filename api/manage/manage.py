import json
from api.database.ormquery import *
import api.docker.base as dkr
from api.docker.monitor import *
import api.format.response_objects as ro # Response Objects
import api.format.response_teplates as rt # Response Template


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


# Roles
def mng_create_role(name, code):
   return mngdb_create_role(name, code)


# Docker
def mng_docker_info():
   response = dkr.dkr_docker_info()
   if (not response['error']): response = ro.docker_info(response['response'])
   return response


def mng_docker_image_run(imageId, **kwargs):
   return dkr.dkr_image_run(imageId, **kwargs)


def mng_images():
   response = dkr.dkr_images()
   if (not response['error']): response = ro.docker_images(response['response'])
   return response


def mng_image(imageId):
   response = dkr.dkr_images()
   if (not response['error']): response = ro.docker_image(imageId, response['response'])
   return response


def mng_containers():
   resp_cmd_json_cont = dkr.dkr_containers()
   resp_cmd_json_img = dkr.dkr_images()
   data = {'containers':resp_cmd_json_cont['response'], 'images':resp_cmd_json_img['response']}
   # response = ro.dkr_containers(data) if( not resp_cmd_json_cont['error'] ) else resp_cmd_json_cont
   response = {}
   if (not resp_cmd_json_cont['error']): response = ro.dkr_containers(data)
   return response


def mng_containers_stats():
   response = dkr.dkr_containers_stats()
   if (not response['error']): response = ro.containers_stats(response['response'])
   return response


def mng_container(containerId):
   response = dkr.dkr_container(containerId)
   if (not response['error']): response = ro.container(response['response'])
   return response


def mng_container_stats(containerId):
   response = dkr.dkr_containers_stats()
   if (not response['error']): response = ro.container_stats(containerId, response['response'])
   return response
   

def mng_container_monitor(containerId):
   monitor = Monitor()
   result = monitor.create_json(containerId)
   return result
