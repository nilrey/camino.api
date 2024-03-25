from api.database.ormquery import *
from api.docker.base import *


# Users
def mng_create_user( **kwargs):
   return CUser.mngdb_create_user(**kwargs)


def mng_single_user( userId ):
   return CUser.mngdb_single_user( userId )


def mng_update_user(id, **kwargs):
   return CUser.mngdb_update_user(id, **kwargs)


def mng_delete_user(id):
   return CUser.mngdb_delete_user(id)


# Projects
def mng_create_project(**kwargs):
   return mngdb_create_project(**kwargs)


def mng_single_project( projectId ):
   return mngdb_single_project(projectId)


def mng_update_project(id, **kwargs):
   return mngdb_update_project(id, **kwargs)


def mng_delete_project(id):
   return mngdb_delete_project(id)


# Roles
def mng_create_role( name, code):
   return mngdb_create_role( name, code)


# Docker
def mng_docker_get_info():
   return dck_get_info()