# import docker
import subprocess
import os.path
import json
import threading 
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
                volume_weights = f' -v {value}:{C.CNTR_BASE_01_DIR_WEIGHTS} '
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
def dkr_ann_export(imageId, file_path):
    command = f'docker save {imageId} > {file_path} ' # выгружаем образ из докера в файл 
    t = threading.Thread(target=runCommand, args=[command]) # запускаем в потоке чтобы отдать ответ сразу
    t.start()
    return True

# запуск мониторинга текущего статуса в потоке
def start_monitoring_status(imageId, export_file):
    t = threading.Thread(target=monitoring_status, args=[imageId, export_file])
    t.start()
    return True

# мониторинг текущего статуса экспорта образа
def monitoring_status(imageId, export_file):
    while process_runs(imageId, export_file): # пока процесс висит в списке процессов - формирование образа незакончено
        time.sleep(2)
    # процесс завершен
    with open( pathLogFile(export_file) ) as f:      
        if C.EXPORT_IMAGE_SUCCESS in f.read(): #проверяем лог, если процесс окончен успешно
            if os.path.isfile( pathImgFile(export_file) ): # если файл образа существует
            # команда перейти в дир. экспорта, потом формируем архив из файла образа + файл весов + readme
                command = f'cd {C.EXPORT_DIR} && tar -cf {pathArchFile(export_file)} {pathImgFile(export_file)} README.md'
                logInfo(export_file, f'Команда на архивацию: {command}')
                t = threading.Thread(target=logRunCommand, args=[export_file, command]) # запускаем в потоке чтобы отдать ответ сразу
                t.start()
            else:
                logInfo(export_file, f'Ошибка: Файл образа не найден: {pathImgFile(export_file)}')
    # мониторинг окончания архивации
    while archive_runs(export_file):
        time.sleep(2)
    # процесс завершен
    if os.path.isfile( pathArchFile(export_file) ): # файл архива нейросети сформирован 
        logInfo(export_file, "Экспорт нейросети завершен успешно")
        os.unlink(pathImgFile(export_file))
        if os.path.isfile( pathImgFile(export_file) ):
            logInfo(export_file, "Ошибка: Временный файл образа удалить не удалось")
        else:
            logInfo(export_file, "Временный файл образа удален")
    else:
        logInfo(export_file, f"Ошибка: Файл архива нейросети не найден. {pathArchFile(export_file)} , \
                IsFile: {os.path.isfile( pathArchFile(export_file) )}")

    return True

def archive_runs(export_file):
    log_file = pathLogFile(export_file)
    if not os.path.isfile(log_file):
        logInfo(export_file, f'Лог файл не найден. {log_file}' )
        return False
    
    with open(log_file) as f:      
        if C.EXPORT_ARCH_FINISHED in f.read(): #проверяем лог на наличие сигнала что процесс архивирования окончен
            logInfo(export_file, f'Процесс архивирования окончен {dt.datetime.now().timestamp()}' )
            return False
    logInfo(export_file, f'Процесс архивирования запущен {dt.datetime.now().timestamp()}' )
    return True

def process_runs(imageId, export_file):
    command = f'ps aux | grep "docker save {imageId}" '
    resp = runCommand(command )    
    if resp.returncode == 0:
        is_running = True if resp.stdout.find(f'docker save {imageId} > ') > 0 else False
        proc_cnt  = len(resp.stdout.splitlines() )
        if(is_running):
            mes = f'Процесс запущен | {is_running=} | {proc_cnt=} | COMMAND: {command}\n'
        else:
            mes = f'Процесс экспорт образа {imageId} завершен. {C.EXPORT_IMAGE_SUCCESS}.'
            if os.path.isfile( pathImgFile(export_file) ):
                mes = mes + f" Файл образа '{pathImgFile(export_file)}'"
            else:
                mes = mes + " Файл не обнаружен"
    else:
        # set log error
        is_running = False
        proc_cnt = 0
        mes = f'Процесс не запущен. Ошибка: {resp.stderr} | COMMAND: {command}'

    logInfo(export_file, mes)

    return is_running

def logInfo(export_file, mes):
    with open(pathLogFile(export_file), "a") as file:
        file.write(f'{mes}\n')

def logRunCommand(export_file, command):
    try:
        response = execCommand(command )
    finally:
        logInfo(export_file, C.EXPORT_ARCH_FINISHED)
    return True

def pathLogFile(export_file):
    return f'{C.EXPORT_DIR}/{export_file}.log'

def pathArchFile(export_file):
    return f'{C.EXPORT_DIR}/{export_file}.tar'

def pathImgFile(export_file):
    return f'{C.EXPORT_DIR}/img_{export_file}.tar'

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