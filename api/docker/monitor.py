import os
import copy
import subprocess

class Monitor():
    # Создается экземпляр класса Monitor 
    # Вызывается метод create_json с параметром, переданным через API
    # Возвращается dict

    def __init__(self, file_path = os.path.dirname(os.path.realpath(__file__))):
        self.file_path = file_path
        self.template = {"id": "",
                        "title": "",
                        "source": "",
                        "content": "",
	                    "noResize": True,
                        "x": 0, 
	                    "y": 0, 
	                    "w": 3, 
	                    "h": 2
                        }
        self.containers_names = ['grafana', 
                                'node-exporter',
                                'cadvisor',
                                'prometheus',
                                'camino-back',
                                'camino-front',
                                'camino-pgadmin',
                                'camino-restapi',
                                'camino-plugins',
                                'camino-pgdb']
            
    def get_containers_from_docker(self)->dict:
        '''Получение списка активных контейнеров от docker
        Return: словарь вида full_id:name
        '''
        result = subprocess.check_output('docker ps --format "{{.ID}}: {{.Names}}" --no-trunc', shell=True).decode("utf-8").split('\n')
        containers = {}
        for line in result:
            if ': ' in line:
                key, value = line.split(': ')
                containers[key] = value
        return containers

    def create_json_part(self, id, name = None):
        if name is None:
            name = id
        template = copy.deepcopy(self.template)
        template['id'] = id
        template['title'] = name
        template['source'] = 'http://127.0.0.1:3000/d/b5f1b21e-35e1-4dc7-be5e-361d1bcb1bcf/docker-monitoring?orgId=1&var-id=%2Fsystem.slice%2Fdocker-{}.scope&from=now-5m&to=now'.format(id)
        return template
        
    def create_json(self, id)->dict:
        ''' Метод для создания файлов отображения мониторинга
            Return: создается словарь со структурой template. Имя файла - id контейнера
        '''
        result = []
        if id != 'GRAFANA':
            result.append(self.create_json_part(id))
        else:
            containers = self.get_containers_from_docker()
            for id, name in containers.items():
                if name in self.containers_names:
                    result.append(self.create_json_part(id,name))
        return {'items':result}

if __name__ == "__main__":
    monitor = Monitor()
    res = monitor.create_json('GRAFANA')
    print(res)

