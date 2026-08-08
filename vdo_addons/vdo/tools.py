"""AI tools ของโมดูล vdo — ใช้ได้ทั้ง agent ภายใน, LINE และ MCP client ภายนอก"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.ai import agent_tool

from vdo_addons.vdo.models import Video


@agent_tool(module="vdo", permission=None)
async def search_videos(session: AsyncSession, query: str) -> str:
    """ค้นหาวิดีโอที่พร้อมดู (ready) จากชื่อเรื่อง"""
    result = await session.execute(
        select(Video)
        .where(Video.status == "ready", Video.title.ilike(f"%{query}%"))
        .order_by(Video.id.desc())
        .limit(10)
    )
    videos = list(result.scalars())
    if not videos:
        return "ไม่พบวิดีโอที่ตรงกับคำค้น"
    return "\n".join(f"- [{v.id}] {v.title} (hls: {v.hls_path})" for v in videos)


@agent_tool(module="vdo", permission="vdo.manage")
async def video_pipeline_status(session: AsyncSession) -> str:
    """สรุปสถานะ pipeline วิดีโอ: กี่ตัวรอ transcode / กำลังทำ / พร้อมดู / พัง"""
    result = await session.execute(select(Video.status))
    counts: dict[str, int] = {}
    for (status,) in result:
        counts[status] = counts.get(status, 0) + 1
    if not counts:
        return "ยังไม่มีวิดีโอในระบบ"
    label = {"uploaded": "รอ transcode", "processing": "กำลังทำ", "ready": "พร้อมดู", "error": "พัง"}
    return ", ".join(f"{label.get(s, s)} {n}" for s, n in sorted(counts.items()))
