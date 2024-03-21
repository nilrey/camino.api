from api.database.models.models import *
from api.database.dbquery import *


def mngdb_create_user( name, login, password, role, description):
    newUser = insert_new (User, User( id=getUuid(), name = name, login=login, role_code=role, password=password, description=description, is_deleted=False) )
    return newUser


def mngdb_single_user(userId):
   res = select_byid(User, userId)
   return res


def mngdb_create_role( name, code):
    newRole = insert_new (Role, Role( name = name, code=code ) , False)
    return newRole