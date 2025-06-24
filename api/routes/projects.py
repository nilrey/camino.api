from . import (router, Path, Body, logger, 
               PostedDataDatasetImport, PostedDataDatasetExport,
               ImportAnnJsonToDB, DatasetMarkupsExport)


router_projects = router(prefix="/projects", tags=["Проекты"])


@router_projects.post("/projects/{projectId}/datasets/{datasetId}/import", summary="Загрузка датасета из JSON файлов")
async def api_import_json_to_db(
      project_id:str = Path(..., alias="projectId"),
      dataset_id:str = Path(..., alias="datasetId"),
      import_data:PostedDataDatasetImport = Body(...),
   ):
   logger.info(f"Requested url: /{project_id}/datasets/{dataset_id}/import")
   resp = ImportAnnJsonToDB(project_id, dataset_id, import_data.files)
   res = resp.run()
   logger.info(f"Результат import: {res}")
   return res


@router_projects.post("/projects/{projectId}/datasets/{datasetId}/export", summary="Запускает процесс формирования JSON файлов разметки датасета и возвращает признак успешного начала операции. По окончании операции вызывается соотв. роут export on_save")
async def api_export_db_to_json(
      project_id:str = Path(..., alias="projectId"),
      dataset_id:str = Path(..., alias="datasetId"),
      exparams:PostedDataDatasetExport = Body(...),
   ):
   post_data = exparams.getAllParams()
   post_data['project_id'] = project_id
   post_data['dataset_id'] = dataset_id
   resp = DatasetMarkupsExport(post_data , {})
   res = resp.run()
   return res
