from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from addons.storage import services as storage_services

from vdo_addons.vdo.config import get_vdo_settings
from vdo_addons.vdo.models import Video


def hls_dir() -> Path:
    path = Path(get_vdo_settings().hls_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def create_video(
    session: AsyncSession, upload: UploadFile, title: str, owner_id: int
) -> Video:
    stored = await storage_services.save_upload(session, upload, owner_id)
    video = Video(title=title or stored.original_name, stored_file_id=stored.id, owner_id=owner_id)
    session.add(video)
    await session.commit()
    await session.refresh(video)
    return video


async def get_for_user(session: AsyncSession, video_id: int, user) -> Video:
    video = await session.get(Video, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="video not found")
    if video.owner_id != user.id and not user.is_superuser:
        raise HTTPException(status_code=403, detail="not your video")
    return video


async def list_owned(session: AsyncSession, owner_id: int) -> list[Video]:
    result = await session.execute(
        select(Video).where(Video.owner_id == owner_id).order_by(Video.id.desc())
    )
    return list(result.scalars())


async def set_status(
    session: AsyncSession, video_id: int, status: str, hls_path: str | None = None, error: str = ""
) -> None:
    video = await session.get(Video, video_id)
    if video is None:
        return
    video.status = status
    video.error = error
    if hls_path is not None:
        video.hls_path = hls_path
    await session.commit()
