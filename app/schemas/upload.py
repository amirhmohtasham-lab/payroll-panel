from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.upload import UploadType


class IssueOut(BaseModel):
    severity: str
    code: str
    sheet: str | None
    message: str

    model_config = {"from_attributes": True}


class IssueGroup(BaseModel):
    code: str
    count: int
    items: list[IssueOut]


class UploadOut(BaseModel):
    id: uuid.UUID
    upload_type: UploadType
    month_key: str
    month_label: str
    original_filename: str
    sha256: str
    uploaded_at: datetime
    error_count: int
    warn_count: int
    highlight_url: str | None = None
    drive_file_id: str | None = None
    drive_error: str | None = None
    crop: str | None = None
    season: str | None = None
    row_count: int | None = None
    fertilizer_count: int | None = None
    audit_summary: dict[str, Any] | None = None
    issues_grouped: list[IssueGroup] = []

    model_config = {"from_attributes": True}


class UploadResultResponse(BaseModel):
    ok: bool = True
    error_count: int
    warn_count: int
    record: UploadOut


class DuplicateUploadInfo(BaseModel):
    duplicate: bool = True
    message: str
    existing: dict[str, Any]


class MonthListItem(BaseModel):
    month_key: str
    month_label: str
    filename: str
    uploaded_at: datetime
    error_count: int
    warn_count: int
    status_label: str
    status_text: str
    worker_rows: int | None = None
    row_count: int | None = None
    fertilizer_count: int | None = None


class MonthListSummary(BaseModel):
    month_count: int
    total_errors: int
    total_warns: int
    total_workers: int | None = None
    total_rows: int | None = None


class MonthListResponse(BaseModel):
    items: list[MonthListItem]
    summary: MonthListSummary


class ArchiveItem(BaseModel):
    month_key: str
    type: str
    module_label: str
    label: str
    filename: str
    uploaded_at: datetime
    error_count: int
    warn_count: int


class ArchiveSummary(BaseModel):
    workforce_count: int
    fertilizer_count: int
    total: int


class ArchiveResponse(BaseModel):
    items: list[ArchiveItem]
    summary: ArchiveSummary
