from fastapi import APIRouter
from  api.services import docker_services 

router_vm = APIRouter(prefix="/vm", tags=["Вирутальные машины"])

@router_vm.get("/check")
async def get_vm_without_ann():
    result, is_error = docker_services.get_available_vm() 
    if is_error:
        message = f'Ошибка при просмотре VM: {result}'
    elif result: 
        message = f'Свободная VM: {result}'
    else:
        message = 'Нет свободных VM.'            

    return {"message": message}    
