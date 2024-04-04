from api.database.models.models import *
# from api.database.models.User import User
from api.database.dbquery import *
import uuid
from api.lib.func_datetime import get_dt_now


# Users
def mngdb_create_user( name, login, password, role_code, description):
    newUser = insert_new(User, User( id=getUuid(), name = name, login=login, role_code=role_code, password=password, description=description, is_deleted=False) )
    return newUser

def mngdb_new_user( name, login, password, role_code, description):
    newUser = insert_new(User, User( id=getUuid(), name = name, login=login, role_code=role_code, password=password, description=description, is_deleted=False) )
    return newUser


def mngdb_update_user( id, **kwargs):
    updUser = update_record(User, id, **kwargs)
    return updUser  


def mngdb_all_users():
    res = select_all(User)
    return res


def mngdb_single_user(id):
    res = select_byid(User, id)
    return res


def mngdb_delete_user(id):
    res = delete_record(User, id)
    return res


# Projects
def mngdb_create_project( **kwargs ):
    newproject = insert_new(Project, Project( id=getUuid(), name=kwargs['name'], type_id=int(kwargs['type_id']), description=kwargs['description'], 
                                              author_id=uuid.UUID(kwargs['author_id']).hex, dt_created=get_dt_now(), is_deleted=False ) )
    return newproject


def mngdb_all_projects():
    res = select_all(Project)
    return res


def mngdb_update_project( id, **kwargs):
    updproject = update_record (Project, id, **kwargs)
    return updproject  


def mngdb_single_project(projectId):
   res = select_byid(Project, projectId)
   return res


def mngdb_single_project_ext(projectId):
   proj = select_byid(Project, projectId)
   res = q_project_select_by_project_id(projectId)
   proj['users'] = json.dumps(res)
   return proj


def mngdb_delete_project(projectId):
    res = delete_record(Project, projectId)
    return res


# Roles
def mngdb_create_role( name, code):
    newRole = insert_new(Role, Role( name = name, code=code ) , False)
    return newRole
