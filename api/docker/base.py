# import docker
import subprocess
import json
import api.sets.const as C
import api.format.response_teplates as rt # Response Template
import api.format.response_objects as ro # Response Objects


def dkr_docker_info():
    return exeCommand(' docker info '+ C.PARAM_TO_JSON )


def dkr_images():
    return exeCommand('docker images '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_image_run(image_name, params):
    command = 'docker run -d --rm '
    param_name = volume_weights = param_hyper_params = volume_input = volume_output = param_input_data = ''
    for param, value in params.items():
        if(param == 'name' and value != '' ):
            param_name += f' --name {value} '
        if(param == 'weights' ):
            volume_weights += f' -v {value}:{C.CNTR_BASE_01_DIR_WEIGHTS} '
        if(param == 'hyper_params' and value != '' ):
            param_hyper_params += ""
        if(param == 'in_dir' and value != '' ):
            volume_input += f' -v {value}:{C.CNTR_BASE_01_DIR_IN} '
            param_input_data = '--input_data \'{"datasets":[{"dataset_name": "video"}]}\''
        if(param == 'out_dir' and value != '' ):
            volume_output += f' -v {value}:{C.CNTR_BASE_01_DIR_OUT} '
    command = 'docker run -d --rm '+volume_output+' '+volume_input+' -it '+param_name +' ' +image_name+' ' + param_input_data
    return execCommand(command)


def dkr_container_create(image_name, params):
    command = 'docker create --rm '
    param_name = volume_weights = param_hyper_params = volume_input = volume_output = volume_socket = param_network = param_input_data = param_ann_mode = param_host_web = ''
    volume_socket = ' -v /var/run/docker.sock:/var/run/docker.sock '
    volume_storage = ' -v /projects_data:/projects_data '
    param_network = ' --network camino-net '
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
                param_input_data = ' --input_data \'{"path1":{}}\' '
            elif(param == 'out_dir' ):
                volume_output = f' -v {value}:{C.CNTR_BASE_01_DIR_OUT} '
            elif(param == 'video_storage'):
                volume_storage = f' -v {value}:/projects_data '
            elif(param == 'network' ):
                param_network = f' --network {value} '
            elif(param == 'host_web' ):
                param_host_web = f'--host_web \'{value}\' '

    command = 'docker create --rm ' + ' -it '+param_name + ' ' + volume_storage + ' '  + volume_output + ' '+volume_input + ' ' + volume_weights + ' ' + volume_socket + ' ' + param_network + ' ' + image_name + ' ' + param_input_data + ' ' + param_host_web + ' ' + param_ann_mode
    return exeCommand(command)


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