"""Transcode วิดีโอเป็น HLS ด้วย ffmpeg — รันบน ARQ worker (งานหนัก CPU แยกจาก web)"""

import asyncio
import logging

from addons.storage import services as storage_services
from addons.storage.models import StoredFile
from core.db import get_sessionmaker
from core.jobs import background_job
from core.runtime import ctx

from vdo_addons.vdo import services
from vdo_addons.vdo.config import get_vdo_settings
from vdo_addons.vdo.models import Video

logger = logging.getLogger(__name__)


@background_job
async def transcode_video(job_ctx: dict, video_id: int) -> str:
    settings = get_vdo_settings()

    async with get_sessionmaker()() as db:
        video = await db.get(Video, video_id)
        if video is None:
            return "video not found"
        stored = await db.get(StoredFile, video.stored_file_id)
        source = storage_services.file_path(stored)
        await services.set_status(db, video_id, "processing")

    out_dir = services.hls_dir() / str(video_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    playlist = out_dir / "index.m3u8"

    cmd = [
        settings.ffmpeg_bin,
        "-y", "-i", str(source),
        "-c:v", "libx264", "-preset", "veryfast",
        "-c:a", "aac",
        "-hls_time", str(settings.segment_seconds),
        "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(out_dir / "seg_%04d.ts"),
        str(playlist),
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        ok = proc.returncode == 0
        err = "" if ok else (stderr or b"")[-800:].decode(errors="replace")
    except FileNotFoundError:
        ok, err = False, f"ไม่พบ {settings.ffmpeg_bin} — ติดตั้ง ffmpeg ใน image ก่อน"

    async with get_sessionmaker()() as db:
        if ok:
            await services.set_status(db, video_id, "ready", hls_path=f"{video_id}/index.m3u8")
            await ctx.events.emit("vdo.ready", {"video_id": video_id}, broadcast=True)
        else:
            logger.error("transcode %s failed: %s", video_id, err)
            await services.set_status(db, video_id, "error", error=err)
    return "ready" if ok else "error"
