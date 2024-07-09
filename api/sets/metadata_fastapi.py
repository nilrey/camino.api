from fastapi import APIRouter


tags_metadata = [
    {
        "name": "Аутентификация",
        "description": "API для аутентификации",
    },
    {
        "name": "Проекты",
        "description": "API для работы с проектами",
    },
    {
        "name": "Проект / Пользователи",
        "description": "API для работы с пользователями проекта",
    },
    {
        "name": "Проект / Датасеты",
        "description": "API для работы с датасетами проекта",
    },
    {
        "name": "Проект / Датасет / Файлы",
        "description": "API для работы с файлами датасета проекта",
    },
    {
        "name": "Проект / Датасет / Цепочки примитивов",
        "description": "API для работы с цепочками примитивов",
    },
    {
        "name": "Проект / Датасет / Примитивы",
        "description": "API для работы с примитивами",
    },
    {
        "name": "Проект / Датасет / ИНС",
        "description": "API для работы с ИНС датасета проекта",
    },
    {
        "name": "Пользователи",
        "description": "API для работы с пользователями",
    },
    {
        "name": "Роли",
        "description": "API для работы с ролями пользователей",
    },
    {
        "name": "Docker",
        "description": "API для Docker",
    },
    {
        "name": "Docker-реестр",
        "description": "API для Docker-реестра",
    },
    {
        "name": "Docker-образы",
        "description": "API для работы Docker-образами",
    },
    {
        "name": "Docker-контейнеры",
        "description": "API для работы с Docker-контейнерами",
    }
]

# APIRouters
users = APIRouter( prefix="/users", tags=["Пользователи"] )
auth = APIRouter( prefix="/auth", tags=["Аутентификация"] )
projects = APIRouter( prefix="/projects", tags=["Проекты"] )
proj_users = APIRouter( prefix="/projects/{projectId}/users", tags=["Проект / Пользователи"] )
proj_datasets = APIRouter( prefix="/projects/{projectId}/datasets", tags=["Проект / Датасеты"] )
proj_dts_files = APIRouter( prefix="/projects/{projectId}/datasets/{datasetId}/files", tags=["Проект / Датасет / Файлы"] )
proj_dts_primitives = APIRouter( prefix="/projects/{projectId}/datasets/{datasetId}/markups", tags=["Проект / Датасет / Примитивы"] )
proj_dts_prim_chains = APIRouter( prefix="/projects/{projectId}/datasets/{datasetId}/chains", tags=["Проект / Датасет / Цепочки примитивов"] )
proj_dts_ann = APIRouter( prefix="/projects/{projectId}/datasets/{datasetId}/ann", tags=["Проект / Датасет / ИНС"] )
users = APIRouter( prefix="/users", tags=["Пользователи"] )
roles = APIRouter( prefix="/roles", tags=["Роли"] )
docker = APIRouter( prefix="/docker", tags=["Docker"] )
docker_registry = APIRouter( prefix="/registry", tags=["Docker-реестр"] )
docker_images = APIRouter( prefix="/images", tags=["Docker-образы"] )
docker_containers = APIRouter( prefix="/containers", tags=["Docker-контейнеры"] )
