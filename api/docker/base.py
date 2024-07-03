# import docker
import os

# client = docker.from_env()
# client = docker.DockerClient(base_url='tcp://172.18.0.1:1234')


def dkr_get_info():
    file_path = os.path.realpath(__file__)
    data = os.path.dirname(file_path)
    with open("/code/api/docker/hostpipe/input/status.txt", "r") as file:
        data = file.read()
    return data


def dkr_image_run(imageId):
    # file_path = os.path.realpath(__file__)
    # root = os.path.dirname(file_path)
    resp = False
    with open('/code/api/docker/hostpipe/input/params.txt', 'w') as f:
        f.write(imageId+" start cmockneuro")
        resp = True
    return resp

def dkr_container_stats(containerId):
    
    return True