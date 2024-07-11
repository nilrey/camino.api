import json
import re

def replaceSpaces(str):
    replacements = {' / ': '/', ', ': ',', 'CONTAINER ID':'CONTAINER_ID', ' %':'%', ' I/O':'_I/O', 'IMAGE ID':'IMAGE_ID', ' second ':'_second_', ' seconds ':'_seconds_', ' minutes ':'_minutes_', ' minute ':'_minute_'
                   , ' hours ':'_hours_', ' day ':'_day_', ' days ':'_days_', ' week ':'_week_', ' weeks ':'_weeks_', ' month ':'_month_', ' months ':'_months_', ' year ':'_year_', ' years ':'_years_'}
    for replaceFrom, replaceTo in replacements.items():
        str = str.replace(replaceFrom, replaceTo)
    output = re.sub(r'\s+', ' ', str)
    return output

def replaceHeaderTitles(headers, replacements):
    newheaders = []
    for header in headers:
        if header in replacements.keys():
            newheader = header.replace(header, replacements[header]) 
            newheaders.append(newheader)
        else:
            newheaders.append(header)
    return newheaders

def dkr_docker_info(data):
    outjson = json.loads('{"version": "string","containers": {"running": 0,"paused": 0,"stopped": 0,"total": 0},"images": 0,"cpus": 0,"mem": "string"}')
    return outjson


def dkr_images(data):
    items = []
    headers = replaceHeaderTitles( replaceSpaces(data.pop(0)).split(' ') )
    headers.extend(['location', 'comment', 'archive'])
    for line in data:
        values = replaceSpaces(line).split(' ')
        values.extend(['registry', 'Added Apache to Fedora base image', 'string'])
        items.append(dict(zip(headers, values)))
    page = { "page": 1, "pageSize": len(items), "totalItems": len(items), "totalPages": 1}
    return {'pagination':page, 'items':items}


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
    # outjson='{"containers": [{"id": "583407a61900","image": {"id": "583407a61900","name": "library/ann","tag": "v1"},"command": "top","names": "ann","ports": "8080/tcp","created_at": "2024-07-04 10:33:15","status": "Up 1 hour"}]}'
    dictionary = []
    for line in data:
        # Id, Image, Command, CreatedAt, Status, Ports, Names = line.split(';')
        keys = ['Id', 'Image', 'Command', 'CreatedAt', 'Status', 'Ports', 'Names']
        values = line.split(';')
        dictionary.append(dict(zip(keys, values)))
    return dictionary


def dkr_containers_stats(data):
    # outjson='{"containers": [{"id": "583407a61900","state": "running","cpu": "0.15%","mem": "0.25%","mem_use": "25MiB","size": "1.07 GB"}]}'
    headers = replaceSpaces(data.pop(0)).split(' ')
    dictionary = []
    for line in data:
        values = replaceSpaces(line).split(' ')
        dictionary.append(dict(zip(headers, values)))
    return dictionary

def dkr_container(data):
    outjson='{"id": "583407a61900","image": {"id": "583407a61900","name": "library/ann","tag": "v1"},"command": "top","names": "ann","ports": "8080/tcp","created_at": "2024-07-04 10:33:15","status": "Up 1 hour"}'
    return outjson


def dkr_container_stats(data):
    outjson='{"id": "583407a61900","state": "running","cpu": "0.15%","mem": "0.25%","mem_use": "25MiB","size": "1.07 GB"}'
    return outjson