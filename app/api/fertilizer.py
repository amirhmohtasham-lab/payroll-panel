"""Fertilizer (مصرف کود) xlsx upload -> audit -> Drive backup -> DB persistence."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session as DbSession

from app.core.security import current_user_dep
from app.db import get_db
from app.models.upload import UploadType
from app.models.user import User
from app.services import upload_service
from app.services.upload_service import DuplicateFileError, DuplicateMonthError

router = APIRouter(prefix="/api/fertilizer", tags=["fertilizer"])


@router.post("/upload")
async def upload_fertilizer(
    file: UploadFile = File(...),
    month_key: str = Form(...),
    month_label: str = Form(""),
    replace: str = Form("false"),
    crop: str = Form(""),
    season: str = Form(""),
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user_dep),
):
    do_replace = replace.lower() in ("1", "true", "yes")
    try:
        upload = await upload_service.process_fertilizer_upload(
            db,
            file=file,
            month_key=month_key,
            month_label=month_label,
            replace=do_replace,
            crop=crop,
            season=season,
            user=user,
        )
    except DuplicateMonthError as e:
        return JSONResponse(
            status_code=409,
            content={
                "duplicate": True,
                "message": "این ماه قبلاً ثبت شده است",
                "existing": {
                    "month_label": e.existing.month_label,
                    "filename": e.existing.original_filename,
                    "uploaded_at": e.existing.uploaded_at.isoformat(),
                },
            },
        )
    except DuplicateFileError as e:
        return JSONResponse(
            status_code=409,
            content={
                "duplicate": True,
                "message": "این فایل قبلاً برای ماه دیگری ثبت شده",
                "existing": {
                    "month_key": e.existing.month_key,
                    "month_label": e.existing.month_label,
                    "filename": e.existing.original_filename,
                },
            },
        )

    record = upload_service.to_public_dict(upload)
    return {
        "ok": True,
        "error_count": upload.error_count,
        "warn_count": upload.warn_count,
        "row_count": upload.row_count,
        "fertilizer_count": upload.fertilizer_count,
        "issues": [i for group in record["issues_grouped"] for i in group["items"]],
        "highlight_url": record["highlight_url"],
        "drive_id": upload.drive_file_id,
        "drive_error": upload.drive_error,
        "record": record,
    }


@router.get("/download/{month_key}/highlighted")
def download_fertilizer_highlight(
    month_key: str, db: DbSession = Depends(get_db), _: User = Depends(current_user_dep)
):
    from sqlalchemy import select
    from app.models.upload import Upload

    upload = db.execute(
        select(Upload).where(Upload.upload_type == UploadType.FERTILIZER, Upload.month_key == month_key)
    ).scalar_one_or_none()
    if not upload or not upload.highlight_path:
        raise HTTPException(status_code=404)
    path = Path(upload.highlight_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="فایل موجود نیست")
    return FileResponse(
        path,
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
