"""Greenhouse analysis schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class GreenhouseRunOut(BaseModel):
    id: uuid.UUID
    temp_filename: str
    humi_filename: str
    row_count: int | None = None
    metrics: dict[str, Any] | None = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class GreenhouseRunDetail(GreenhouseRunOut):
    tables: dict[str, Any] | None = None


class GreenhouseRunListResponse(BaseModel):
    items: list[GreenhouseRunOut]
    total: int
