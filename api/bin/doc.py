import docker
client = docker.from_env()
# client = docker.DockerClient(base_url='tcp://172.18.0.1:1234')

def getDockerInfo():
    return client.info()