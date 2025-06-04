import os
import time
import threading 
from pathlib import Path as PathLib
import ffmpeg
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import api.sets.config as C  


class VideoConverter:
    TIME_BUFFER_TO_RUN = 3

    def __init__(self, source_dir, target_dir):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.video_files = []
        self.log_handler = None
        self.init_logger()

    def init_logger(self, type = 'file'):
        self.directory_name = C.LOG_PATH #'/home/sadmin/Work/mounts/export/logs' #
        self.file_name = f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")}_video_convreter.log'
        self.file_path = os.path.join(self.directory_name, self.file_name)
        os.makedirs(self.directory_name, exist_ok=True)
        self.log_handler = open(self.file_path, 'a+') 
        
    def logger_info(self, content):
        if self.log_handler :
            self.log_handler.write(f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")} - {content}\n')
            self.log_handler.flush()

    def logger_error(self, content):
        if self.log_handler :
            self.log_handler.write(f'{datetime.now().strftime("%Y-%m-%d_%H:%M:%S")} - Ошибка: {content}\n')
            self.log_handler.flush()

    def find_video_files(self):
        try:  
            for ext in C.VIDEO_EXT_LIST:
                self.video_files.extend(self.source_dir.glob(f'*{ext}'))
        except Exception as e:
            self.logger_error(f'Ошибка при поиске файлов в директории: {e} ')

    def convert_file(self, orig_file_path):
        target_file_path = self.target_dir / orig_file_path.with_suffix(C.PRIMARY_EXT).name
        if target_file_path.exists():
            self.logger_info(f"Файл: {target_file_path.name} существует, исключаем его из обработки.")
            return

        self.logger_info(f"Обработка: {orig_file_path.name} -> {target_file_path.name}")
        start_time = time.time()
        try:
            (
                ffmpeg
                .input(str(orig_file_path))
                .output(str(target_file_path), vcodec='libx264', acodec='aac', preset='fast')
                .overwrite_output()
                .run(quiet=True)
            )
            duration = time.time() - start_time
            self.logger_info(f"{target_file_path.name} обработан за ({duration:.1f} сек)")
        except ffmpeg.Error as e:
            self.logger_error(f"Ошибка при конвертации {orig_file_path.name}:\n{e.stderr.decode()}")

    def convert_all(self):
        try:
            with ThreadPoolExecutor(max_workers=2) as executor:
                executor.map(self.convert_file, self.video_files) 
        except Exception as e:
            self.logger_error(f"ThreadPoolExecutor, ошибка при запуске конвертации: {e}")

    def run(self):
        self.find_video_files()
        if not self.video_files:
            self.logger_error("Файлы для конвертации не найдены. Обработка закончена")
        self.target_dir.mkdir(parents=True, exist_ok=True)
        thread = threading.Thread(target=self.convert_all)
        thread.start()
        time.sleep(self.TIME_BUFFER_TO_RUN)
        message = f'Файлов в обработке: {len(self.video_files)}'
        self.logger_info(message)
        return message


# Пример использования
if __name__ == "__main__":
    source_dir = PathLib("/home/sadmin/Work/mounts/export/convert")
    target_dir = PathLib("/home/sadmin/Work/mounts/export/convert/new")
    converter = VideoConverter(source_dir, target_dir)
    resp = converter.run()
    print(resp)
    print(f"Основной поток отработал")
