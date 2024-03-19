from api.manage.managedb import *


def mng_create_user( name, login, password, role, description):
   return mngdb_create_user( name, login, password, role, description)


def mng_single_user( userId ):
   return mngdb_single_user( userId )


def mng_create_role( name, code):
   return mngdb_create_role( name, code)