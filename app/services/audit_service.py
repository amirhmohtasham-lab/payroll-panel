"""Thin wrapper around audit_engine — keeps API routes decoupled from audit internals."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from audit_engine import fertilizer as fertilizer_engine
from audit_engine import payroll as payroll_engine


def audit_payroll(path: Path) -> payroll_engine.AuditResult:
    return payroll_engine.audit_workbook(path)


def write_payroll_highlight(result: payroll_engine.AuditResult, src: Path, dest: Path) -> None:
    payroll_engine.write_highlighted_workbook(result, src, dest)


def payroll_issues_jsonable(result: payroll_engine.AuditResult) -> list[dict[str, Any]]:
    return [asdict(i) for i in result.issues]


def payroll_summary(result: payroll_engine.AuditResult) -> dict[str, Any]:
    data = payroll_engine.result_to_jsonable(result)
    return {
        "sheet_count": len(result.sheets),
        "worker_rows": sum(s.worker_rows for s in result.sheets),
        "sheets": data["sheets"],
    }


def audit_fertilizer(path: Path) -> fertilizer_engine.FertilizerResult:
    return fertilizer_engine.audit_workbook(path)


def write_fertilizer_highlight(
    result: fertilizer_engine.FertilizerResult, src: Path, dest: Path
) -> None:
    fertilizer_engine.write_highlighted_workbook(result, src, dest)


def fertilizer_issues_jsonable(result: fertilizer_engine.FertilizerResult) -> list[dict[str, Any]]:
    return [asdict(i) for i in result.issues]


def report_foreman(records: list[dict[str, Any]]) -> str:
    return payroll_engine.report_foreman(records)


def report_well(records: list[dict[str, Any]]) -> str:
    return payroll_engine.report_well(records)
