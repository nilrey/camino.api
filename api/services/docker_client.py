import docker
from docker.errors import APIError

HOST_VM = {"name": "vm1", "host": "172.17.0.1", "port": 2375}

def get_docker_client(host = HOST_VM['host'], port = HOST_VM['port'], protocol = 'tcp'):
    try:
        client = docker.DockerClient(base_url=f"{protocol}://{host}:{port}")
        return client
    except APIError as e:
        raise Exception(f"Ошибка DockerClient: {e}")