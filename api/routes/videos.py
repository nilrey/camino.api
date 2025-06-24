from fastapi import APIRouter, HTTPException
from api.lib.posted_data_classes import PostedDataVideoConverter
from api.lib.VideoConverter import VideoConverter
from pathlib import Path as PathLib

router_video = APIRouter(prefix="/video", tags=["Видео"])


@router_video.post("/converter")
async def api_video_convert(req: PostedDataVideoConverter):
    source_dir = PathLib(req.source_dir)
    target_dir = PathLib(req.target_dir)
    if not source_dir.exists() or not source_dir.is_dir():
        raise HTTPException(status_code=400, detail="Указанная директория не существует или не является директорией")

    converter = VideoConverter(source_dir, target_dir)
    message = converter.run()
    return {"message": message}
