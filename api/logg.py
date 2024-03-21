from loguru import logger


logger.add("./api/log/logfile.log", format="{time:YYYY-MM-DD HH:mm:ss} [{level}] {message}", level="DEBUG", rotation="10 Kb", compression="zip")