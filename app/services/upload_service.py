"""Upload + audit orchestration: validate xlsx, hash, audit, highlight, Drive backup, persist to DB.

Replaces the JSON-file-based index.json / fertilizer_index.json flow in the legacy app.
"""
from __future__ import annotations
from app.services.fertilizer_hook import post_process_fertilizer_upload

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.upload import AuditIssue, Upload, UploadType
from app.models.user import User
from app.services import audit_service, drive_service, storage_service

MONTH_KEY_RE = re.compile(r"^\d{4}-\d{2}$")


class DuplicateMonthError(Exception):
    def __init__(self, existing: Upload):
        self.existing = existing


class DuplicateFileError(Exception):
    def __init__(self, existing: Upload):
        self.existing = existing


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_month_key(month_key: str) -> str:
    month_key = month_key.strip()
    if not MONTH_KEY_RE.match(month_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="فرمت ماه نامعتبر (مثلاً 1405-03)"
        )
    return month_key


def validate_xlsx(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="فقط فایل .xlsx مجاز است")


def _existing_for_month(db: DbSession, upload_type: UploadType, month_key: str) -> Upload | None:
    return db.execute(
        select(Upload).where(Upload.upload_type == upload_type, Upload.month_key == month_key)
    ).scalar_one_or_none()


def _existing_by_hash(
    db: DbSession, upload_type: UploadType, digest: str, exclude_month_key: str
) -> Upload | None:
    return db.execute(
        select(Upload).where(
            Upload.upload_type == upload_type,
            Upload.sha256 == digest,
            Upload.month_key != exclude_month_key,
        )
    ).scalar_one_or_none()


def _backup_to_drive(local_path: Path, *, label: str, existing: Upload | None) -> tuple[str | None, str | None]:
    drive_id: str | None = None
    drive_error: str | None = None
    try:
        folder = drive_service.ensure_folder()
        if existing and existing.drive_file_id:
            try:
                drive_service.delete_file(existing.drive_file_id, permanent=True)
            except Exception:
                pass
        uploaded = drive_service.upload_file(local_path, parent=folder, name=label)
        drive_id = uploaded.get("id")
    except drive_service.DriveNotConfiguredError as e:
        drive_error = str(e)
    except Exception as e:  # noqa: BLE001 - Drive backup failures shouldn't block the upload
        drive_error = str(e)
    return drive_id, drive_error


async def process_payroll_upload(
    db: DbSession,
    *,
    file: UploadFile,
    month_key: str,
    month_label: str,
    replace: bool,
    user: User,
) -> Upload:
    validate_xlsx(file)
    month_key = validate_month_key(month_key)

    existing = _existing_for_month(db, UploadType.PAYROLL, month_key)
    if existing and not replace:
        raise DuplicateMonthError(existing)

    content = await file.read()
    local_path = storage_service.store_uploaded_file(
        content, kind="payroll", month_key=month_key, original_filename=file.filename
    )
    digest = storage_service.file_sha256(local_path)

    other = _existing_by_hash(db, UploadType.PAYROLL, digest, month_key)
    if other and not replace:
        storage_service.delete_if_exists(local_path)
        raise DuplicateFileError(other)

    highlight_path = storage_service.highlighted_path(kind="payroll", month_key=month_key)
    try:
        result = audit_service.audit_payroll(local_path)
        audit_service.write_payroll_highlight(result, local_path, highlight_path)
    except Exception as e:
        storage_service.delete_if_exists(local_path)
        raise HTTPException(status_code=500, detail=f"خطا در حسابرسی: {e}") from e

    safe_name = storage_service.sanitize_filename(file.filename)
    drive_id, drive_error = _backup_to_drive(
        local_path, label=f"{month_label or month_key} - {safe_name}", existing=existing
    )

    if existing:
        storage_service.delete_if_exists(existing.stored_path)
        if existing.highlight_path and existing.highlight_path != str(highlight_path):
            storage_service.delete_if_exists(existing.highlight_path)

    issues = result.issues
    error_count = len([i for i in issues if i.severity == "error"])
    warn_count = len([i for i in issues if i.severity == "warn"])

    if existing:
        upload = existing
        db.execute(select(AuditIssue).where(AuditIssue.upload_id == upload.id))
        for old_issue in list(upload.issues):
            db.delete(old_issue)
    else:
        upload = Upload(upload_type=UploadType.PAYROLL, month_key=month_key)
        db.add(upload)

    upload.month_label = month_label.strip() or month_key
    upload.original_filename = safe_name
    upload.sha256 = digest
    upload.stored_path = str(local_path)
    upload.highlight_path = str(highlight_path)
    upload.drive_file_id = drive_id
    upload.drive_error = drive_error
    upload.error_count = error_count
    upload.warn_count = warn_count
    upload.audit_summary = audit_service.payroll_summary(result)
    upload.uploaded_by = user.id
    upload.uploaded_at = _utcnow()
    upload.issues = [
        AuditIssue(severity=i.severity, code=i.code, sheet=i.sheet, message=i.message) for i in issues
    ]


    db.commit()
    db.refresh(upload)
    return upload


async def process_fertilizer_upload(
    db: DbSession,
    *,
    file: UploadFile,
    month_key: str,
    month_label: str,
    replace: bool,
    crop: str,
    season: str,
    user: User,
) -> Upload:
    validate_xlsx(file)
    month_key = validate_month_key(month_key)

    existing = _existing_for_month(db, UploadType.FERTILIZER, month_key)
    if existing and not replace:
        raise DuplicateMonthError(existing)

    content = await file.read()
    local_path = storage_service.store_uploaded_file(
        content, kind="fertilizer", month_key=month_key, original_filename=file.filename
    )
    digest = storage_service.file_sha256(local_path)

    other = _existing_by_hash(db, UploadType.FERTILIZER, digest, month_key)
    if other and not replace:
        storage_service.delete_if_exists(local_path)
        raise DuplicateFileError(other)

    highlight_path = storage_service.highlighted_path(kind="fertilizer", month_key=month_key)
    try:
        result = audit_service.audit_fertilizer(local_path)
        audit_service.write_fertilizer_highlight(result, local_path, highlight_path)
    except Exception as e:
        storage_service.delete_if_exists(local_path)
        raise HTTPException(status_code=500, detail=f"خطا در حسابرسی: {e}") from e

    safe_name = storage_service.sanitize_filename(file.filename)
    drive_id, drive_error = _backup_to_drive(
        local_path, label=f"{month_label or month_key} - کود - {safe_name}", existing=existing
    )

    if existing:
        storage_service.delete_if_exists(existing.stored_path)
        if existing.highlight_path and existing.highlight_path != str(highlight_path):
            storage_service.delete_if_exists(existing.highlight_path)

    issues = result.issues
    error_count = len([i for i in issues if i.severity == "error"])
    warn_count = len([i for i in issues if i.severity == "warn"])

    if existing:
        upload = existing
        for old_issue in list(upload.issues):
            db.delete(old_issue)
    else:
        upload = Upload(upload_type=UploadType.FERTILIZER, month_key=month_key)
        db.add(upload)

    upload.month_label = month_label.strip() or month_key
    upload.original_filename = safe_name
    upload.sha256 = digest
    upload.stored_path = str(local_path)
    upload.highlight_path = str(highlight_path)
    upload.drive_file_id = drive_id
    upload.drive_error = drive_error
    upload.error_count = error_count
    upload.warn_count = warn_count
    upload.crop = crop.strip() or None
    upload.season = season.strip() or None
    upload.row_count = len(result.rows)
    upload.fertilizer_count = len(result.fertilizers)
    upload.uploaded_by = user.id
    upload.uploaded_at = _utcnow()
    upload.issues = [
        AuditIssue(severity=i.severity, code=i.code, sheet=i.sheet, message=i.message) for i in issues
    ]

    # ── Run unpivot to create Cleaned Data sheet ──
    unpivot_result = post_process_fertilizer_upload(db, upload)
    if unpivot_result.get("unpivot_success"):
        upload.fertilizer_count = unpivot_result["row_count"]
    elif unpivot_result.get("error") and "Missing sheets" not in unpivot_result.get("error", ""):
        logger.warning("unpivot warning: %s", unpivot_result["error"])

    db.commit()
    db.refresh(upload)
    return upload


def status_label_and_text(error_count: int, warn_count: int) -> tuple[str, str]:
    if error_count > 0:
        return "error", f"{error_count} خطا"
    if warn_count > 0:
        return "warn", f"{warn_count} هشدار"
    return "ok", "تأیید"


def issues_grouped(issues: list[AuditIssue]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for i in issues:
        grouped.setdefault(i.code, {"code": i.code, "count": 0, "items": []})
        grouped[i.code]["count"] += 1
        grouped[i.code]["items"].append(
            {"severity": i.severity, "code": i.code, "sheet": i.sheet, "message": i.message}
        )
    return list(grouped.values())


def to_public_dict(upload: Upload) -> dict[str, Any]:
    highlight_url = None
    if upload.highlight_path:
        kind = "fertilizer" if upload.upload_type == UploadType.FERTILIZER else ""
        prefix = "/api/fertilizer/download" if kind else "/api/download"
        highlight_url = f"{prefix}/{upload.month_key}/highlighted"
    return {
        "id": upload.id,
        "upload_type": upload.upload_type,
        "month_key": upload.month_key,
        "month_label": upload.month_label,
        "original_filename": upload.original_filename,
        "sha256": upload.sha256,
        "uploaded_at": upload.uploaded_at,
        "error_count": upload.error_count,
        "warn_count": upload.warn_count,
        "highlight_url": highlight_url,
        "drive_file_id": upload.drive_file_id,
        "drive_error": upload.drive_error,
        "crop": upload.crop,
        "season": upload.season,
        "row_count": upload.row_count,
        "fertilizer_count": upload.fertilizer_count,
        "audit_summary": upload.audit_summary,
        "issues_grouped": issues_grouped(upload.issues),
    }
