from . import ( router, Path, Body, logger, endpoints_internal as ep,
               PostedDataAnnExport, 
               ANNExporter )

router_ann = router(prefix="/ann", tags=["ИНС"])

@router_ann.post("/{annId}/archive/save", tags=["ИНС"], summary="Выгрузка ИНС (Docker-образа и файла весов) в архив")
async def api_docker_ann_export(
      ann_id:str = Path(..., alias="annId"),
      export: PostedDataAnnExport = Body(...) ):
   
   logger.info("Выгрузка ИНС (Docker-образа и файла весов) в архив")
   exporter = ANNExporter(ann_id=ann_id, export_data=export)
   exporter.run()

   return {"status":"running"}