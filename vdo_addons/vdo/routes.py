import logging
import os
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from core.db import get_session
from core.jobs import enqueue

from vdo_addons.vdo import services

logger = logging.getLogger(__name__)

router = APIRouter(tags=["vdo"])
api = APIRouter(prefix="/api/vdo")


class VideoOut(BaseModel):
    id: int
    title: str
    status: str
    hls_path: str | None
    error: str
    created_at: datetime

    model_config = {"from_attributes": True}


@api.post("/videos", response_model=VideoOut, status_code=201)
async def upload_video(
    file: UploadFile,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user)],
    title: Annotated[str, Form()] = "",
):
    video = await services.create_video(session, file, title, user.id)
    try:
        await enqueue("transcode_video", video.id)
        await services.set_status(session, video.id, "processing")
        video.status = "processing"
    except Exception as e:  # redis/worker ยังไม่ขึ้น — ค้างสถานะ uploaded ไว้ก่อน
        logger.warning("enqueue transcode ไม่ได้ (%s) — video %s ค้างที่ uploaded", e, video.id)
    return video


@api.get("/videos", response_model=list[VideoOut])
async def list_videos(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user)],
):
    return await services.list_owned(session, user.id)


@api.get("/videos/{video_id}", response_model=VideoOut)
async def get_video(
    video_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user)],
):
    return await services.get_for_user(session, video_id, user)


@router.get("/hls/{video_id}/{filename}")
async def hls_file(video_id: int, filename: str):
    """เสิร์ฟ playlist/segment (dev เท่านั้น — production ให้ Caddy/nginx เสิร์ฟโฟลเดอร์ hls ตรงๆ)"""
    safe = os.path.basename(filename)
    path = (services.hls_dir() / str(video_id) / safe).resolve()
    if not path.is_relative_to(services.hls_dir().resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="not found")
    media = "application/vnd.apple.mpegurl" if safe.endswith(".m3u8") else "video/mp2t"
    return FileResponse(path, media_type=media)


router.include_router(api)
