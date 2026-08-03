"""Greenhouse analysis orchestration — saves uploads, runs the pipeline, stores results."""

from __future__ import annotations

import io
import uuid
import zipfile
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session as DbSession

from app.config import get_settings
from app.models.greenhouse import GreenhouseRun
from app.models.user import User
from app.services import greenhouse_analysis
from app.services.storage_service import sanitize_filename


def _run_dir(run_id: uuid.UUID) -> Path:
    settings = get_settings()
    path = settings.data_dir / "greenhouse" / str(run_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _make_zip(folder: Path, zip_path: Path) -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(folder))
    zip_path.write_bytes(buffer.getvalue())


async def process_greenhouse_upload(
    db: DbSession,
    *,
    temp_file: UploadFile,
    humi_file: UploadFile,
    temperature_scale: float,
    condensation_margin: float,
    vpd_low: float,
    vpd_high: float,
    temp_day_low: float,
    temp_day_high: float,
    temp_night_low: float,
    temp_night_high: float,
    rh_low: float,
    rh_high: float,
    day_start: float,
    day_end: float,
    irrigation_start: float,
    irrigation_end: float,
    user: User,
) -> GreenhouseRun:
    temp_name = sanitize_filename(temp_file.filename or "temperature.csv")
    humi_name = sanitize_filename(humi_file.filename or "humidity.csv")

    run = GreenhouseRun(
        temp_filename=temp_name,
        humi_filename=humi_name,
        uploaded_by=user.id,
    )
    db.add(run)

    temp_ext = Path(temp_name).suffix.lower() or ".csv"
    humi_ext = Path(humi_name).suffix.lower() or ".csv"

    run_id = uuid.uuid4()
    run.id = run_id
    work = _run_dir(run_id)

    temp_path = work / f"temperature_input{temp_ext}"
    humi_path = work / f"humidity_input{humi_ext}"
    temp_path.write_bytes(await temp_file.read())
    humi_path.write_bytes(await humi_file.read())

    run.temp_path = str(temp_path)
    run.humi_path = str(humi_path)
    output = work / "results"
    run.output_dir = str(output)

    db.flush()

    try:
        result = greenhouse_analysis.run_complete_analysis(
            temp_path,
            humi_path,
            output,
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
        )
    except Exception:
        db.delete(run)
        db.commit()
        raise

    run.row_count = result["metrics"]["days"]
    run.metrics = result["metrics"]
    run.tables = result["tables"]
    run.output_dir = result["output_dir"]

    zip_path = work / "greenhouse_results.zip"
    _make_zip(Path(result["output_dir"]), zip_path)
    run.zip_path = str(zip_path)

    db.commit()
    db.refresh(run)
    return run
