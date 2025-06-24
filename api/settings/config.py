# Настройки адресации конейнеров
HOST_RESTAPI = "http://camino-restapi" # хост либо домен контейнера camino-restapi
HOST_GRAFANA = "http://10.0.0.1:3000" # хост либо домен контейнера grafana
HOST_ANN = "http://10.0.0.1:8000" # хост либо домен контейнера camino-restapi для отправки сообщений из контейнера с привязкой к порту
HOST_REGISTRY = "10.0.0.1:6000" # хост либо домен где располагается репозиторий образов ИНС, с привязкой к порту

# Управление режимом отладки
DEBUG_MODE = True # указать False

# Настроки файловой структуры
ROOT = "/code" # корневая директория в развернутом контейнере, в которой расположен проект

# Файл подключения к базе данных
POSTGRES_CONNECT = ROOT+"/api/settings/config.py"
# Разделы для VOLUMES при создании контейнера
WEIGHTS_DIR = "/weights"
EXPORT_DIR = "/export"

EXPORT_README_PATH = ROOT+"/api/docs" # Раздел для хранения документации при создании архива образа
LOG_PATH = "/export/logs" # корневая директория в развернутом контейнере, в которой расположены логи проекта
LOG_FNAME = "back" # условное обозначение лог-файла, полное название имеет вид: "Y-m-d_H:M:S_<LOG_FNAME>.log"


EXPORT_README_FNAME = "Readme.md" # файл инструкции для добавления в архив, при экспорте ИНС 
EXPORT_IMAGE_SUCCESS = 'Image export success'
EXPORT_ARCH_FINISHED = 'Archive process finished'

PARAM_TO_JSON = " --format '{{json .}}' "
PARAM_NO_TRUNC = " --no-trunc "

BLOCK_LIST_IMAGES = ['idockerapi', 'vdbr/grafana', 'camino-camino-plugins', 'vdbr/monitor', 'vdbr/test', 'elestio/pgadmin', 'jrottenberg/ffmpeg', 'yiisoftware/yii2-php', 'postgres', 'inevm/camino', 'grafana/grafana-enterprise', 'postgres', 'prom/node-exporter', 'ubuntu/prometheus', 'gcr.io/cadvisor/cadvisor', 'registry']
BLOCK_LIST_CONTAINERS = ['camino-back', 'camino-pgdb', 'camino-restapi', 'camino-front', 'camino-plugins', 'camino-pgadmin', 'grafana', 'prometheus', 'cadvisor', 'node-exporter', 'registry']

HOST_VM = {"name": "vm1", "host": "172.17.0.1", "port": 2375}
VIRTUAL_MACHINES_LIST = [
    {"name": "vm1", "host": "172.17.0.1", "port": 2375},
    # {"name": "vm2", "host": "172.17.0.2", "port": 2375},
]

ANN_IMAGES_LIST = ['bytetracker-image', 'ynp_inf', 'deeplab', 'sam']

VIDEO_EXT_LIST = ['.avi', '.m4v', '.mov', '.mpg', '.mpeg', '.wmv']
PRIMARY_EXT = '.mp4'

SET_MAX_WORKERS = 2
SET_SHM_SIZE = 20 # размер shm при старте контейнера

# DB_SCHEMA = 'public'
# TABLE_CHAINS = 'chains_copy'
# TABLE_MARKUPS = 'markups_copy'
# TABLE_MARKUPS_CHAINS = 'markups_chains_copy'
# DB_CHAINS = "{DB_SCHEMA}.{TABLE_CHAINS}"
# DB_MARKUPS = "{DB_SCHEMA}.{TABLE_MARKUPS}"
# DB_MARKUPS_CHAINS = "{DB_SCHEMA}.{TABLE_MARKUPS_CHAINS}"