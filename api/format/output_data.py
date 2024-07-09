import json


def dkr_docker_info(data):
    outjson = json.loads('{"version": "string","containers": {"running": 0,"paused": 0,"stopped": 0,"total": 0},"images": 0,"cpus": 0,"mem": "string"}')
    return outjson


def dkr_images(data):
    outjson=json.loads('{"images": [{"id": "583407a61900","name": "library/ann","tag": "v1","location": "registry","created_at": "2024-07-04 10:33:15","size": "1.07 GB","comment": "Added Apache to Fedora base image","is_archived": true}]}')
    return outjson


def dkr_image(data):
    outjson=json.loads('{"id": "583407a61900","name": "library/ann","tag": "v1","location": "registry","created_at": "2024-07-04 10:33:15","size": "1.07 GB","comment": "Added Apache to Fedora base image","is_archived": true}')
    return outjson

def dkr_image_mock(data):
    outjson=json.loads('{"id": "' + data[0] + '","name": "library/ann","tag": "v1","location": "registry","created_at": "2024-07-04 10:33:15","size": "1.07 GB","comment": "Added Apache to Fedora base image","is_archived": true}')
    return outjson


def dkr_image_run(data):
    outjson='{"id": "583407a61900","image": {"id": "583407a61900","name": "library/ann","tag": "v1"},"command": "top","names": "ann","ports": "8080/tcp","created_at": "2024-07-04 10:33:15","status": "Up 1 hour"}'
    return outjson


def dkr_containers(data):
    outjson='{"containers": [{"id": "583407a61900","image": {"id": "583407a61900","name": "library/ann","tag": "v1"},"command": "top","names": "ann","ports": "8080/tcp","created_at": "2024-07-04 10:33:15","status": "Up 1 hour"}]}'
    return outjson


def dkr_containers_stats(data):
    outjson='{"containers": [{"id": "583407a61900","state": "running","cpu": "0.15%","mem": "0.25%","mem_use": "25MiB","size": "1.07 GB"}]}'
    return outjson


def dkr_container(data):
    outjson='{"id": "583407a61900","image": {"id": "583407a61900","name": "library/ann","tag": "v1"},"command": "top","names": "ann","ports": "8080/tcp","created_at": "2024-07-04 10:33:15","status": "Up 1 hour"}'
    return outjson


def dkr_container_stats(data):
    outjson='{"id": "583407a61900","state": "running","cpu": "0.15%","mem": "0.25%","mem_use": "25MiB","size": "1.07 GB"}'
    return outjson