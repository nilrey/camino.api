import json

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
    resp = {}
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
        items.append( {
            'id':container['ID'],
            'img':container['Image'],
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
    lst_items = json.loads(data['container'])
    items = []
    for item in lst_items:
        image_info = {}
        lst_images = json.loads(data['images'])
        for image in lst_images:
            # в данном месте image["Repository"] имеет вид "postgres" а container['Image'] = "postgres:16.1" , т.е. к названию добавлено значения Tag
            # соответствено добавлена обработка, в выборку добавлено оригинальное значение Image для отладки
            if(item['Image'].replace(':'+image['Tag'], '') == image["Repository"] ):
                image_info = {
                    "id":removeSha256(image["ID"]),
                    "name":image["Repository"],
                    "tag":image["Tag"]
                }
                break
        items.append(
            {
                "id": item['ID'],
                'img':item['Image'],
                "image": image_info,
                "command": item['Command'],
                "names": item['Names'],
                "ports": item['Ports'],
                "created_at": item['CreatedAt'],
                "status": item['Status'],
            }
        )
    return {'pagination':getPagination(len(items)), 'items':items }


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