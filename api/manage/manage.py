from api.database.ormquery import *
from api.docker.base import *


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


# # Docker
def mng_docker_get_info():
   return dkr_docker_info()

def mng_docker_image_run(imageId, **kwargs):
   return dkr_image_run(imageId, **kwargs)


def mng_images():
   return dkr_images()


def mng_image(imageId):
   return dkr_image(imageId)


# def mng_image_run(imageId):
#    return dkr_image_run(imageId)


def mng_containers():
   return dkr_containers()


def mng_containers_stats():
   return dkr_containers_stats()


def mng_container(containerId):
   return dkr_container(containerId)


def mng_container_stats(containerId):
   return dkr_container_stats(containerId)
