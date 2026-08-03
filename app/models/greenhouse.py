"""Greenhouse climate analysis runs — one record per uploaded analysis."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GreenhouseRun(Base):
    __tablename__ = "greenhouse_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    temp_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    humi_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # stored file paths (original uploads + outputs)
    temp_path: Mapped[str] = mapped_column(String(500), nullable=False)
    humi_path: Mapped[str] = mapped_column(String(500), nullable=False)
    output_dir: Mapped[str] = mapped_column(String(500), nullable=False)
    zip_path: Mapped[str | None] = mapped_column(String(500))

    row_count: Mapped[int | None] = mapped_column(Integer)
    metrics: Mapped[dict | None] = mapped_column(JSON)
    tables: Mapped[dict | None] = mapped_column(JSON)

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
