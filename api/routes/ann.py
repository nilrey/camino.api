from . import ( router, Path, Body, logger, endpoints_internal as ep,
               PostedDataAnnExport, 
               ANNExporter )

router_ann = router(prefix="/ann", tags=["ИНС"])

@router_ann.post("/ann/{annId}/archive/save", tags=ep["ann_save"]["tags"], summary=ep["ann_save"]["summary"])
async def api_docker_ann_export(
      ann_id:str = Path(..., alias="annId"),
      export: PostedDataAnnExport = Body(...) ):
   
   logger.info(ep["ann_save"]["summary"])
   exporter = ANNExporter(ann_id=ann_id, export_data=export)
   exporter.run()

   return {"status":"running"}