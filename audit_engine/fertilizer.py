"""Fertilizer consumption (مصرف کود) workbook audit engine.

See audit_engine/README.md — from-scratch, API-compatible reimplementation of the
original ~/.hermes/scripts/fertilizer_audit.py.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
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

FERTILIZER_KEYWORDS = ["کود", "نوع کود"]
QUANTITY_KEYWORDS = ["مقدار", "میزان مصرف", "وزن"]
DATE_KEYWORDS = ["تاریخ", "دوره"]


@dataclass
class FertilizerRow:
    row: int
    fertilizer: str | None
    quantity: float | None


@dataclass
class FertilizerResult:
    file: str = ""
    rows: list[FertilizerRow] = field(default_factory=list)
    fertilizers: set[str] = field(default_factory=set)
    issues: list[Issue] = field(default_factory=list)


def audit_workbook(path: Path) -> FertilizerResult:
    wb = open_workbook_data_only(path)
    result = FertilizerResult(file=str(path))

    for ws in wb.worksheets:
        fert_header = find_header_cell(ws, FERTILIZER_KEYWORDS)
        qty_header = find_header_cell(ws, QUANTITY_KEYWORDS)

        if not fert_header:
            result.issues.append(
                Issue(severity="error", code="NO_HEADER", sheet=ws.title, message="ستون نوع کود یافت نشد")
            )
            continue

        header_row, fert_col = fert_header
        qty_col = qty_header[1] if qty_header else None

        for row_idx in range(header_row + 1, ws.max_row + 1):
            fert_val = ws.cell(row=row_idx, column=fert_col).value
            if fert_val is None or str(fert_val).strip() == "":
                continue
            fert_name = str(fert_val).strip()
            result.fertilizers.add(fert_name)

            qty_val = to_number(ws.cell(row=row_idx, column=qty_col).value) if qty_col else None
            if qty_col and qty_val is None:
                result.issues.append(
                    Issue(
                        severity="warn",
                        code="MISSING_QUANTITY",
                        sheet=ws.title,
                        message=f"ردیف {row_idx}: مقدار مصرف خالی یا نامعتبر است",
                    )
                )
            elif qty_val is not None and qty_val < 0:
                result.issues.append(
                    Issue(
                        severity="error",
                        code="NEGATIVE_QUANTITY",
                        sheet=ws.title,
                        message=f"ردیف {row_idx}: مقدار مصرف منفی است ({qty_val})",
                    )
                )

            result.rows.append(FertilizerRow(row=row_idx, fertilizer=fert_name, quantity=qty_val))

    wb.close()
    return result


def write_highlighted_workbook(result: FertilizerResult, src: Path, dest: Path) -> None:
    wb = open_workbook_for_write(src)
    issues_by_sheet: dict[str, list[Issue]] = {}
    for i in result.issues:
        issues_by_sheet.setdefault(i.sheet, []).append(i)

    for ws in wb.worksheets:
        issues = issues_by_sheet.get(ws.title, [])
        error_rows = {
            int(i.message.split("ردیف ")[1].split(":")[0]) for i in issues if i.severity == "error" and "ردیف" in i.message
        }
        warn_rows = {
            int(i.message.split("ردیف ")[1].split(":")[0]) for i in issues if i.severity == "warn" and "ردیف" in i.message
        }
        for row_idx in error_rows | warn_rows:
            fill = ERROR_FILL if row_idx in error_rows else WARN_FILL
            for cell in ws[row_idx]:
                cell.fill = fill
    save_highlighted(wb, dest)


def result_to_jsonable(result: FertilizerResult) -> dict:
    return {
        "file": result.file,
        "row_count": len(result.rows),
        "fertilizer_count": len(result.fertilizers),
        "fertilizers": sorted(result.fertilizers),
        "issues": [asdict(i) for i in result.issues],
    }
