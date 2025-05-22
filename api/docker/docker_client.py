import docker
from docker import DockerClient
from docker.models.containers import Container
import api.sets.const as C

docker_client:DockerClient = docker.DockerClient(base_url=C.HOST_DOCKER_API)