# import docker
import os
import time
import api.sets.const as C
import api.format.output_data as tojson
import json
import subprocess
import random
import string
# client = docker.from_env()
# client = docker.DockerClient(base_url='tcp://172.18.0.1:1234')


def send_command(keyname, command, pause=5):
    output = '{}'
    with open(C.PATH_CONTAINER_HOSTPIPE+'/input/' + keyname + '.txt', 'w') as f:
        f.write(command)
    # time.sleep(pause)
    with open(C.PATH_CONTAINER_HOSTPIPE+'/output/' + keyname + '.txt', 'r') as file:
        data = file.read()
    return data


def dkr_docker_info():
    # file_path = os.path.realpath(__file__)
    # data = os.path.dirname(file_path)
    resp = send_command('docker_info', 'docker_info')
    return tojson.dkr_docker_info(resp)


def dkr_images():
    resp = send_command('images', 'images_all')
    return tojson.dkr_images(resp)


def dkr_image(imageId):
    # resp = send_command('image', imageId)
    # return tojson.dkr_image(resp)
    return tojson.dkr_image_mock([imageId] )


def dkr_image_run(imageId, **kwargs):
    command = 'docker run -d --rm '

    if( not 'name' in kwargs.items()):
        command += ' --name '+generate_code(6)+' '
  
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

    data = execCommand(command)
    return {'id':data}


def get_containers_from_docker():
    '''Получение списка активных контейнеров от docker
    Return: словарь вида full_id:name
    '''
    output = '{"status":"READY"}'
    out = {}
    try:
        result = subprocess.run('docker ps --format "{{.ID}}: {{.Names}}" --no-trunc', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result :
            for line in result.stdout.splitlines():
                if ': ' in line:
                    output = '{"status":"resultnotnull"}'
                    key, value = line.split(': ')
                    out[key] = value
            output = json.dumps(out)
    except subprocess.CalledProcessError as e:
        output = '{"status":"error "}'#+e.output

    return output
    
def dkr_containers():
    # command = 'docker ps --format "{{.ID}},{{.Image}},{{.Command}},{{.CreatedAt}},{{.Status}},{{.Ports}},{{.Names}}" --no-trunc '
    command = 'docker ps --no-trunc '
    return tojson.dkr_containers(execCommand(command))


def dkr_containers_stats():
    command = 'docker container stats -a --no-stream '
    return tojson.dkr_containers_stats(execCommand(command))


def dkr_container(containerId):
    resp = send_command('container', containerId)
    return tojson.dkr_container(resp)


def dkr_container_stats(containerId):
    resp = send_command('container_stats', containerId)
    return tojson.dkr_container_stats(resp)

# запуск шелл команды через сокет
def runCommand(command):
	return subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# 
def execCommand(command):
    resp = runCommand(command)
    # опредлить единый формат вывода и обработки ошибки в т.ч. Internal Server Error
    if resp.returncode == 0:
        output = resp.stdout.splitlines()
    else:
        output = {'error':resp.stderr}
    return output

def generate_code(length):
 all_symbols = string.ascii_uppercase + string.digits
 result = ''.join(random.choice(all_symbols) for _ in range(length))
 return result