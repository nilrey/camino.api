from . import (router, Request, Path, Body, HTTPException, logger, endpoints_internal as ep, 
                PostedDataImageRun)
from api.lib.ExportDataset import * 
from fastapi.responses import JSONResponse
from api.services import docker_services 

router_images = router(prefix="/images", tags=["Docker-образы"])

@router_images.get("/", tags=["Docker-образы"], summary="Получение списка Docker-образов на сервере")
async def api_docker_images():
   #  logger.info("Получение списка Docker-образов на сервере")
    try:
        images = docker_services.get_vms_images()
        response = JSONResponse(content={
            "pagination": {"totalItems": len(images)},
            "items": images
        })
        logger.info(f"Результат images: {response}")
        return response
    except Exception as e:
        response = JSONResponse(status_code=500, content={
            "code": 500,
            "message": str(e)
        })
        logger.info(f"Ошибка status_code=500: {response}")
        return 


@router_images.get("/{imageId}", tags=["Docker-образы"], summary="Получение информации о Docker-образе на сервере") 
async def get_docker_image(image_id: str = Path(..., alias="imageId")):
   #  logger.info("Получение информации о Docker-образе на сервере")
    try:
        image = docker_services.find_image_by_id(image_id)
        logger.info(f"Результат поиска: {image}")
        if image:
            logger.info(f"Response на запрос: {image} ")
            return image
        else:
            logger.info(f"Response на запрос: status_code=404 , Ошибка: образ не найден {image_id} ")
            raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        logger.info(f"Response на запрос: status_code=500 , Ошибка: {image_id} Описание: {str(e)} ")
        return {
            "code": 500,
            "message": str(e)
        }

@router_images.post("/{imageId}/run", tags=["Docker-образы"], summary="Создание Dockеr-контейнера из Docker-образа и его запуск")
async def api_docker_image_run(request: Request,
      imrun: PostedDataImageRun,
      image_id: str = Path(..., alias="imageId")
   ):
   logger.info("Создание Dockеr-контейнера из Docker-образа и его запуск")
   post_data = imrun.getAllParams()
   post_data['image_id'] = image_id
   resp = DatasetMarkupsExport({"dataset_id": post_data['dataset_id'], "only_verified_chains": post_data['only_verified_chains'], "only_selected_files": post_data['only_selected_files']}, post_data)
   res = resp.run()
   return res 

