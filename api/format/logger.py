# import logging
from datetime import datetime
import os 
import api.sets.config as C

LOG_FILE = f'{C.LOG_PATH}/{C.LOG_FNAME}_{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}.log'

class LogManager:
    def __init__(self, log_name = C.LOG_FNAME):
        self.directory_name = C.LOG_PATH
        self.file_name = f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_{log_name}.log'
        self.file_path = os.path.join(self.directory_name, self.file_name)
        os.makedirs(self.directory_name, exist_ok=True)
        self.handler = open(self.file_path, 'a+')
        
    def info(self, content):
        self.handler.write(f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")} - {content}\n')
        self.handler.flush()

    def error(self, content):
        self.handler.write("Ошибка: " + content + "\n")
        self.handler.flush()

    def __del__(self):
        if self.handler:
            self.handler.close()

logger = LogManager()
logger.info("Log enabled")