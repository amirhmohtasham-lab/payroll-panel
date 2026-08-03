"""Greenhouse hydroponic climate analysis endpoints."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.security import current_user_dep
from app.db import get_db
from app.models.greenhouse import GreenhouseRun
from app.models.user import User
from app.schemas.greenhouse import GreenhouseRunDetail, GreenhouseRunListResponse, GreenhouseRunOut
from app.services import greenhouse_service

router = APIRouter(prefix="/api/greenhouse", tags=["greenhouse"])


@router.post("/upload", response_model=GreenhouseRunOut, status_code=201)
async def upload_greenhouse(
    temperature: UploadFile = File(...),
    humidity: UploadFile = File(...),
    temperature_scale: float = Form(10.0),
    condensation_margin: float = Form(2.0),
    vpd_low: float = Form(0.8),
    vpd_high: float = Form(1.1),
    temp_day_low: float = Form(20.0),
    temp_day_high: float = Form(35.0),
    temp_night_low: float = Form(14.0),
    temp_night_high: float = Form(18.0),
    rh_low: float = Form(40.0),
    rh_high: float = Form(75.0),
    day_start: float = Form(7.0),
    day_end: float = Form(19.0),
    irrigation_start: float = Form(8.5),
    irrigation_end: float = Form(14.5),
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user_dep),
):
    if not temperature.filename or not humidity.filename:
        raise HTTPException(status_code=400, detail="هر دو فایل دما و رطوبت الزامی است")

    # Validate settings (mirrors the streamlit app validation)
    if vpd_low >= vpd_high:
        raise HTTPException(status_code=422, detail="VPD target minimum must be lower than its maximum.")
    if temp_day_low >= temp_day_high or temp_night_low >= temp_night_high:
        raise HTTPException(status_code=422, detail="Each temperature minimum must be lower than its maximum.")
    if rh_low >= rh_high:
        raise HTTPException(status_code=422, detail="RH minimum must be lower than RH maximum.")
    if day_start >= day_end or irrigation_start >= irrigation_end:
        raise HTTPException(status_code=422, detail="Schedule start times must be earlier than their end times.")

    try:
        run = await greenhouse_service.process_greenhouse_upload(
            db,
            temp_file=temperature,
            humi_file=humidity,
            temperature_scale=temperature_scale,
            condensation_margin=condensation_margin,
            vpd_low=vpd_low,
            vpd_high=vpd_high,
            temp_day_low=temp_day_low,
            temp_day_high=temp_day_high,
            temp_night_low=temp_night_low,
            temp_night_high=temp_night_high,
            rh_low=rh_low,
            rh_high=rh_high,
            day_start=day_start,
            day_end=day_end,
            irrigation_start=irrigation_start,
            irrigation_end=irrigation_end,
            user=user,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطا در تحلیل: {e}")
    return run


@router.get("/runs", response_model=GreenhouseRunListResponse)
def list_runs(
    limit: int = Query(20, ge=1, le=100),
    db: DbSession = Depends(get_db),
    _: User = Depends(current_user_dep),
):
    runs = db.execute(
        select(GreenhouseRun).order_by(GreenhouseRun.uploaded_at.desc()).limit(limit)
    ).scalars().all()
    return {"items": runs, "total": len(runs)}


@router.get("/runs/{run_id}", response_model=GreenhouseRunDetail)
def get_run(
    run_id: uuid.UUID,
    db: DbSession = Depends(get_db),
    _: User = Depends(current_user_dep),
):
    run = db.get(GreenhouseRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="تحلیل یافت نشد")
    return run


@router.get("/runs/{run_id}/download")
def download_run_zip(
    run_id: uuid.UUID,
    db: DbSession = Depends(get_db),
    _: User = Depends(current_user_dep),
):
    run = db.get(GreenhouseRun, run_id)
    if not run or not run.zip_path:
        raise HTTPException(status_code=404, detail="فایل یافت نشد")
    path = Path(run.zip_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="فایل موجود نیست")
    return FileResponse(path, filename=f"greenhouse_analysis_{run_id}.zip", media_type="application/zip")


@router.delete("/runs/{run_id}", status_code=204)
def delete_run(
    run_id: uuid.UUID,
    db: DbSession = Depends(get_db),
    user: User = Depends(current_user_dep),
):
    run = db.get(GreenhouseRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="تحلیل یافت نشد")
    work = Path(run.output_dir).parent if run.output_dir else None
    db.delete(run)
    db.commit()
    if work and work.exists():
        import shutil
        shutil.rmtree(work, ignore_errors=True)
    return None
