from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base

# status: uploaded -> processing -> ready | error
STATUSES = ("uploaded", "processing", "ready", "error")


class Video(Base):
    __tablename__ = "vdo_videos"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="uploaded", index=True)
    stored_file_id: Mapped[int] = mapped_column(
        ForeignKey("stored_files.id", ondelete="CASCADE")
    )
    hls_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
