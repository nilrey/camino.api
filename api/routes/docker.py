from fastapi import APIRouter

router_docker = APIRouter(prefix="/docker", tags=["Docker"])


@router_docker.get("/", tags=["Docker"], summary="Получение информации о состоянии Docker")
async def api_docker_info():
   return True