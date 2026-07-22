"""Payroll (صورت کارگری) workbook audit engine.

See audit_engine/README.md — this is a from-scratch, API-compatible reimplementation
of the original ~/.hermes/scripts/farm_payroll_audit.py, matching the interface that
app.py relied on. Replace the rule logic below if the real business rules differ.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path

from audit_engine.common import (
    ERROR_FILL,
    Issue,
    WARN_FILL,
    find_header_cell,
    open_workbook_data_only,
    open_workbook_for_write,
    save_highlighted,
    to_number,
)

FOREMAN_KEYWORDS = ["سرکارگر", "سر کارگر", "پیمانکار"]
WORKPLACE_KEYWORDS = ["چاه", "محل", "محدوده", "مزرعه"]
PERIOD_KEYWORDS = ["دوره", "تاریخ", "ماه"]
NAME_KEYWORDS = ["نام و نام خانوادگی", "نام کارگر", "نام"]
# NOTE: intentionally excludes the bare "کارگر" token — it's a substring of
# "سرکارگر" (foreman) meta rows and would cause the name-column header search
# to false-positive on the foreman row above the real table header.
WORKER_GROSS_KEYWORDS = ["جمع دریافتی", "مبلغ قابل پرداخت", "دستمزد", "خالص پرداختی"]
DESC_GROSS_KEYWORDS = ["جمع", "هزینه", "توضیحات"]


@dataclass
class SheetResult:
    name: str
    foreman: str | None = None
    list_no: str | None = None
    workplace: str | None = None
    period: str | None = None
    worker_rows: int = 0
    worker_gross: float | None = None
    desc_gross: float | None = None
    issues: list[Issue] = field(default_factory=list)
    _name_cell_rows: list[int] = field(default_factory=list, repr=False)
    _gross_col: int | None = field(default=None, repr=False)


@dataclass
class AuditResult:
    file: str = ""
    sheets: list[SheetResult] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


def _extract_meta(ws, sheet_name: str) -> tuple[str | None, str | None, str | None]:
    foreman = workplace = period = None
    for row in ws.iter_rows(min_row=1, max_row=min(10, ws.max_row)):
        for cell in row:
            if cell.value is None:
                continue
            text = str(cell.value).strip()
            if not text:
                continue
            if foreman is None and any(k in text for k in FOREMAN_KEYWORDS):
                # value is often in the next cell
                neighbor = ws.cell(row=cell.row, column=cell.column + 1).value
                foreman = str(neighbor).strip() if neighbor else text
            if workplace is None and any(k in text for k in WORKPLACE_KEYWORDS):
                neighbor = ws.cell(row=cell.row, column=cell.column + 1).value
                workplace = str(neighbor).strip() if neighbor else text
            if period is None and any(k in text for k in PERIOD_KEYWORDS):
                neighbor = ws.cell(row=cell.row, column=cell.column + 1).value
                period = str(neighbor).strip() if neighbor else text
    return foreman, workplace, period


def _audit_sheet(ws, sheet_name: str) -> SheetResult:
    sr = SheetResult(name=sheet_name)
    sr.foreman, sr.workplace, sr.period = _extract_meta(ws, sheet_name)

    header = find_header_cell(ws, NAME_KEYWORDS)
    gross_header = find_header_cell(ws, WORKER_GROSS_KEYWORDS)

    if header is None:
        sr.issues.append(
            Issue(severity="error", code="NO_HEADER", sheet=sheet_name, message="ستون نام کارگر یافت نشد")
        )
        return sr

    header_row, name_col = header
    gross_col = gross_header[1] if gross_header else None
    sr._gross_col = gross_col

    total_gross = 0.0
    row_count = 0
    for row_idx in range(header_row + 1, ws.max_row + 1):
        name_val = ws.cell(row=row_idx, column=name_col).value
        if name_val is None or str(name_val).strip() == "":
            continue
        row_count += 1
        sr._name_cell_rows.append(row_idx)

        if gross_col:
            gross_val = to_number(ws.cell(row=row_idx, column=gross_col).value)
            if gross_val is None:
                sr.issues.append(
                    Issue(
                        severity="warn",
                        code="MISSING_AMOUNT",
                        sheet=sheet_name,
                        message=f"ردیف {row_idx}: مبلغ دریافتی خالی یا نامعتبر است",
                    )
                )
            elif gross_val < 0:
                sr.issues.append(
                    Issue(
                        severity="error",
                        code="NEGATIVE_AMOUNT",
                        sheet=sheet_name,
                        message=f"ردیف {row_idx}: مبلغ دریافتی منفی است ({gross_val:,.0f})",
                    )
                )
            elif gross_val == 0:
                sr.issues.append(
                    Issue(
                        severity="warn",
                        code="ZERO_AMOUNT",
                        sheet=sheet_name,
                        message=f"ردیف {row_idx}: مبلغ دریافتی صفر است",
                    )
                )
            else:
                total_gross += gross_val

    sr.worker_rows = row_count
    sr.worker_gross = total_gross if gross_col else None

    desc_header = find_header_cell(ws, DESC_GROSS_KEYWORDS, max_row=ws.max_row)
    if desc_header and desc_header[1] != gross_col:
        desc_col = desc_header[1]
        desc_total = 0.0
        for row_idx in range(desc_header[0] + 1, ws.max_row + 1):
            v = to_number(ws.cell(row=row_idx, column=desc_col).value)
            if v:
                desc_total += v
        sr.desc_gross = desc_total or None

    if row_count == 0:
        sr.issues.append(
            Issue(severity="warn", code="EMPTY_SHEET", sheet=sheet_name, message="هیچ کارگری در این شیت ثبت نشده")
        )

    return sr


def audit_workbook(path: Path) -> AuditResult:
    wb = open_workbook_data_only(path)
    result = AuditResult(file=str(path))
    for ws in wb.worksheets:
        sr = _audit_sheet(ws, ws.title)
        result.sheets.append(sr)
        result.issues.extend(sr.issues)
    wb.close()
    return result


def write_highlighted_workbook(result: AuditResult, src: Path, dest: Path) -> None:
    wb = open_workbook_for_write(src)
    by_sheet: dict[str, SheetResult] = {s.name: s for s in result.sheets}
    for ws in wb.worksheets:
        sr = by_sheet.get(ws.title)
        if not sr:
            continue
        error_rows = {
            int(i.message.split("ردیف ")[1].split(":")[0])
            for i in sr.issues
            if i.severity == "error" and "ردیف" in i.message
        }
        warn_rows = {
            int(i.message.split("ردیف ")[1].split(":")[0])
            for i in sr.issues
            if i.severity == "warn" and "ردیف" in i.message
        }
        for row_idx in error_rows | warn_rows:
            fill = ERROR_FILL if row_idx in error_rows else WARN_FILL
            for cell in ws[row_idx]:
                cell.fill = fill
    save_highlighted(wb, dest)


def result_to_jsonable(result: AuditResult) -> dict:
    return {
        "file": result.file,
        "sheets": [
            {
                "name": s.name,
                "foreman": s.foreman,
                "list_no": s.list_no,
                "workplace": s.workplace,
                "period": s.period,
                "worker_rows": s.worker_rows,
                "worker_gross": s.worker_gross,
                "desc_gross": s.desc_gross,
                "error_count": len([i for i in s.issues if i.severity == "error"]),
                "warn_count": len([i for i in s.issues if i.severity == "warn"]),
            }
            for s in result.sheets
        ],
        "issues": [asdict(i) for i in result.issues],
    }


def report_foreman(records: list[dict]) -> str:
    """Markdown table: total worker_gross per foreman across all ingested records."""
    totals: dict[str, float] = {}
    for rec in records:
        for s in rec.get("sheets", []):
            f = s.get("foreman") or "نامشخص"
            totals[f] = totals.get(f, 0.0) + (s.get("worker_gross") or 0)
    lines = ["| سرکارگر | جمع دریافتی |", "|---|---|"]
    for f, v in sorted(totals.items(), key=lambda x: -x[1]):
        lines.append(f"| {f} | {v:,.0f} |")
    return "\n".join(lines)


def report_well(records: list[dict]) -> str:
    """Markdown table: total desc_gross per workplace across all ingested records."""
    totals: dict[str, float] = {}
    for rec in records:
        for s in rec.get("sheets", []):
            w = s.get("workplace") or "نامشخص"
            totals[w] = totals.get(w, 0.0) + (s.get("desc_gross") or 0)
    lines = ["| چاه/محدوده | هزینه |", "|---|---|"]
    for w, v in sorted(totals.items(), key=lambda x: -x[1]):
        lines.append(f"| {w} | {v:,.0f} |")
    return "\n".join(lines)
