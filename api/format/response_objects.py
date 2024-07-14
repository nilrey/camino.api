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
    resp = {
        'pagination':getPagination(len(data['images'])),
        'items':[]
    }
    for line in data['images'].splitlines():
        resp['items'].append(json.loads(line )  )
    return resp
