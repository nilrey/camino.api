# Настройки для конейнеров
HOST_RESTAPI = "http://camino-restapi"
HOST_GRAFANA = "http://10.0.0.1:3000"

ROOT = "/code"

CNTR_BASE_01_DIR_WEIGHTS_FILE="/common/yolov5s.pt"
CNTR_BASE_01_DIR_IN="/input_videos"
CNTR_BASE_01_DIR_OUT="/output"

LOG_DIR = "/export/logs"
LOG_PATH = ROOT+LOG_DIR

WEIGHTS_DIR = ROOT+"/weights"
EXPORT_DIR = ROOT+"/export"
EXPORT_README_PATH = ROOT+"/api/docs"
EXPORT_README_FNAME = "README.md"
EXPORT_EXT="tar"
EXPORT_IMAGE_SUCCESS = 'Image export success'
EXPORT_ARCH_FINISHED = 'Archive process finished'

PARAM_TO_JSON = " --format '{{json .}}' "
PARAM_NO_TRUNC = " --no-trunc "

BLOCK_LIST_IMAGES = ['idockerapi', 'vdbr/grafana', 'camino-camino-plugins', 'vdbr/monitor', 'vdbr/test', 'elestio/pgadmin', 'jrottenberg/ffmpeg', 'yiisoftware/yii2-php', 'postgres', 'inevm/camino', 'grafana/grafana-enterprise', 'postgres', 'prom/node-exporter', 'ubuntu/prometheus', 'gcr.io/cadvisor/cadvisor']
BLOCK_LIST_CONTAINERS = ['camino-back', 'camino-pgdb', 'camino-restapi', 'camino-front', 'camino-plugins', 'camino-pgadmin', 'node-exporter']

SET_MAX_WORKERS = 2

# DB_SCHEMA = 'public'
# TABLE_CHAINS = 'chains_copy'
# TABLE_MARKUPS = 'markups_copy'
# TABLE_MARKUPS_CHAINS = 'markups_chains_copy'
# DB_CHAINS = "{DB_SCHEMA}.{TABLE_CHAINS}"
# DB_MARKUPS = "{DB_SCHEMA}.{TABLE_MARKUPS}"
# DB_MARKUPS_CHAINS = "{DB_SCHEMA}.{TABLE_MARKUPS_CHAINS}"