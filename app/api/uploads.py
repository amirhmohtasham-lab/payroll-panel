"""Payroll xlsx upload -> audit -> Drive backup -> DB persistence."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from sqlalchemy.orm import Session as DbSession

from app.core.security import current_user_dep
from app.db import get_db
from app.models.upload import UploadType
from app.models.user import User
from app.services import upload_service
from app.services.upload_service import DuplicateFileError, DuplicateMonthError

router = APIRouter(tags=["uploads"])


@router.post("/api/upload")
async def upload_payroll(
    file: UploadFile = File(...),
    month_key: str = Form(...),
    month_label: str = Form(""),
    replace: str = Form("false"),
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user_dep),
):
    do_replace = replace.lower() in ("1", "true", "yes")
    try:
        upload = await upload_service.process_payroll_upload(
            db,
            file=file,
            month_key=month_key,
            month_label=month_label,
            replace=do_replace,
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

    return {
        "ok": True,
        "error_count": upload.error_count,
        "warn_count": upload.warn_count,
        "record": upload_service.to_public_dict(upload),
    }


@router.get("/api/download/{month_key}/highlighted")
def download_payroll_highlight(
    month_key: str, db: DbSession = Depends(get_db), _: User = Depends(current_user_dep)
):
    from sqlalchemy import select
    from app.models.upload import Upload

    upload = db.execute(
        select(Upload).where(Upload.upload_type == UploadType.PAYROLL, Upload.month_key == month_key)
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


@router.delete("/api/upload/{month_key}")
def delete_payroll_upload(
    month_key: str,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user_dep),
):
    from app.models.upload import Upload, UploadType
    from sqlalchemy import select

    upload = db.execute(
        select(Upload).where(Upload.upload_type == UploadType.PAYROLL, Upload.month_key == month_key)
    ).scalar_one_or_none()
    if not upload:
        raise HTTPException(status_code=404, detail="فایل یافت نشد")

    upload_service.delete_upload(db, upload, user)
    return {"ok": True, "message": "فایل با موفقیت حذف شد"}