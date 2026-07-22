"""Months/reports/archive endpoints — DB-backed, replacing index.json/fertilizer_index.json queries."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.core.security import require_roles
from app.db import get_db
from app.models.upload import Upload, UploadType
from app.models.user import User, UserRole
from app.services import audit_service, upload_service

router = APIRouter(tags=["reports"])


def _month_list_items(uploads: list[Upload]) -> list[dict[str, Any]]:
    items = []
    for rec in sorted(uploads, key=lambda u: u.month_key, reverse=True):
        status_label, status_text = upload_service.status_label_and_text(rec.error_count, rec.warn_count)
        items.append(
            {
                "month_key": rec.month_key,
                "month_label": rec.month_label,
                "filename": rec.original_filename,
                "uploaded_at": rec.uploaded_at,
                "error_count": rec.error_count,
                "warn_count": rec.warn_count,
                "status_label": status_label,
                "status_text": status_text,
                "worker_rows": (rec.audit_summary or {}).get("worker_rows", 0)
                if rec.upload_type == UploadType.PAYROLL
                else None,
                "row_count": rec.row_count if rec.upload_type == UploadType.FERTILIZER else None,
                "fertilizer_count": rec.fertilizer_count
                if rec.upload_type == UploadType.FERTILIZER
                else None,
            }
        )
    return items


@router.get("/api/months")
def api_months(
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ACCOUNTANT)),
):
    uploads = list(
        db.execute(select(Upload).where(Upload.upload_type == UploadType.PAYROLL)).scalars()
    )
    items = _month_list_items(uploads)
    total_errors = sum(u.error_count for u in uploads)
    total_warns = sum(u.warn_count for u in uploads)
    total_workers = sum((u.audit_summary or {}).get("worker_rows", 0) for u in uploads)
    return {
        "items": items,
        "summary": {
            "month_count": len(items),
            "total_errors": total_errors,
            "total_warns": total_warns,
            "total_workers": total_workers,
        },
    }


@router.get("/api/months/{month_key}")
def api_month_detail(
    month_key: str,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ACCOUNTANT)),
):
    rec = db.execute(
        select(Upload).where(Upload.upload_type == UploadType.PAYROLL, Upload.month_key == month_key)
    ).scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="ماه یافت نشد")
    return upload_service.to_public_dict(rec)


@router.get("/api/fertilizer/months")
def api_fertilizer_months(
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ACCOUNTANT)),
):
    uploads = list(
        db.execute(select(Upload).where(Upload.upload_type == UploadType.FERTILIZER)).scalars()
    )
    items = _month_list_items(uploads)
    total_errors = sum(u.error_count for u in uploads)
    total_warns = sum(u.warn_count for u in uploads)
    total_rows = sum(u.row_count or 0 for u in uploads)
    return {
        "items": items,
        "summary": {
            "month_count": len(items),
            "total_errors": total_errors,
            "total_warns": total_warns,
            "total_rows": total_rows,
        },
    }


@router.get("/api/fertilizer/months/{month_key}")
def api_fertilizer_month_detail(
    month_key: str,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ACCOUNTANT)),
):
    rec = db.execute(
        select(Upload).where(Upload.upload_type == UploadType.FERTILIZER, Upload.month_key == month_key)
    ).scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="ماه یافت نشد")
    return upload_service.to_public_dict(rec)


@router.get("/api/archive")
def api_archive(
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ACCOUNTANT)),
):
    payroll_uploads = list(
        db.execute(select(Upload).where(Upload.upload_type == UploadType.PAYROLL)).scalars()
    )
    fertilizer_uploads = list(
        db.execute(select(Upload).where(Upload.upload_type == UploadType.FERTILIZER)).scalars()
    )

    workforce_items = [
        {
            "month_key": u.month_key,
            "type": "workforce",
            "module_label": "صورت کارگری",
            "label": u.month_label,
            "filename": u.original_filename,
            "uploaded_at": u.uploaded_at,
            "error_count": u.error_count,
            "warn_count": u.warn_count,
        }
        for u in payroll_uploads
    ]
    fertilizer_items = [
        {
            "month_key": u.month_key,
            "type": "fertilizer",
            "module_label": "مصرف کود",
            "label": f"{u.crop or ''} - {u.season or u.month_label}",
            "filename": u.original_filename,
            "uploaded_at": u.uploaded_at,
            "error_count": u.error_count,
            "warn_count": u.warn_count,
        }
        for u in fertilizer_uploads
    ]

    merged = sorted(workforce_items + fertilizer_items, key=lambda x: x["uploaded_at"], reverse=True)

    return {
        "items": merged,
        "summary": {
            "workforce_count": len(workforce_items),
            "fertilizer_count": len(fertilizer_items),
            "total": len(merged),
        },
    }


def _rec_to_sheets_dict(u: Upload) -> list[dict[str, Any]]:
    return (u.audit_summary or {}).get("sheets", [])


@router.get("/api/reports/data")
def api_reports_data(
    db: DbSession = Depends(get_db), _: User = Depends(require_roles(UserRole.ACCOUNTANT))
):
    """Structured, chart-friendly aggregation across all ingested payroll uploads."""
    uploads = list(
        db.execute(select(Upload).where(Upload.upload_type == UploadType.PAYROLL)).scalars()
    )

    f_totals: dict[str, float] = defaultdict(float)
    w_totals: dict[str, float] = defaultdict(float)
    m_totals: dict[str, dict[str, float]] = defaultdict(lambda: {"worker": 0.0, "desc": 0.0})
    status_counts = {"clean": 0, "error": 0, "warn": 0}
    f_ts: dict[str, dict[str, float]] = defaultdict(dict)
    all_months: set[str] = set()

    for u in uploads:
        month = u.month_key
        all_months.add(month)
        for s in _rec_to_sheets_dict(u):
            f = s.get("foreman") or "نامشخص"
            w = s.get("workplace") or "نامشخص"
            wg = _to_float(s.get("worker_gross"))
            dg = _to_float(s.get("desc_gross"))

            f_totals[f] += wg
            w_totals[w] += dg
            m_totals[month]["worker"] += wg
            m_totals[month]["desc"] += dg
            f_ts[f][month] = f_ts[f].get(month, 0) + wg

            if s.get("error_count", 0) > 0:
                status_counts["error"] += 1
            elif s.get("warn_count", 0) > 0:
                status_counts["warn"] += 1
            else:
                status_counts["clean"] += 1

    sorted_months = sorted(all_months)

    def to_labels_items(d: dict[str, float]) -> dict[str, Any]:
        items = sorted(d.items(), key=lambda x: -x[1])
        return {"labels": [x[0] for x in items], "values": [round(x[1]) for x in items]}

    foreman_matrix = {fm: {m: round(mdict.get(m, 0)) for m in sorted_months} for fm, mdict in f_ts.items()}

    return {
        "foreman_totals": to_labels_items(f_totals),
        "well_totals": to_labels_items(w_totals),
        "monthly": {
            "labels": sorted_months,
            "worker": [round(m_totals[m]["worker"]) for m in sorted_months],
            "desc": [round(m_totals[m]["desc"]) for m in sorted_months],
        },
        "status": status_counts,
        "foreman_monthly": {
            "foremen": list(foreman_matrix.keys()),
            "months": sorted_months,
            "matrix": foreman_matrix,
        },
        "month_count": len(sorted_months),
        "sheet_count": sum(len(_rec_to_sheets_dict(u)) for u in uploads),
    }


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def _records_for_report(uploads: list[Upload]) -> list[dict[str, Any]]:
    return [{"file": u.original_filename, "sheets": _rec_to_sheets_dict(u)} for u in uploads]


def _markdown_table_to_html(md: str) -> str:
    lines = [ln.strip() for ln in md.splitlines() if ln.strip()]
    if len(lines) < 2:
        return f"<pre>{md}</pre>"
    out = ["<table>"]
    for i, ln in enumerate(lines):
        if ln.startswith("|---"):
            continue
        cells = [c.strip() for c in ln.strip("|").split("|")]
        tag = "th" if i == 0 else "td"
        out.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
    out.append("</table>")
    return "\n".join(out)


@router.get("/api/reports/{report_type}")
def api_reports(
    report_type: str,
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ACCOUNTANT)),
):
    uploads = list(
        db.execute(select(Upload).where(Upload.upload_type == UploadType.PAYROLL)).scalars()
    )
    if not uploads:
        return {"html": "<p>هنوز فایلی ingest نشده.</p>"}

    records = _records_for_report(uploads)
    if report_type == "foreman":
        md = audit_service.report_foreman(records)
    elif report_type == "well":
        md = audit_service.report_well(records)
    else:
        raise HTTPException(status_code=400)
    html = "<div style='overflow:auto'>" + _markdown_table_to_html(md) + "</div>"
    return {"html": html}
