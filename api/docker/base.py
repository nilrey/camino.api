# import docker
import subprocess
import json
import api.sets.const as C
import api.format.response_teplates as rt # Response Template
# import random
# import string


def dkr_docker_info():
    return exeCommand(' docker info '+ C.PARAM_TO_JSON )


def dkr_images():
    return exeCommand('docker images '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_image_run(imageId, **kwargs):
    command = 'docker run -d --rm '
    param_name = param_weights = param_hyper_params = param_input = param_output = ''
    # if( not 'name' in kwargs.items()): command += ' --name '+generate_code(6)+' '
    for param, value in kwargs.items():
        if(param == 'name' and value != '' ):
            param_name += f' --name {value} '
        if(param == 'weights' ):
            param_weights += f' -v {value}:{C.CNTR_BASE_01_DIR_WEIGHTS} '
        if(param == 'hyper_params' and value != '' ):
            param_hyper_params += ""
        if(param == 'in_dir' and value != '' ):
            param_input += f' -v {value}:{C.CNTR_BASE_01_DIR_IN} '
        if(param == 'out_dir' and value != '' ):
            param_output += f' -v {value}:{C.CNTR_BASE_01_DIR_OUT} '
    # command += f' {imageId}'

    command = 'docker run -d --rm '+param_output+' '+param_input+' -it '+param_name +' ' +imageId+' --input_data \'{"datasets":[{"dataset_name": "video"}]}\''
    
    data = {'container_id': execCommand(command)}
    # data['container_data'] = dkr_container(data['container_id'])
    # data['image_data'] = dkr_container(data['container_id']['image_id'])
    return data


def dkr_containers():
    return exeCommand('docker ps '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_containers_stats():
    return exeCommand('docker stats -a --no-stream '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_container(container_id):
    return exeCommand(f'docker ps --filter "id={container_id}" '+ C.PARAM_NO_TRUNC + C.PARAM_TO_JSON )


def dkr_container_start(container_id):
    return runCommand(f'docker start {container_id} ' )


def dkr_container_stop(container_id):
    return runCommand(f'docker stop {container_id} ' )


# запуск шелл команды через сокет
def runCommand(command):
	return subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

 
def execCommand(command):
    resp = runCommand(command)
    # опредлить единый формат вывода и обработки ошибки в т.ч. Internal Server Error
    if resp.returncode == 0:
        output = resp.stdout.splitlines()
    else:
        output = {'error':resp.stderr}
    return output


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

# def generate_code(length):
#  all_symbols = string.ascii_uppercase + string.digits
#  result = ''.join(random.choice(all_symbols) for _ in range(length))
#  return result
