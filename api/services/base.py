# import docker
import shutil
import subprocess
import os.path
import json
import threading

import requests 
import api.sets.config as C
import api.format.response_teplates as rt # Response Template
import api.format.response_objects as ro # Response Objects
import time, datetime as dt

from  api.format.logger import logger


def dkr_docker_info():
    return exeCommand(' docker info '+ C.PARAM_TO_JSON )

def dkr_images():
    command = 'docker images '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON 
    logger.info(command)
    return exeCommand(command)

def dkr_containers():
    return exeCommand('docker ps '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_containers_stats():
    # logger = init_logger()
    command = 'docker stats -a --no-stream '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON 
    logger.info(command)
    res = exeCommand(command)
    m = "Recieve Not Json response"
    if isJson(res):
        m = "Recieve Json response"
    logger.info(m)
    logger.info(res)
    return res


def dkr_container(container_id):
    return exeCommand(f'docker ps -a --filter "id={container_id}" '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_container_start(container_id):
    return execCommand(f'docker start {container_id} ' )


def dkr_container_stop(container_id):
    return execCommand(f'docker stop {container_id} ' )

# запуск экспорта 
def dkr_ann_export(imageId, export_code, annId):
    execCommand(f'mkdir {C.EXPORT_DIR}/tmp_{export_code}')
    command = f'docker save {imageId} > {img_file_path(export_code)} ' # выгружаем образ из докера в файл 
    logger.info(f"Выгрузка образа из докера: {command}")
    threading.Thread(target=runCommand, args=[command]).start() # запускаем в потоке чтобы отдать ответ сразу
    return True


# запуск мониторинга текущего статуса в потоке
def prepare_ann_archive(imageId, weights, export_code, annId):
    t = threading.Thread(target=process_archive, args=[imageId, weights, export_code, annId])
    t.start()
    return {"status":"running"}


# мониторинг текущего статуса экспорта образа
def process_archive(imageId, weights, export_code, annId):
    logger.info("Мониторинг экспорта временного файла образа запущен.")
    while process_runs(imageId, export_code, annId): # пока процесс висит в списке процессов - формирование образа незакончено
        time.sleep(2)
    # процесс завершен
    with open( log_file_path(export_code) ) as f:      
        if C.EXPORT_IMAGE_SUCCESS in f.read(): #проверяем лог, если процесс окончен успешно
            if os.path.isfile( img_file_path(export_code) ): # если файл образа существует
            # команда перейти в дир. экспорта, потом формируем архив из файла образа + файл весов + readme
                command = f'cd {C.EXPORT_DIR} && tar -zcf {arch_file_path(export_code)} {tar_img_file(export_code)} {tar_weights_file(weights)} {tar_readme_file()}'
                logger.info(f'Команда на архивацию: {command}')
                threading.Thread(target=run_command_with_finally, args=[export_code, command]).start() # запускаем в потоке чтобы перейти к мониторингу
            else:
                msg = f'Ошибка: Файл образа не найден: {img_file_path(export_code)}'
                logger.info(msg)
                send_on_error(export_code, annId, msg)
    # мониторинг окончания архивации
    while archive_runs(export_code):
        time.sleep(2)
    # процесс завершен
    threading.Thread(target=send_arch_on_save, args=[export_code, annId]).start() # отправить сообщение о завершении работы
    if os.path.isfile( arch_file_path(export_code) ):
        logger.info("Файл экспорта нейросети успешно сформирован")
        shutil.rmtree(img_path(export_code))
        if os.path.isfile( img_file_path(export_code) ):
            logger.info("Ошибка: Временный файл образа удалить не удалось")
        else:
            logger.info("Временный файл образа удален")
    else:
        msg = f"Ошибка: Файл архива нейросети не найден. {arch_file_path(export_code)} , IsFile: {os.path.isfile( arch_file_path(export_code) )}"
        logger.info(msg)
        send_on_error(export_code, annId, msg)
    return True

def archive_runs(export_code):
    with open(log_file_path(export_code)) as f:      
        if C.EXPORT_ARCH_FINISHED in f.read(): #проверяем лог на наличие сигнала что процесс архивирования окончен
            logger.info(f'Процесс архивирования окончен' )
            return False
    logger.info(f'Процесс архивирования запущен' )
    return True

def process_runs(imageId, export_code, annId):
    command = f'ps aux | grep "docker save {imageId}" '
    resp = runCommand(command ) # ищем в списоке процессов запущенный процесс выгрузки
    if resp.returncode == 0:
        is_running = True if resp.stdout.find(f'docker save {imageId} > ') > 0 else False # в результатах ищем нужную подстроку 
        if(is_running):
            msg = f'Процесс экспорта образа запущен'
        else:
            msg = f'Процесс экспорта образа {imageId} завершен. {C.EXPORT_IMAGE_SUCCESS}.' # Ставим метку об окончании процесса 
    else:
        # set log error
        is_running = False
        msg = f'Процесс не запущен. Ошибка: {resp.stderr} | COMMAND: {command}'
        send_on_error(export_code, annId, msg)
    logger.info(msg)
    return is_running

# def logger.info(mes):
    # with open(log_file_path(export_code), "a") as file:
    #     file.write(f'{get_time_no_microsec()} {mes}\n')

def run_command_with_finally(export_code, command):
    msg = ""
    try:
        execCommand(command )
        msg = f"Команда успешно выполенена. {command}"
    except Exception:
        msg = f"Ошибка: Команда выполенена с ошибкой. {command}"
    finally:
        logger.info(C.EXPORT_ARCH_FINISHED)
        logger.info(msg)
    return True

def log_file_path(export_code):
    dir = f'{C.LOG_PATH}' if(os.path.isdir(f'{C.LOG_PATH}')) else C.EXPORT_DIR # если сущ. директория для логов
    logger.info(f'Директория логов: {dir}')
    return f'{dir}/{log_fname(export_code)}'

def log_fname(export_code):
    return f'{export_code}.log'

def arch_file_path(export_code):
    return f'{C.EXPORT_DIR}/{arch_fname(export_code)}'

def arch_fname(export_code):
    return f'{export_code}.tar.gz'

def img_file_path(export_code):
    return f'{img_path(export_code)}/{img_fname(export_code)}'

def img_path(export_code):
    return f'{C.EXPORT_DIR}/tmp_{export_code}' if(os.path.isdir(f'{C.EXPORT_DIR}/tmp_{export_code}')) else C.EXPORT_DIR 

def tar_img_file(export_code):
    return f' -C {C.EXPORT_DIR}/tmp_{export_code} {img_fname(export_code)} '

def img_fname(export_code):
    return f'img_{export_code}.tar'

def tar_weights_file(weights):
    return f' -C {C.WEIGHTS_DIR} {weights} '

def tar_readme_file():
    return f' -C {C.EXPORT_README_PATH} {C.EXPORT_README_FNAME} '

def get_time_no_microsec():
    return dt.datetime.now().replace(microsecond=0)

def get_time_today_no_sec():
    return dt.datetime.now().strftime("%Y%m%d_%H:%M")

def send_arch_on_save(export_code, annId):
    url = f'{C.HOST_RESTAPI}/ann/{annId}/archive/on_save'
    try:
        requests.post(url, json = {"action":"start"} )
        mes = f"Сообщение отправлено. {url}"
    except Exception:
        mes = f"Ошибка: сообщение не отправлено. {url}"
    finally:
        logger.info(mes)

def send_on_error(export_code, annId, msg):
    url = f'{C.HOST_RESTAPI}/ann/{annId}/archive/on_error'
    try:
        requests.post(url, json = {"msg": msg} )
        mes = f"Сообщение об ошибке отправлено: {msg}. {url}"
    except Exception as e:
        mes = f"Ошибка: сообщение не отправлено.{e}. {url}"
    finally:
        logger.info(mes)

# запуск шелл команды через сокет
def runCommand(command):
	return subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

 
def execCommand(command):
    resp = runCommand(command)
    is_error = True
    # опредлить единый формат вывода и обработки ошибки в т.ч. Internal Server Error
    if resp.returncode == 0:
        is_error = False
    else:
        output = {'error':resp.stderr}
    return {'command':command, 'error': is_error, 'response': resp.stdout.splitlines() if(type(resp.stdout).__name__ == "str") else resp.stdout , 'error_descr': resp.stderr} 


def noFormatResponse(command):
    return  exeCommand(command)


def exeCommand(command):
    resp = runCommand(command)
    # cmd возвращает некорректный json (не хватает квадратных скобок и запятых в списке между элементами), в данной строке исправляем json
    resp_stdout = resp.stdout
    is_error = True
    if resp.returncode == 0 and type(resp.stdout).__name__ == "str":
        response_json = '['+ resp.stdout.replace('}\n{', '},\n{') + ']'
        if( isJson(response_json)):
            resp_stdout = response_json
            is_error = False
        else:
            resp.stderr = "Формат не распознан. Убедитесь, что данные представлены в формате JSON"
    output = {'command':command, 'error': is_error, 'response': resp_stdout, 'error_descr': resp.stderr} 
    return output


def isJson(str):
  try:
    json.loads(str)
  except Exception as e:
    return False
  
  return True