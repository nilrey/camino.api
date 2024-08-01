import json
import api.sets.const as C
from fastapi import HTTPException
from api.format.exceptions import http_exception_handler, NotFoundError

def getPagination(cnt = 0):
    return { "page": 1, "pageSize": cnt, "totalItems": cnt, "totalPages": 1}


def docker_info(data_json):
    lst_items = json.loads(data_json)
    resp = {
        "version": lst_items[0]["ServerVersion"],
        "containers": {
            "running": lst_items[0]["ContainersRunning"],
            "paused":  lst_items[0]["ContainersPaused"],
            "stopped":  lst_items[0]["ContainersStopped"],
            "total": lst_items[0]["Containers"]
        },
        "images": lst_items[0]["Images"],
        "cpus": lst_items[0]["NCPU"],
        "mem": lst_items[0]["MemTotal"]
    }
    return resp


def docker_images(data_json):    
    lst_items = json.loads(data_json)
    items = []
    for item in lst_items:
        if(isWhiteList(item["Repository"])):
            items.append(
                {
                "id":removeSha256(item["ID"]),
                "name":item["Repository"],
                "tag":item["Tag"],
                "created_at":item["CreatedAt"],
                "size":item["Size"],
                "location":"",
                "comment":"",
                "archive":""
            })
    return {'pagination':getPagination(len(items)), 'items':items }


def docker_image(imageId, data_json):
    lst_items = json.loads(data_json)
    for item in lst_items:
        if(removeSha256(item["ID"]) == imageId ):
            resp = {
                "id":removeSha256(item["ID"]),
                "name":item["Repository"],
                "tag":item["Tag"],
                "created_at":item["CreatedAt"],
                "size":item["Size"],
                "location":"",
                "comment":"",
                "archive":""
            }
    if not "resp" in locals():
        raise NotFoundError(detail="Bad Request")
    return resp


def dkr_containers(data):
    lst_container = json.loads(data['containers'])
    items = []
    for container in lst_container:
        img_info = {}
        lst_images = json.loads(data['images'])
        for image in lst_images:
            # в данном месте image["Repository"] имеет вид "postgres" а container['Image'] = "postgres:16.1" , т.е. к названию добавлено значения Tag
            # соответствено добавлена обработка, в выборку добавлено оригинальное значение Image для отладки
            if(container['Image'].replace(':'+image['Tag'], '') == image["Repository"] ):
                img_info = {
                    "id":removeSha256(image["ID"]),
                    "name":image["Repository"],
                    "tag":image["Tag"]
                }
        if( isWhiteList(img_info["name"])):
            items.append( {
                'id':container['ID'],
                # 'img':container['Image'],
                'image' : img_info,
                'command' : container['Command'],
                'names' : container['Names'],
                'ports' : container['Ports'],
                'created_at' : container['CreatedAt'],
                'status' : container['Status']
                } )

    return {'pagination':getPagination(len(items)), 'items':items }


def containers_stats(data_json):
    lst_items = json.loads(data_json)
    items = []
    for item in lst_items:
        items.append(
            {
                "id": item['ID'],
                "state": "",
                "cpu": item['CPUPerc'],
                "mem": item['MemPerc'],
                "mem_use": item['MemUsage'],
                "size": ""
            }
        )
    return {'items':items }


def container(data)->dict:

    try:
        tmp = json.loads(data['container'])
        if len(tmp) > 0:
          item = tmp[0]
        else: 
          return {'error':True, 'error_descr': 'Контейнер не найден'}
        
    except ValueError as e:
        return {'error':True, 'error_descr': 'Контейнер не найден'}
    
    
    image_info = findImageByName( json.loads(data['images']), item['Image'] )
    resp = {
            "id": item['ID'],
            # 'img':item['Image'],
            "image": image_info,
            "command": item['Command'],
            "names": item['Names'],
            "ports": item['Ports'],
            "created_at": item['CreatedAt'],
            "status": item['Status'],
        }
    return resp


def container_stats(containerId, data_json):
    lst_items = json.loads(data_json)
    resp = {}
    for item in lst_items:
        if(removeSha256(item["ID"]) == containerId ):
            resp = {
                "id": item['ID'],
                "state": "",
                "cpu": item['CPUPerc'],
                "mem": item['MemPerc'],
                "mem_use": item['MemUsage'],
                "size": ""
            }
    return resp


def removeSha256(str):
    return str.replace('sha256:','')


def findImageByName(lst_images, imageName):
    image_info = {}
    for image in lst_images:
        # в данном месте image["Repository"] имеет вид "postgres" а imageName = "postgres:16.1" , т.е. к названию добавлено значения Tag
        # соответствено добавлена обработка, также в выборку добавлено оригинальное значение Image для отладки
        if(imageName.replace(':'+image['Tag'], '') == image["Repository"] 
           #or imageName == image["ID"]
           ):
            image_info = {
                "id":removeSha256(image["ID"]),
                "name":image["Repository"],
                "tag":image["Tag"]
            }
            break
    return image_info


def getImageById(image_id, images):
    lst_images = json.loads(images)
    image_info = []
    for image in lst_images:
        if( removeSha256(image_id) == removeSha256(image["ID"]) ):
            image_info = {
                    "id": removeSha256(image["ID"]),
                    "name":image["Repository"],
                    "tag":image["Tag"]
                }
    return image_info


def isWhiteList(image_name):
    for wl_name in C.WHITE_LIST :
        if image_name.startswith(wl_name):
            return True
    return False