"""
Fertilizer Unpivot Service
==========================
تبدیل شیت [اطلاعات ورودی] از فرمت عریض (wide) به فرمت بلند (long)
با ساختار مناسب برای Pivot Table و گزارش‌گیری

FIX: openpyxl پس از ذخیره مجدد، کش (cache) فرمول‌ها را پاک می‌کند.
این ماژول به جای reliance روی cached values، **توصیه/مساحت** را
از توصیه/هکتار × مساحت محاسبه می‌کند.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


# ─── Configuration ───────────────────────────────────────────────────────────

INPUT_COLUMNS = {
    "rec_date":    1,   # A
    "stage":       2,   # B
    "exec_date":   3,   # C
    "gap":         4,   # D  (formula)
    "rec_num":     5,   # E
    "well":        6,   # F
    "area":        7,   # G
    "plant":       8,   # H
    "variety1":    9,   # I
    "variety2":   10,   # J
    "variety3":   11,   # K
}

FERT_NAME_START   = 12   # L
REC_HA_START      = 22   # V
REC_AREA_START    = 32   # AF  ← FORMULA
CONS_WEIGHT_START = 42   # AP
INVENTORY_START   = 52   # AZ
NUM_SLOTS         = 10

DV_SHEET = "Data Validation"
DV_COL_NAME  = 1   # A
DV_COL_TYPE  = 2   # B
DV_COL_UNIT  = 3   # C
DV_COL_PRICE = 4   # D

TARGET_COLUMNS = [
    "ردیف",
    "تاریخ توصیه",
    "شماره سرک",
    "تاریخ اجرا",
    "فاصله (روز)",
    "شماره توصیه",
    "شماره چاه",
    "مساحت (هکتار)",
    "نوع گیاه",
    "واریته ۱",
    "واریته ۲",
    "واریته ۳",
    "نام کود",
    "قیمت فی خرید",
    "توصیه/هکتار",
    "توصیه/مساحت",
    "مصرفی/وزنی",
    "مصرفی/ریالی",
    "موجودی انبار",
    "واحد",
    "جنس کود",
    "مازاد/کمبود",
    "تحقق%",
]


def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_str(val):
    if val is None:
        return ""
    return str(val).strip()


def build_fertilizer_lookup(ws_dv):
    lookup = {}
    for row in range(2, ws_dv.max_row + 1):
        name = ws_dv.cell(row=row, column=DV_COL_NAME).value
        if name and str(name).strip():
            name = str(name).strip()
            if name not in lookup:
                lookup[name] = {
                    "price": safe_float(ws_dv.cell(row=row, column=DV_COL_PRICE).value),
                    "unit": safe_str(ws_dv.cell(row=row, column=DV_COL_UNIT).value),
                    "type": safe_str(ws_dv.cell(row=row, column=DV_COL_TYPE).value),
                }
    return lookup


def compute_rec_per_area(rec_per_ha, area_numeric, cached_value):
    """
    Compute توصیه/مساحت = توصیه/هکتار × مساحت.
    Uses cached formula value if available, otherwise computes directly.
    Needed because openpyxl discards formula caches on save.
    """
    if cached_value and cached_value > 0:
        return cached_value
    return rec_per_ha * area_numeric


def unpivot_data(ws_input, ws_input_data, fert_lookup):
    cleaned = []
    row_counter = 0

    for src_row in range(3, ws_input.max_row + 1):
        rec_date = ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["rec_date"]).value
        if rec_date is None:
            continue

        rec_date = safe_str(rec_date)
        stage_num = ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["stage"]).value
        exec_date = ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["exec_date"]).value
        gap_days  = ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["gap"]).value
        rec_num   = ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["rec_num"]).value
        well_num  = ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["well"]).value
        area      = safe_float(ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["area"]).value)
        plant_type= ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["plant"]).value
        var1      = ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["variety1"]).value
        var2      = ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["variety2"]).value
        var3      = ws_input_data.cell(row=src_row, column=INPUT_COLUMNS["variety3"]).value

        if isinstance(stage_num, (int, float)):
            stage_num = str(int(stage_num))
        else:
            stage_num = safe_str(stage_num)

        try:
            gap_val = int(float(gap_days)) if gap_days is not None else 0
        except (ValueError, TypeError):
            gap_val = 0

        for slot in range(NUM_SLOTS):
            fert_col = FERT_NAME_START + slot
            fert_name = ws_input.cell(row=src_row, column=fert_col).value
            if fert_name is None or str(fert_name).strip() == "":
                continue
            fert_name = str(fert_name).strip()

            rec_per_ha = safe_float(
                ws_input_data.cell(row=src_row, column=REC_HA_START + slot).value
            )
            rec_area_cached = safe_float(
                ws_input_data.cell(row=src_row, column=REC_AREA_START + slot).value
            )
            rec_per_area = compute_rec_per_area(rec_per_ha, area, rec_area_cached)

            cons_weight = safe_float(
                ws_input_data.cell(row=src_row, column=CONS_WEIGHT_START + slot).value
            )
            inventory = safe_float(
                ws_input_data.cell(row=src_row, column=INVENTORY_START + slot).value
            )

            finfo = fert_lookup.get(fert_name, {})
            price = finfo.get("price", 0.0)
            unit  = finfo.get("unit", "")
            ftype = finfo.get("type", "")

            cons_rial  = cons_weight * price
            surplus    = round(rec_per_area - cons_weight, 2)
            achievement = round((cons_weight / rec_per_area) * 100, 2) if rec_per_area > 0 else 0.0

            row_counter += 1
            cleaned.append([
                row_counter,          # ردیف
                rec_date,             # تاریخ توصیه
                stage_num,            # شماره سرک
                safe_str(exec_date),  # تاریخ اجرا
                gap_val,              # فاصله (روز)
                safe_str(rec_num),    # شماره توصیه
                well_num,             # شماره چاه
                area,                 # مساحت (هکتار)
                plant_type,           # نوع گیاه
                var1,                 # واریته ۱
                var2,                 # واریته ۲
                var3,                 # واریته ۳
                fert_name,            # نام کود
                round(price, 0),      # قیمت فی خرید
                rec_per_ha,           # توصیه/هکتار
                rec_per_area,         # توصیه/مساحت ✅ computed
                cons_weight,          # مصرفی/وزنی
                round(cons_rial, 0),  # مصرفی/ریالی
                inventory,            # موجودی انبار
                unit,                 # واحد
                ftype,                # جنس کود
                surplus,              # مازاد/کمبود
                achievement,          # تحقق%
            ])

    return cleaned


def write_cleaned_sheet(wb, cleaned_rows):
    if "Cleaned Data" in wb.sheetnames:
        del wb["Cleaned Data"]

    ws = wb.create_sheet("Cleaned Data")

    header_font = Font(name="B Nazanin", bold=True, size=11, color="FFFFFF")
    header_fill = PatternFill(start_color="063B5B", end_color="063B5B", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    data_font = Font(name="B Nazanin", size=10)
    data_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    for ci, col_name in enumerate(TARGET_COLUMNS, 1):
        cell = ws.cell(row=1, column=ci, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    for ri, row_data in enumerate(cleaned_rows, 2):
        for ci, value in enumerate(row_data, 1):
            cell = ws.cell(row=ri, column=ci, value=value)
            cell.font = data_font
            cell.alignment = data_align
            cell.border = thin_border
            if isinstance(value, float):
                if abs(value) >= 1_000_000:
                    cell.number_format = "#,##0"
                elif value == int(value):
                    cell.number_format = "#,##0"
                else:
                    cell.number_format = "#,##0.00"
            elif isinstance(value, int):
                cell.number_format = "#,##0"

    col_widths = {
        1: 7, 2: 14, 3: 12, 4: 14, 5: 10,
        6: 12, 7: 10, 8: 12, 9: 14, 10: 14,
        11: 14, 12: 14, 13: 20, 14: 16, 15: 14,
        16: 14, 17: 14, 18: 18, 19: 14, 20: 10,
        21: 10, 22: 14, 23: 10,
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.freeze_panes = "A2"
    last_col = get_column_letter(len(TARGET_COLUMNS))
    ws.auto_filter.ref = f"A1:{last_col}{len(cleaned_rows) + 1}"

    return len(cleaned_rows)


def run_unpivot(file_path: str) -> dict:
    """
    Run the unpivot on an Excel file.

    Args:
        file_path: Absolute path to the .xlsx file.

    Returns:
        dict with keys: success (bool), row_count (int), error (str | None)
    """
    try:
        wb = load_workbook(file_path)
        wb_data = load_workbook(file_path, data_only=True)

        required = {"اطلاعات ورودی", DV_SHEET}
        missing = required - set(wb.sheetnames)
        if missing:
            return {
                "success": False,
                "row_count": 0,
                "error": f"Missing sheets: {', '.join(missing)}. Has: {', '.join(wb.sheetnames)}",
            }

        fert_lookup = build_fertilizer_lookup(wb_data[DV_SHEET])
        cleaned = unpivot_data(wb["اطلاعات ورودی"], wb_data["اطلاعات ورودی"], fert_lookup)

        if not cleaned:
            return {
                "success": False,
                "row_count": 0,
                "error": "No data rows found in 'اطلاعات ورودی'",
            }

        row_count = write_cleaned_sheet(wb, cleaned)
        wb.save(file_path)

        logger.info("unpivot: created 'Cleaned Data' with %d rows from %s", row_count, file_path)

        return {
            "success": True,
            "row_count": row_count,
            "error": None,
        }

    except Exception as e:
        logger.exception("unpivot failed for %s", file_path)
        return {
            "success": False,
            "row_count": 0,
            "error": str(e),
        }


def main():
    """CLI entry point for standalone usage."""
    if len(sys.argv) < 2:
        print("Usage: python3 unpivot_fertilizer_data.py <path_to_excel_file>")
        sys.exit(1)

    file_path = sys.argv[1].strip()
    if not os.path.isfile(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    result = run_unpivot(file_path)
    if result["success"]:
        print(f"\n✅ Done! Sheet 'Cleaned Data' created with {result['row_count']} rows.")
        print("   📌 توصیه/مساحت = توصیه/هکتار × مساحت (محاسبه مستقیم)")
    else:
        print(f"❌ Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
