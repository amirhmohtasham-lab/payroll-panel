"""
Fertilizer Upload Hook
======================
Called after a fertilizer Excel file is uploaded.
Runs the unpivot (wide → long) on the file, saves the updated
file locally, re-uploads it to Google Drive (replacing the original),
and returns the cleaned row count for the caller to persist.

NOTE: Does NOT call db.commit() — the caller (upload_service) handles that.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from app.models.upload import Upload, UploadType
from app.services import drive_service
from app.services.unpivot_fertilizer import run_unpivot

logger = logging.getLogger(__name__)


def post_process_fertilizer_upload(
    db_session,
    upload: Upload,
) -> dict:
    """
    Post-process a fertilizer upload:
      1. Run the wide-to-long unpivot on the local file.
      2. Re-upload the modified file to Drive (replaces original).
      3. Returns cleaned row count for the caller to persist.
    """
    if upload.upload_type != UploadType.FERTILIZER:
        return {
            "unpivot_success": False,
            "row_count": 0,
            "error": "Not a fertilizer upload",
        }

    file_path = upload.stored_path
    if not file_path or not os.path.isfile(file_path):
        return {
            "unpivot_success": False,
            "row_count": 0,
            "error": f"File not found: {file_path}",
        }

    # ── 1. Run the unpivot ──────────────────────────────────────────────
    result = run_unpivot(file_path)
    if not result["success"]:
        logger.warning("unpivot skipped for upload %s: %s", upload.id, result.get("error"))
        return result

    row_count = result["row_count"]

    # ── 2. Re-upload modified file to Drive (replace original) ──────────
    try:
        folder = drive_service.ensure_folder()
        if upload.drive_file_id:
            try:
                drive_service.delete_file(upload.drive_file_id, permanent=True)
            except Exception:
                pass
        label = f"{upload.month_label or upload.month_key} - {upload.original_filename}"
        uploaded = drive_service.upload_file(
            Path(file_path), parent=folder, name=label
        )
        new_drive_id = uploaded.get("id")
        if new_drive_id:
            upload.drive_file_id = new_drive_id
    except drive_service.DriveNotConfiguredError:
        logger.info("Drive not configured, skipping re-upload")
    except Exception as exc:
        logger.exception("drive re-upload failed for %s", file_path)

    logger.info(
        "fertilizer post-process: upload %s → Cleaned Data with %d rows",
        upload.id, row_count,
    )

    return {
        "unpivot_success": True,
        "row_count": row_count,
        "error": None,
    }
