import tarfile
import threading
import requests 
import datetime as dt
import subprocess
import time
from pathlib import Path
from  api.format.logger import LogManager
import api.sets.config as C
from api.sets.endpoints import ENDPOINTS
from api.lib.func_datetime import * 


class ANNExporter:
    # Класс выгрузки образа ИНС. В результате создается архив с образом, папкой набора весов и файлом инструкцией 
    def __init__(self, ann_id: str, export_data):
        self.base_path = Path(C.EXPORT_DIR)
        self.ann_id = ann_id
        self.image_id = export_data.image_id
        self.weights_path = Path(export_data.weights)
        self.export_path = self.base_path / export_data.export
        self.readme_path = Path(f"{C.EXPORT_README_PATH}/{C.EXPORT_README_FNAME}")
        self.image_tar_path = self.base_path / f"{get_dt_now_noms_nows()}_export_img_{export_data.export}"
        self.is_archiving = False  
        self.logger = LogManager("ann_export")
        self.logger.info(f"Получены параметры: {export_data}")

    def _log(self, message: str):
        self.logger.info(message)

    def _log_error(self, message: str):
        self.logger.error(message)

    def _send_ann_arch_on_save(self, ann_id):
        template = ENDPOINTS.get("ann_archive_on_save")
        if not template:
            raise ValueError("Параметр 'ann_archive_on_save' не задан.")
        url = C.HOST_RESTAPI + template.format(annId=ann_id)
        post_data = {"action":"start"}
        try:
            response = requests.post(url, json=post_data)
            response.raise_for_status()
            mes = f"Сообщение отправлено. {url}, статус: {response.status_code}"
        except requests.exceptions.RequestException as e:
            mes = f"RequestException: {url} \nОшибка: {e}"
        except Exception as e:
            mes = f"Ошибка: {e}"
        
        self.logger.info(mes)
        return mes

    def _docker_save_image(self):
        self._log(f"Экспорт Docker-образа '{self.image_id}' в файл '{self.image_tar_path.name}'.")
        result = subprocess.run(
            ["docker", "save", "-o", str(self.image_tar_path), self.image_id],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise Exception(f"Ошибка при экспорте Docker-образа: {result.stderr.strip()}")

    def _validate_paths(self):
        if not self.weights_path.is_dir():
            raise Exception(f"Папка весов не найдена: {self.weights_path}")
        if not self.readme_path.is_file():
            raise Exception(f"Файл {C.EXPORT_README_FNAME} не найден: {self.readme_path}")

    def _create_archive(self):
        self._log(f"Создание архива '{self.export_path.name}'.")
        self.is_archiving = True 
        log_thread = threading.Thread(target=self._log_archiving_progress, daemon=True)
        log_thread.start()        
        try:
            with tarfile.open(self.export_path, "w:gz") as tar:
                tar.add(self.image_tar_path, arcname=self.image_tar_path.name)
                tar.add(self.weights_path, arcname=self.weights_path.name)
                tar.add(self.readme_path, arcname=self.readme_path.name)
        finally:
            self.is_archiving = False 

    def _log_archiving_progress(self):
        while self.is_archiving:
            self._log("Процесс архивирования запущен")
            time.sleep(10)

    def _delete_tmp_image(self):
        if self.image_tar_path.exists():
            self.image_tar_path.unlink()

    def export(self):
        try:
            self._log("Начало процесса экспорта ИНС.")
            self._validate_paths()
            self._docker_save_image()
            self._create_archive()
            self._log(f"Архив успешно создан: {str(self.export_path)}")
            self._send_ann_arch_on_save(self.ann_id)
        except Exception as e:
            self._log_error(f"Ошибка при экспорте: {str(e)}")
        finally:
            self._delete_tmp_image()

    def run(self):
        thread = threading.Thread(target=self.export, daemon=True)
        thread.start()
