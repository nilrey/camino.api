from api.database.models.models import *
from api.database.models.User import User
from api.database.dbquery import *


# Users
class CUser(User):

    def mngdb_create_user( name, login, password, role, description):
        newUser = insert_new (User, User( id=getUuid(), name = name, login=login, role_code=role, password=password, description=description, is_deleted=False) )
        return newUser


    def mngdb_update_user( id, **kwargs):
        updUser = update_record (User, id, **kwargs)
        return updUser  


    def mngdb_single_user(userId):
        res = select_byid(User, userId)
        return res


    def mngdb_delete_user(userId):
        res = delete_record(User, userId)
        return res


# Projects
def mngdb_create_project( name, login, password, role, description):
    newproject = insert_new (Project, Project( id=getUuid(), name = name, login=login, role_code=role, password=password, description=description, is_deleted=False) )
    return newproject


def mngdb_update_project( id, **kwargs):
    updproject = update_record (Project, id, **kwargs)
    return updproject  


def mngdb_single_project(projectId):
   res = select_byid(Project, projectId)
   return res


def mngdb_delete_project(projectId):
    res = delete_record(Project, projectId)
    return res


# Roles
def mngdb_create_role( name, code):
    newRole = insert_new (Role, Role( name = name, code=code ) , False)
    return newRole
