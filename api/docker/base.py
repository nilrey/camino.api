# import docker
import subprocess
import os.path
import json
import threading

import requests 
import api.sets.const as C
import api.format.response_teplates as rt # Response Template
import api.format.response_objects as ro # Response Objects
import time, datetime as dt


def dkr_docker_info():
    return exeCommand(' docker info '+ C.PARAM_TO_JSON )


def dkr_images():
    return exeCommand('docker images '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_container_create(image_name, params):
    command = 'docker create --rm '
    param_name = volume_weights = param_hyper_params = volume_input = volume_output = volume_socket = param_network = param_input_data = param_ann_mode = param_host_web = ''
    volume_socket = ' -v /var/run/docker.sock:/var/run/docker.sock '
    volume_storage = ''
    param_network = ''
    for param, value in params.items():
        if( value ):
            if(param == 'name' ):
                param_name = f' --name {value} '
            elif(param == 'ann_mode' and value == 'teach'):
                param_ann_mode = ' --work_format_training  '
            elif(param == 'weights' ):
                volume_weights = f' -v {value}:{C.CNTR_BASE_01_DIR_WEIGHTS_FILE} '
            # elif(param == 'hyper_params'):
            #     param_hyper_params = ""
            elif(param == 'in_dir' ):
                volume_input = f' -v {value}:{C.CNTR_BASE_01_DIR_IN} '
                # param_input_data = ' --input_data \'{"path1":{}}\' '
                param_input_data = ' --input_data \'{"datasets":[{"dataset_name": "video"}]}\' '
            elif(param == 'out_dir' ):
                volume_output = f' -v {value}:{C.CNTR_BASE_01_DIR_OUT} '
            elif(param == 'video_storage'):
                volume_storage = f' -v {value}:/projects_data '
            elif(param == 'network' ):
                param_network = f' --network {value} '
            elif(param == 'host_web' ):
                param_host_web = f'--host_web \'{value}\' '

    command = 'docker create --rm ' + ' -it '+param_name + ' ' + volume_storage + ' '  + volume_output + ' '+volume_input + ' ' + volume_weights + ' ' + volume_socket + ' ' + param_network + ' ' + image_name + ' ' + param_input_data + ' ' + param_host_web + ' ' + param_ann_mode
    return execCommand(command)


def dkr_containers():
    return exeCommand('docker ps '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_containers_stats():
    return exeCommand('docker stats -a --no-stream '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_container(container_id):
    return exeCommand(f'docker ps -a --filter "id={container_id}" '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_container_start(container_id):
    return execCommand(f'docker start {container_id} ' )


def dkr_container_stop(container_id):
    return execCommand(f'docker stop {container_id} ' )

# запуск экспорта 
def dkr_ann_export(imageId, export_name, annId):
    # отправить обращение о начале работы
    t1 = threading.Thread(target=send_ann_post, args=[annId])
    t1.start()
    command = f'docker save {imageId} > {pathImgFile(export_name)} ' # выгружаем образ из докера в файл 
    logInfo(export_name, f"Выгрузка образа из докера: {command}")
    t2 = threading.Thread(target=runCommand, args=[command]) # запускаем в потоке чтобы отдать ответ сразу
    t2.start()
    return True

# запуск мониторинга текущего статуса в потоке
def prepare_ann_archive(imageId, weights, export_file, annId):
    t = threading.Thread(target=process_archive, args=[imageId, weights, export_file, annId])
    t.start()
    return True

def send_ann_post(annId):
    requests.post(f'http://camino-resapi/ann/{annId}/archive/on_save', json = {"action":"start"} )

# мониторинг текущего статуса экспорта образа
def process_archive(imageId, weights, export_file, annId):
    logInfo(export_file, "Мониторинг экспорта временного файла образа запущен.")
    while process_runs(imageId, export_file): # пока процесс висит в списке процессов - формирование образа незакончено
        time.sleep(2)
    # процесс завершен
    with open( pathLogFile(export_file) ) as f:      
        if C.EXPORT_IMAGE_SUCCESS in f.read(): #проверяем лог, если процесс окончен успешно
            if os.path.isfile( pathImgFile(export_file) ): # если файл образа существует
            # команда перейти в дир. экспорта, потом формируем архив из файла образа + файл весов + readme
                command = f'cd {C.EXPORT_DIR} && tar -zcf {nameArchFile(export_file)} {nameImgFile(export_file)} {pathWeightsFile(weights)} {pathReadmeFile()}'
                logInfo(export_file, f'Команда на архивацию: {command}')
                t = threading.Thread(target=logRunCommand, args=[export_file, command]) # запускаем в потоке чтобы перейти к мониторингу
                t.start()
            else:
                logInfo(export_file, f'Ошибка: Файл образа не найден: {pathImgFile(export_file)}')
    # мониторинг окончания архивации
    while archive_runs(export_file):
        time.sleep(2)
    # процесс завершен
    if os.path.isfile( pathArchFile(export_file) ):
        logInfo(export_file, "Файл экспорта нейросети успешно сформирован")
        os.unlink(pathImgFile(export_file))
        if os.path.isfile( pathImgFile(export_file) ):
            logInfo(export_file, "Ошибка: Временный файл образа удалить не удалось")
        else:
            logInfo(export_file, "Временный файл образа удален")
    else:
        logInfo(export_file, f"Ошибка: Файл архива нейросети не найден. {pathArchFile(export_file)} , IsFile: {os.path.isfile( pathArchFile(export_file) )}")

    return True

def archive_runs(export_file):
    with open(pathLogFile(export_file)) as f:      
        if C.EXPORT_ARCH_FINISHED in f.read(): #проверяем лог на наличие сигнала что процесс архивирования окончен
            logInfo(export_file, f'Процесс архивирования окончен' )
            return False
    logInfo(export_file, f'Процесс архивирования запущен' )
    return True

def process_runs(imageId, export_file):
    command = f'ps aux | grep "docker save {imageId}" '
    resp = runCommand(command ) # ищем в списоке процессов запущенный процесс выгрузки
    if resp.returncode == 0:
        is_running = True if resp.stdout.find(f'docker save {imageId} > ') > 0 else False # в результатах ищем нужную подстроку 
        if(is_running):
            mes = f'Процесс экспорта образа запущен'
        else:
            mes = f'Процесс экспорта образа {imageId} завершен. {C.EXPORT_IMAGE_SUCCESS}.' # Ставим метку об окончании процесса 
    else:
        # set log error
        is_running = False
        mes = f'Процесс не запущен. Ошибка: {resp.stderr} | COMMAND: {command}'
    logInfo(export_file, mes)
    return is_running

def logInfo(export_file, mes):
    with open(pathLogFile(export_file), "a") as file:
        file.write(f'{getTimeNoMsec()} {mes}\n')

def logRunCommand(export_file, command):
    try:
        response = execCommand(command )
    finally:
        logInfo(export_file, C.EXPORT_ARCH_FINISHED)
    return True

def pathLogFile(export_file):
    return f'{C.EXPORT_DIR}/{nameLogFile(export_file)}'.replace('//', '/')

def nameLogFile(export_file):
    return f'{export_file}.log'

def pathArchFile(export_file):
    return f'{C.EXPORT_DIR}/{nameArchFile(export_file)}'.replace('//', '/')

def nameArchFile(export_file):
    return f'{export_file}.tar.gz'

def pathImgFile(export_file):
    return f'{C.EXPORT_DIR}/{nameImgFile(export_file)}'.replace('//', '/')

def nameImgFile(export_file):
    return f'img_{export_file}.tar'

def pathWeightsFile(weights):
    return f'{C.WEIGHTS_DIR}/{weights}'.replace('//', '/')

def pathReadmeFile():
    return C.EXPORT_README

def getTimeNoMsec():
    return dt.datetime.now().replace(microsecond=0)

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
  except ValueError as e:
    return False
  return True