from api.database.ormquery import *
from api.docker.base import *


# Users
def mng_create_user( name, login, password, role, description):
   return mngdb_create_user( name, login, password, role, description)


def mng_single_user( userId ):
   return mngdb_single_user( userId )


def mng_update_user(id, **kwargs):
   return mngdb_update_user(id, **kwargs)


# Roles
def mng_create_role( name, code):
   return mngdb_create_role( name, code)


# Docker
def mng_docker_get_info():
   return dck_get_info()