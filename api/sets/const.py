# Настройки для конейнеров
ROOT = "/code"

CNTR_BASE_01_DIR_WEIGHTS_FILE="/common/yolov5s.pt"
CNTR_BASE_01_DIR_IN="/input"
CNTR_BASE_01_DIR_OUT="/output"

WEIGHTS_DIR=ROOT+"/weights"
EXPORT_DIR=ROOT+"/export"
EXPORT_README=ROOT+"/api/docs/README.md"
EXPORT_EXT="tar"
EXPORT_IMAGE_SUCCESS = 'Image export success'
EXPORT_ARCH_FINISHED = 'Archive process finished'

PARAM_TO_JSON = " --format '{{json .}}' "
PARAM_NO_TRUNC = " --no-trunc "

BLOCK_LIST_IMAGES = ['idockerapi', 'vdbr/grafana', 'camino-camino-plugins', 'vdbr/monitor', 'vdbr/test', 'elestio/pgadmin', 'jrottenberg/ffmpeg', 'yiisoftware/yii2-php', 'postgres', 'inevm/camino', 'grafana/grafana-enterprise', 'postgres', 'prom/node-exporter', 'ubuntu/prometheus', 'gcr.io/cadvisor/cadvisor']
BLOCK_LIST_CONTAINERS = ['camino-back', 'camino-pgdb', 'camino-restapi', 'camino-front', 'camino-plugins', 'camino-pgadmin', 'node-exporter']