PATH_DOCKER_MANAGER="/home/sadmin/Work/dockermanager"
PATH_CONTAINER_HOSTPIPE="/code/api/docker/hostpipe"
# Настройки для конейнеров
CNTR_BASE_01_DIR_WEIGHTS="/weights"
CNTR_BASE_01_DIR_IN="/input"
CNTR_BASE_01_DIR_OUT="/output"

PARAM_TO_JSON = " --format '{{json .}}' "
PARAM_NO_TRUNC = " --no-trunc "

BLOCK_LIST_IMAGES = ['idockerapi', 'vdbr/grafana', 'camino-camino-plugins', 'vdbr/monitor', 'vdbr/test', 'elestio/pgadmin', 'jrottenberg/ffmpeg', 'yiisoftware/yii2-php', 'postgres', 'inevm/camino', 'grafana/grafana-enterprise', 'postgres', 'prom/node-exporter', 'ubuntu/prometheus', 'gcr.io/cadvisor/cadvisor']
BLOCK_LIST_CONTAINERS = ['camino-back', 'camino-pgdb', 'camino-restapi', 'camino-front', 'camino-plugins', 'camino-pgadmin', 'node-exporter']