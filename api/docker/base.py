# import docker
import subprocess
import json
import api.sets.const as C
import api.format.response_teplates as rt # Response Template
# import random
# import string


# def send_command(keyname, command, pause=5):
#     output = '{}'
#     with open(C.PATH_CONTAINER_HOSTPIPE+'/input/' + keyname + '.txt', 'w') as f:
#         f.write(command)
#     # time.sleep(pause)
#     with open(C.PATH_CONTAINER_HOSTPIPE+'/output/' + keyname + '.txt', 'r') as file:
#         data = file.read()
#     return data

def exeCommand(command):
    resp = runCommand(command)
    output = {'error':False, 'response': resp.stdout, 'error_descr': resp.stderr} if resp.returncode == 0 else {'error':True, 'response': resp.stdout, 'error_descr': resp.stderr} 
    return output


def addParamJSON(command_string):
    return command_string + C.PARAM_FORMAT_JSON 


def dkr_docker_info():
    command = addParamJSON("docker info ")
    return exeCommand(command)


def dkr_images():
    command = addParamJSON("docker images --no-trunc ")
    return exeCommand(command)


def dkr_image(imageId):
    # command = "docker images --no-trunc  --format '{{json .}}'  | findstr '"+imageId+"'"
    resp = {}
    for line in dkr_images()['response'].splitlines():
        values = json.loads(line)
        if values['ID'] == 'sha256:'+imageId : resp = values
    return  {'error':False, 'response':resp, 'error_descr': ''}


def dkr_image_run(imageId, **kwargs):
    command = 'docker run -d --rm '

    # if( not 'name' in kwargs.items()):
    #     command += ' --name '+generate_code(6)+' '
  
    for param, value in kwargs.items():
        if(param == 'name' and value != '' ):
            command += f' --name {value} '
        if(param == 'weights' ):
            command += f' -v {value}:{C.CNTR_BASE_01_DIR_WEIGHTS} '
        if(param == 'hyper_params' and value != '' ):
            command += ""
        if(param == 'in_dir' and value != '' ):
            command += f' -v {value}:{C.CNTR_BASE_01_DIR_IN} '
        if(param == 'out_dir' and value != '' ):
            command += f' -v {value}:{C.CNTR_BASE_01_DIR_OUT} '
    command += f' {imageId}'

    data = {'container_id': execCommand(command)}
    # data['container_data'] = dkr_container(data['container_id'])
    # data['image_data'] = dkr_container(data['container_id']['image_id'])

    return rt.dkr_image_run(data)


def dkr_containers_():
    # command = 'docker ps --format "{{.ID}},{{.Image}},{{.Command}},{{.CreatedAt}},{{.Status}},{{.Ports}},{{.Names}}" --no-trunc '
    command = 'docker ps --no-trunc '
    containers = execCommand(command)
    images = dkr_images()
    return rt.dkr_containers(containers, images['items'] )

def dkr_containers():
    command = addParamJSON("docker ps --no-trunc ")
    return exeCommand(command)

def dkr_containers_stats():
    command = 'docker container stats -a --no-stream '
    return rt.dkr_containers_stats(execCommand(command))


def dkr_container(container_id):
    command = "docker ps --filter ''id=" + container_id + "'' " 
    return rt.dkr_container(execCommand(command))


# запуск шелл команды через сокет
def runCommand(command):
	return subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
	# return subprocess.run(command, shell=True)

# 
def execCommand(command):
    resp = runCommand(command)
    # опредлить единый формат вывода и обработки ошибки в т.ч. Internal Server Error
    if resp.returncode == 0:
        output = resp.stdout.splitlines()
    else:
        output = {'error':resp.stderr}
    return output

# def generate_code(length):
#  all_symbols = string.ascii_uppercase + string.digits
#  result = ''.join(random.choice(all_symbols) for _ in range(length))
#  return result