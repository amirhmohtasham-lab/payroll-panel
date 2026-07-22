"""Local filesystem storage for uploaded workbooks — config-driven paths, no hardcoded dirs."""
from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path

from app.config import get_settings

_SAFE_NAME_RE = re.compile(r"[^\w\u0600-\u06FF. ()-]+")


def sanitize_filename(filename: str) -> str:
    return _SAFE_NAME_RE.sub("_", filename)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def upload_subdir(kind: str) -> Path:
    """kind: 'payroll' | 'fertilizer'."""
    settings = get_settings()
    path = settings.upload_dir / kind
    path.mkdir(parents=True, exist_ok=True)
    return path


def store_uploaded_file(content: bytes, *, kind: str, month_key: str, original_filename: str) -> Path:
    safe_name = sanitize_filename(original_filename)
    local_name = f"{month_key}_{uuid.uuid4().hex[:8]}_{safe_name}"
    dest = upload_subdir(kind) / local_name
    dest.write_bytes(content)
    return dest


def highlighted_path(*, kind: str, month_key: str) -> Path:
    return upload_subdir(kind) / f"{month_key}_highlighted.xlsx"


def delete_if_exists(path: str | Path | None) -> None:
    if not path:
        return
    p = Path(path)
    try:
        p.unlink(missing_ok=True)
    except OSError:
        pass
