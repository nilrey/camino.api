import json
import re

def stringSplit(str):
    output = re.sub(r'\s\s+', '^-^', str).split('^-^')
    return output

def replaceHeaderTitles(headers, title_aliases={}):
    newheaders = []
    for header in headers:
        if header in title_aliases.keys():
            newheader = header.replace(header, title_aliases[header]) 
            newheaders.append(newheader)
        else:
            newheaders.append(header)
    return newheaders


def getPagination(cnt):
    return { "page": 1, "pageSize": cnt, "totalItems": cnt, "totalPages": 1}


def getItems(data, headers=[], extendValues = []):
    items = []
    for line in data:
        values = stringSplit(line)
        values.extend(extendValues)
        items.append(dict(zip(headers, values)))
    return items


def dkr_docker_info(data):
    outjson = json.loads('{"version": "string","containers": {"running": 0,"paused": 0,"stopped": 0,"total": 0},"images": 0,"cpus": 0,"mem": "string"}')
    return outjson


def dkr_images(data):
    title_aliases = {'IMAGE ID':'id', 'REPOSITORY':'name', 'TAG':'tag', 'location':'location', 'CREATED':'created_at', 'SIZE':'size'}
    headers = replaceHeaderTitles( stringSplit(data.pop(0)) , title_aliases)
    headers.extend(['location', 'comment', 'archive'])
    extendValues = ['registry', 'Added Apache to Fedora base image', 'string']
  
    items = getItems(data, headers, extendValues)
    return {'pagination':getPagination(len(items)), 'items':items}


def dkr_image(data):
    images = dkr_images(data)
    return images['items'][0]


def dkr_image_run(data):
    #1 Получить данные о контейнере 
    #2 ПОлучить данные об образе
    outjson='{"id": "583407a61900","image": {"id": "583407a61900","name": "library/ann","tag": "v1"},"command": "top","names": "ann","ports": "8080/tcp","created_at": "2024-07-04 10:33:15","status": "Up 1 hour"}'
    return outjson


def dkr_containers(data, images):
    # outjson='{"containers": [{"id": "583407a61900","image": {"id": "583407a61900","name": "library/ann","tag": "v1"},"command": "top","names": "ann","ports": "8080/tcp","created_at": "2024-07-04 10:33:15","status": "Up 1 hour"}]}'
    title_aliases = {'CONTAINER ID':'id', 'COMMAND':'command', "NAMES":"names", "PORTS":"ports", "CREATED":"created_at", "STATUS":"status", "IMAGE":"image", }
    headers = replaceHeaderTitles( stringSplit(data.pop(0)) , title_aliases)
    extendValues = ['registry', 'Added Apache to Fedora base image', 'string']
    
    items = getItems(data, headers, extendValues)
    imagesIds = {}
    # for container in items:
    #     for image in images:
    #         if container['image'] == image["name"]:
    #             container.

    return {'pagination':getPagination(len(items)), 'items':items, 'iamgesIds':imagesIds}


def dkr_containers_stats(data):
    # outjson='{"containers": [{"id": "583407a61900","state": "running","cpu": "0.15%","mem": "0.25%","mem_use": "25MiB","size": "1.07 GB"}]}'
    headers = stringSplit(data.pop(0)).split(' ')
    dictionary = []
    for line in data:
        values = stringSplit(line).split(' ')
        dictionary.append(dict(zip(headers, values)))
    return dictionary

def dkr_container(data):
    headers = stringSplit(data.pop(0))
    dictionary = []
    for line in data:
        values = stringSplit(line)
        dictionary.append(dict(zip(headers, values)))
    return dictionary


def dkr_container_stats(data):
    outjson='{"id": "583407a61900","state": "running","cpu": "0.15%","mem": "0.25%","mem_use": "25MiB","size": "1.07 GB"}'
    return outjson