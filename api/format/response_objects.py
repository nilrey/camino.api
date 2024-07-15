import json

def getPagination(cnt = 0):
    return { "page": 1, "pageSize": cnt, "totalItems": cnt, "totalPages": 1}

def docker_info(data):
    resp = {
        "version": data["ServerVersion"],
        "containers": {
            "running": data["ContainersRunning"],
            "paused":  data["ContainersPaused"],
            "stopped":  data["ContainersStopped"],
            "total": data["Containers"]
        },
        "images": data["Images"],
        "cpus": data["NCPU"],
        "mem": data["MemTotal"]
    }
    return resp


def docker_images(data):    
    resp = {'pagination':{}, 'items':[] }
    for line in data['images'].splitlines():
        lst = json.loads(line)
        formatted = {
            "id":lst["ID"].replace('sha256:',''),
            "name":lst["Repository"],
            "tag":lst["Tag"],
            "created_at":lst["CreatedAt"],
            "size":lst["Size"],
            "location":"",
            "comment":"",
            "archive":""
        }
        resp['items'].append(formatted )
    resp['pagination'] = getPagination(len(resp['items']))
    return resp

def docker_image(data):    
    resp = {
        "id":data["ID"].replace('sha256:',''),
        "name":data["Repository"],
        "tag":data["Tag"],
        "created_at":data["CreatedAt"],
        "size":data["Size"],
        "location":"",
        "comment":"",
        "archive":""
    }
    return resp
