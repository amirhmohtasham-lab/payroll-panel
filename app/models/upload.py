"""Upload + audit issue models — replaces index.json / fertilizer_index.json."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UploadType(str, enum.Enum):
    PAYROLL = "payroll"
    FERTILIZER = "fertilizer"


class Upload(Base):
    __tablename__ = "uploads"
    __table_args__ = (UniqueConstraint("upload_type", "month_key", name="uq_upload_type_month"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    upload_type: Mapped[UploadType] = mapped_column(Enum(UploadType, name="upload_type"), nullable=False)
    month_key: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    month_label: Mapped[str] = mapped_column(String(64), nullable=False)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    highlight_path: Mapped[str | None] = mapped_column(String(500))

    drive_file_id: Mapped[str | None] = mapped_column(String(128))
    drive_error: Mapped[str | None] = mapped_column(String(500))

    error_count: Mapped[int] = mapped_column(Integer, default=0)
    warn_count: Mapped[int] = mapped_column(Integer, default=0)

    # fertilizer-specific
    crop: Mapped[str | None] = mapped_column(String(128))
    season: Mapped[str | None] = mapped_column(String(64))
    row_count: Mapped[int | None] = mapped_column(Integer)
    fertilizer_count: Mapped[int | None] = mapped_column(Integer)

    audit_summary: Mapped[dict | None] = mapped_column(JSON)

    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    issues: Mapped[list["AuditIssue"]] = relationship(
        back_populates="upload", cascade="all, delete-orphan"
    )


class AuditIssue(Base):
    __tablename__ = "audit_issues"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    upload_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("uploads.id", ondelete="CASCADE"))
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    sheet: Mapped[str | None] = mapped_column(String(128))
    message: Mapped[str] = mapped_column(String(1000), nullable=False)

    upload: Mapped["Upload"] = relationship(back_populates="issues")
