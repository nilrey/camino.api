import logging
from datetime import datetime
import api.sets.const as C

LOG_FILE = f'{C.LOG_PATH}/{C.LOG_FNAME}_{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}.log'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Создание обработчика для записи в файл
file_handler = logging.FileHandler(f"{LOG_FILE}", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# Формат логов
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)

for handler in logger.handlers[:]:
    if isinstance(handler, logging.FileHandler):
        logger.removeHandler(handler)
        handler.close()
# Добавление обработчика (однократно)
if not logger.handlers:
    logger.addHandler(file_handler)

logger.info("Logger started")