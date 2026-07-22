#!/usr/bin/env python3
"""Web panel v2: upload monthly payroll xlsx, audit, Drive backup, reports + user auth."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sys
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import jwt
from fastapi import FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

PANEL_DIR = Path(__file__).resolve().parent
HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
UPLOAD_DIR = PANEL_DIR / "uploads"
DATA_DIR = PANEL_DIR / "data"
INDEX_PATH = DATA_DIR / "index.json"
FERTILIZER_INDEX_PATH = DATA_DIR / "fertilizer_index.json"
CONFIG_PATH = PANEL_DIR / "config.json"
STATIC_DIR = PANEL_DIR / "static"
AUDIT_SCRIPT = HERMES_HOME / "scripts" / "farm_payroll_audit.py"
USERS_PATH = DATA_DIR / "users.json"
SESSIONS_PATH = DATA_DIR / "sessions.json"

sys.path.insert(0, str(PANEL_DIR))
from drive_sync import delete_file, upload_file  # noqa: E402

sys.path.insert(0, str(HERMES_HOME / "scripts"))
from farm_payroll_audit import (  # noqa: E402
    AuditResult,
    audit_workbook,
    ingest_result,
    load_ingested,
    report_foreman,
    report_well,
    result_to_jsonable,
    write_highlighted_workbook,
)
from farm_payroll_audit import Issue as AuditIssue  # noqa: E402
from fertilizer_audit import (  # noqa: E402
    audit_workbook as fert_audit_workbook,
    write_highlighted_workbook as fert_write_highlighted,
    load_ingested as fert_load_ingested,
    ingest_result as fert_ingest_result,
)

# ── Config ──
JWT_SECRET = os.environ.get("PAYROLL_JWT_SECRET", "change-me-in-production-bzhz1405")
JWT_ALGO = "HS256"
JWT_EXPIRY_HOURS = 24

PIN = os.environ.get("PAYROLL_PANEL_PIN", "behzadian1405")
HOST = os.environ.get("PAYROLL_PANEL_HOST", "0.0.0.0")
PORT = int(os.environ.get("PAYROLL_PANEL_PORT", "8765"))

app = FastAPI(title="Payroll Panel v2", docs_url=None, redoc_url=None)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ── User / Auth helpers ──

def load_users() -> dict[str, Any]:
    if not USERS_PATH.exists():
        return {}
    return json.loads(USERS_PATH.read_text(encoding="utf-8"))


def create_token(username: str, role: str, name: str) -> str:
    payload = {
        "sub": username,
        "role": role,
        "name": name,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="نشست منقضی شده. دوباره وارد شوید.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="توکن نامعتبر است.")


def require_auth(x_auth_token: str | None = Header(default=None)) -> dict[str, Any]:
    """Validate JWT token from header, return user payload {'sub','role','name'}."""
    if not x_auth_token:
        raise HTTPException(status_code=401, detail="لطفاً ابتدا وارد شوید.")
    return decode_token(x_auth_token)


def require_role(required: str) -> dict[str, Any]:
    """Decorator-returning helper — use inside endpoint:
    user = require_role('accounting')
    or user = require_role('operator')
    """
    # This is a helper that returns the user payload after checking header
    # We'll use it differently — see endpoint patterns below.
    pass


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_index() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_PATH.exists():
        return {"uploads": {}}
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def save_index(idx: dict[str, Any]) -> None:
    INDEX_PATH.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_drive_folder() -> str:
    cfg = load_config()
    fid = cfg.get("drive_folder_id")
    if fid:
        return fid
    bootstrap = PANEL_DIR / "bootstrap_drive.py"
    if bootstrap.exists():
        import subprocess
        subprocess.run([sys.executable, str(bootstrap)], check=False)
        cfg = load_config()
        fid = cfg.get("drive_folder_id")
    if not fid:
        raise HTTPException(status_code=503, detail="پوشه Drive تنظیم نشده. bootstrap_drive.py را اجرا کنید.")
    return fid


# ── Auth System ────────────────────────────────────────────────────────────
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _load_users() -> dict:
    if not USERS_PATH.exists():
        # seed default users
        users = {
            "operator1": {"password": _hash_password("op1405"), "role": "operator", "name": "اپراتور"},
            "admin1": {"password": _hash_password("acc1405"), "role": "accountant", "name": "حسابدار"},
        }
        USERS_PATH.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")
        return users
    return json.loads(USERS_PATH.read_text(encoding="utf-8"))


def _save_users(users: dict) -> None:
    USERS_PATH.write_text(json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_sessions() -> dict:
    if not SESSIONS_PATH.exists():
        return {}
    return json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))


def _save_sessions(sessions: dict) -> None:
    SESSIONS_PATH.write_text(json.dumps(sessions, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_session(request: Request) -> dict | None:
    token = request.cookies.get("session_token")
    if not token:
        return None
    sessions = _load_sessions()
    return sessions.get(token)


def require_role(request: Request, allowed_roles: list[str]) -> dict:
    session = _get_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="لاگین نشده")
    if session.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="دسترسی ندارید")
    return session


# ── Decorator-based auth helpers ──

from functools import wraps

def require_session(allowed_roles: list[str] | None = None):
    """Decorator that injects user session dict into endpoint as 'session' kwarg."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find request in args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                raise HTTPException(status_code=500, detail="No request in handler")
            session = _get_session(request)
            if not session:
                raise HTTPException(status_code=401, detail="لاگین نشده")
            if allowed_roles and session.get("role") not in allowed_roles:
                raise HTTPException(status_code=403, detail="دسترسی ندارید")
            kwargs["session"] = session
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ── Auth Routes ────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return HTMLResponse((STATIC_DIR / "login.html").read_text(encoding="utf-8"))


@app.post("/api/login")
async def api_login(body: dict):
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="نام کاربری و رمز را وارد کنید")
    users = _load_users()
    user = users.get(username)
    if not user or user["password"] != _hash_password(password):
        raise HTTPException(status_code=401, detail="نام کاربری یا رمز نادرست است")

    token = secrets.token_hex(24)
    sessions = _load_sessions()
    sessions[token] = {
        "username": username,
        "role": user["role"],
        "name": user.get("name", username),
        "created_at": utc_now(),
    }
    _save_sessions(sessions)

    role_to_panel = {"operator": "operator", "accountant": "index"}
    redirect = f"/{role_to_panel.get(user['role'], 'index')}"

    resp = JSONResponse({"ok": True, "redirect": redirect, "role": user["role"], "name": user.get("name", username)})
    resp.set_cookie(key="session_token", value=token, httponly=True, samesite="strict", max_age=86400 * 7)
    return resp


@app.post("/api/logout")
def api_logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        sessions = _load_sessions()
        sessions.pop(token, None)
        _save_sessions(sessions)
    resp = RedirectResponse(url="/login")
    resp.delete_cookie("session_token")
    return resp


@app.get("/api/me")
def api_me(request: Request):
    session = _get_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="لاگین نشده")
    return {"username": session["username"], "role": session["role"], "name": session["name"]}


# ── Admin: manage users ──
@app.get("/api/users")
def api_users(request: Request):
    require_role(request, ["accountant"])
    users = _load_users()
    safe = {u: {"role": v["role"], "name": v.get("name", u)} for u, v in users.items()}
    return {"users": safe}


@app.post("/api/users")
async def api_create_user(request: Request, body: dict):
    require_role(request, ["accountant"])
    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    role = body.get("role", "operator")
    name = body.get("name", username)
    if not username or not password:
        raise HTTPException(status_code=400, detail="نام کاربری و رمز الزامی است")
    users = _load_users()
    if username in users:
        raise HTTPException(status_code=409, detail="کاربر وجود دارد")
    users[username] = {"password": _hash_password(password), "role": role, "name": name}
    _save_users(users)
    return {"ok": True}


@app.delete("/api/users/{username}")
def api_delete_user(username: str, request: Request):
    require_role(request, ["accountant"])
    users = _load_users()
    if username not in users:
        raise HTTPException(status_code=404)
    del users[username]
    _save_users(users)
    return {"ok": True}


@app.patch("/api/users/{username}")
async def api_update_user(username: str, request: Request, body: dict):
    require_role(request, ["accountant"])
    users = _load_users()
    if username not in users:
        raise HTTPException(status_code=404)
    if "password" in body:
        users[username]["password"] = _hash_password(body["password"])
    if "role" in body:
        users[username]["role"] = body["role"]
    if "name" in body:
        users[username]["name"] = body["name"]
    _save_users(users)
    return {"ok": True}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Redirect root to login or appropriate panel based on session."""
    session = _get_session(request)
    if session:
        role = session.get("role", "")
        if role == "operator":
            return RedirectResponse(url="/operator")
        return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))
    return RedirectResponse(url="/login")


@app.get("/index")
def index_page():
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.get("/operator", response_class=HTMLResponse)
def operator_panel():
    return HTMLResponse((STATIC_DIR / "operator.html").read_text(encoding="utf-8"))


@app.get("/api/meta")
def api_meta(request: Request):
    require_role(request, ["operator", "accountant"])
    cfg = load_config()
    return {
        "drive_folder_id": cfg.get("drive_folder_id"),
        "drive_folder_name": cfg.get("drive_folder_name"),
        "panel_version": "2.0.0",
    }


@app.get("/api/months")
def api_months(request: Request):
    require_role(request, ["operator", "accountant"])
    idx = load_index()
    items = []
    for key, rec in sorted(idx.get("uploads", {}).items(), reverse=True):
        errors = rec.get("error_count", 0)
        warns = rec.get("warn_count", 0)
        if errors > 0:
            status_label = "error"
            status_text = f"{errors} خطا"
        elif warns > 0:
            status_label = "warn"
            status_text = f"{warns} هشدار"
        else:
            status_label = "ok"
            status_text = "تأیید"
        items.append({
            "month_key": key,
            "month_label": rec.get("month_label", key),
            "filename": rec.get("filename"),
            "uploaded_at": rec.get("uploaded_at"),
            "error_count": errors,
            "warn_count": warns,
            "status_label": status_label,
            "status_text": status_text,
            "worker_rows": rec.get("audit_summary", {}).get("worker_rows", 0),
        })
    data = load_ingested()
    # summary cards
    total_errors = sum(r.get("error_count", 0) for r in idx.get("uploads", {}).values()) if idx.get("uploads") else 0
    total_warns = sum(r.get("warn_count", 0) for r in idx.get("uploads", {}).values()) if idx.get("uploads") else 0
    total_workers = sum(r.get("audit_summary", {}).get("worker_rows", 0) for r in idx.get("uploads", {}).values()) if idx.get("uploads") else 0
    return {
        "items": items,
        "summary": {
            "month_count": len(items),
            "total_errors": total_errors,
            "total_warns": total_warns,
            "total_workers": total_workers,
        },
    }


@app.get("/api/months/{month_key}")
def api_month_detail(month_key: str, request: Request):
    require_role(request, ["operator", "accountant"])
    idx = load_index()
    rec = idx.get("uploads", {}).get(month_key)
    if not rec:
        raise HTTPException(status_code=404, detail="ماه یافت نشد")
    return _public_record(rec, month_key)


def _public_record(rec: dict[str, Any], month_key: str) -> dict[str, Any]:
    out = dict(rec)
    out["month_key"] = month_key
    if rec.get("highlight_file"):
        out["highlight_url"] = f"/api/download/{month_key}/highlighted"
    # group issues by code for UI
    issues = out.get("issues", [])
    grouped = {}
    for i in issues:
        code = i.get("code", "OTHER")
        grouped.setdefault(code, {"code": code, "count": 0, "items": []})
        grouped[code]["count"] += 1
        grouped[code]["items"].append(i)
    out["issues_grouped"] = list(grouped.values())
    return out


@app.get("/api/download/{month_key}/highlighted")
def download_highlight(month_key: str, request: Request):
    require_role(request, ["operator", "accountant"])
    idx = load_index()
    rec = idx.get("uploads", {}).get(month_key)
    if not rec or not rec.get("highlight_file"):
        raise HTTPException(status_code=404)
    path = Path(rec["highlight_file"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="فایل موجود نیست")
    return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _summarize_result(result: AuditResult) -> dict:
    """Build per-sheet summary for new audit result."""
    sheets_summary = []
    for s in result.sheets:
        sheets_summary.append({
            "name": s.name,
            "foreman": s.foreman,
            "list_no": s.list_no,
            "workplace": s.workplace,
            "period": s.period,
            "worker_rows": s.worker_rows,
            "worker_gross": f"{s.worker_gross:,.0f}" if s.worker_gross else "-",
            "desc_gross": f"{s.desc_gross:,.0f}" if s.desc_gross else "-",
            "error_count": len([i for i in s.issues if i.severity == "error"]),
            "warn_count": len([i for i in s.issues if i.severity == "warn"]),
        })
    return sheets_summary


@app.post("/api/upload")
async def api_upload(
    request: Request,
    file: UploadFile = File(...),
    month_key: str = Form(...),
    month_label: str = Form(""),
    replace: str = Form("false"),
):
    require_role(request, ["operator", "accountant"])
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="فقط فایل .xlsx مجاز است")

    month_key = month_key.strip()
    if not re.match(r"^\d{4}-\d{2}$", month_key):
        raise HTTPException(status_code=400, detail="فرمت ماه نامعتبر (مثلاً 1405-03)")

    do_replace = replace.lower() in ("1", "true", "yes")
    idx = load_index()
    uploads = idx.setdefault("uploads", {})
    existing = uploads.get(month_key)

    if existing and not do_replace:
        return JSONResponse(
            status_code=409,
            content={
                "duplicate": True,
                "message": "این ماه قبلاً ثبت شده است",
                "existing": {
                    "month_label": existing.get("month_label"),
                    "filename": existing.get("filename"),
                    "uploaded_at": existing.get("uploaded_at"),
                },
            },
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\u0600-\u06FF. ()-]+", "_", file.filename)
    local_name = f"{month_key}_{uuid.uuid4().hex[:8]}_{safe_name}"
    local_path = UPLOAD_DIR / local_name

    content = await file.read()
    local_path.write_bytes(content)

    # same-file check
    digest = file_sha256(local_path)
    for other_key, other in list(uploads.items()):
        if other_key != month_key and other.get("sha256") == digest and not do_replace:
            local_path.unlink(missing_ok=True)
            return JSONResponse(
                status_code=409,
                content={
                    "duplicate": True,
                    "message": "این فایل قبلاً برای ماه دیگری ثبت شده",
                    "existing": {
                        "month_key": other_key,
                        "month_label": other.get("month_label"),
                        "filename": other.get("filename"),
                    },
                },
            )

    highlight_path = UPLOAD_DIR / f"{month_key}_highlighted.xlsx"
    try:
        result = audit_workbook(local_path)
        write_highlighted_workbook(result, local_path, highlight_path)
        ingest_result(result)
    except Exception as e:
        local_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"خطا در حسابرسی: {e}") from e

    # Drive backup
    drive_id = None
    drive_error = None
    try:
        folder = ensure_drive_folder()
        if existing and existing.get("drive_file_id"):
            try:
                delete_file(existing["drive_file_id"], permanent=True)
            except Exception:
                pass
        up = upload_file(local_path, parent=folder, name=f"{month_label or month_key} - {safe_name}")
        drive_id = up.get("id")
    except Exception as e:
        drive_error = str(e)

    # Cleanup old files
    if existing and existing.get("local_path"):
        try:
            Path(existing["local_path"]).unlink(missing_ok=True)
        except OSError:
            pass
    old_hl = existing.get("highlight_file") if existing else None
    if old_hl and Path(old_hl).exists() and Path(old_hl) != highlight_path:
        try:
            Path(old_hl).unlink(missing_ok=True)
        except OSError:
            pass

    errors = [i for i in result.issues if i.severity == "error"]
    warns = [i for i in result.issues if i.severity == "warn"]

    record = {
        "month_label": month_label.strip() or month_key,
        "filename": safe_name,
        "sha256": digest,
        "uploaded_at": utc_now(),
        "local_path": str(local_path),
        "highlight_file": str(highlight_path),
        "drive_file_id": drive_id,
        "drive_error": drive_error,
        "error_count": len(errors),
        "warn_count": len(warns),
        "issues": [asdict(i) for i in result.issues],
        "audit_summary": {
            "sheet_count": len(result.sheets),
            "worker_rows": sum(s.worker_rows for s in result.sheets),
            "sheets": _summarize_result(result),
        },
    }
    uploads[month_key] = record
    save_index(idx)

    return {"ok": True, "error_count": len(errors), "warn_count": len(warns), "record": _public_record(record, month_key)}


@app.get("/api/reports/data")
def api_reports_data(request: Request):
    """Return structured report data + chart-friendly format for all default reports."""
    require_role(request, ["accountant"])
    data = load_ingested()
    from collections import defaultdict

    # ── 1. Foreman totals (سرکارگر) ──
    f_totals = defaultdict(float)
    f_months = defaultdict(lambda: defaultdict(float))
    # ── 2. Well totals (چاه) ──
    w_totals = defaultdict(float)
    # ── 3. Monthly totals ──
    m_totals = defaultdict(lambda: {"worker": 0.0, "desc": 0.0})
    # ── 4. Status (error vs clean) ──
    status_counts = {"clean": 0, "error": 0, "warn": 0}
    # ── 5. Sheet-level per month (for foreman×month chart) ──
    f_ts = defaultdict(dict)  # foreman -> {month_key: gross}

    all_months = set()

    for rec in data:
        month = _extract_month(rec)
        all_months.add(month)
        for s in rec.get("sheets", []):
            f = s.get("foreman") or "نامشخص"
            w = s.get("workplace") or "نامشخص"
            wg = s.get("worker_gross") or 0
            dg = s.get("desc_gross") or 0

            f_totals[f] += wg
            f_months[f][month] += wg
            w_totals[w] += dg
            m_totals[month]["worker"] += wg
            m_totals[month]["desc"] += dg
            f_ts[f][month] = f_ts[f].get(month, 0) + wg

            sc = s.get("error_count", 0)
            if sc > 0:
                status_counts["error"] += 1
            elif s.get("warn_count", 0) > 0:
                status_counts["warn"] += 1
            else:
                status_counts["clean"] += 1

    sorted_months = sorted(all_months)

    # Build chart-ready arrays
    def to_labels_items(d):
        items = sorted(d.items(), key=lambda x: -x[1])
        return {"labels": [x[0] for x in items], "values": [round(x[1]) for x in items]}

    # Foreman × Month matrix for stacked/grouped bar
    foreman_matrix = {}
    for fm, mdict in f_ts.items():
        foreman_matrix[fm] = {m: round(mdict.get(m, 0)) for m in sorted_months}

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
        "sheet_count": sum(len(rec.get("sheets", [])) for rec in data),
    }


def _extract_month(rec: dict) -> str:
    import re
    fname = rec.get("file", "")
    m = re.search(r'(\d{4}-\d{2})', fname)
    if m:
        return m.group(1)
    return fname[-9:].replace("_", " - ")


# ── Chat-based report generation ──

import json as _json

CHAT_HISTORY_PATH = DATA_DIR / "chat_history.json"


def _load_chat():
    if not CHAT_HISTORY_PATH.exists():
        return []
    return _json.loads(CHAT_HISTORY_PATH.read_text(encoding="utf-8"))


def _save_chat(msgs):
    CHAT_HISTORY_PATH.write_text(_json.dumps(msgs, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/reports/{report_type}")
def api_reports(report_type: str, request: Request):
    require_role(request, ["accountant"])
    data = load_ingested()
    if not data:
        return {"html": "<p>هنوز فایلی ingest نشده.</p>"}
    if report_type == "foreman":
        md = report_foreman(data)
    elif report_type == "well":
        md = report_well(data)
    else:
        raise HTTPException(status_code=400)
    html = "<div style='overflow:auto'>" + markdown_table_to_html(md) + "</div>"
    return {"html": html}


@app.post("/api/chat")
async def api_chat(body: dict, request: Request):
    """Chat endpoint: user asks for a custom report, we generate it."""
    require_role(request, ["accountant"])
    msg = body.get("message", "").strip()
    if not msg:
        return {"reply": "لطفاً درخواست خود را بنویسید. مثلاً: «هزینه هر سرکارگر به تفکیک ماه»"}

    data = load_ingested()
    if not data:
        return {"reply": "⚠️ هنوز هیچ فایلی آپلود نشده. اول یک ماه آپلود کنید."}

    # Collect all data for analysis
    from collections import defaultdict
    all_sheets = []
    for rec in data:
        for s in rec.get("sheets", []):
            s_copy = dict(s)
            s_copy["_month"] = _extract_month(rec)
            all_sheets.append(s_copy)

    # Simple NL-based routing
    reply_parts = []
    chart_html = ""
    msg_lower = msg.replace(" ", "")

    # Build numbers for reply
    foreman_totals = defaultdict(float)
    well_totals = defaultdict(float)
    month_worker = defaultdict(float)
    month_desc = defaultdict(float)
    fm = defaultdict(lambda: defaultdict(float))

    for s in all_sheets:
        f = s.get("foreman") or "نامشخص"
        w = s.get("workplace") or "نامشخص"
        m = s["_month"]
        wg = s.get("worker_gross") or 0
        dg = s.get("desc_gross") or 0
        foreman_totals[f] += wg
        well_totals[w] += dg
        month_worker[m] += wg
        month_desc[m] += dg
        fm[f][m] += wg

    sorted_months = sorted(month_worker.keys())

    # --- Route ---
    if any(x in msg_lower for x in ["سرکارگر", "هرکارگر", "پیمانکار"]):
        items = sorted(foreman_totals.items(), key=lambda x: -x[1])
        reply_parts.append("**📊 جمع دریافتی به تفکیک سرکارگر:**\n")
        for f, v in items:
            reply_parts.append(f"▫️ {f}: {v:,.0f} ریال")
        total = sum(v for _, v in items)
        reply_parts.append(f"\n**جمع کل:** {total:,.0f} ریال")

        # Bar chart
        labels = _json.dumps([x[0] for x in items], ensure_ascii=False)
        values = _json.dumps([round(x[1]) for x in items])
        chart_html = _bar_chart(labels, values, "سرکارگر", "ریال")

    elif any(x in msg_lower for x in ["چاه", "محل", "محدوده", "مزرعه"]):
        items = sorted(well_totals.items(), key=lambda x: -x[1])
        reply_parts.append("**📊 هزینه به تفکیک چاه / محدوده:**\n")
        for w, v in items:
            reply_parts.append(f"▫️ {w}: {v:,.0f} ریال")
        total = sum(v for _, v in items)
        reply_parts.append(f"\n**جمع کل:** {total:,.0f} ریال")

        labels = _json.dumps([x[0] for x in items[:10]], ensure_ascii=False)
        values = _json.dumps([round(x[1]) for x in items[:10]])
        chart_html = _bar_chart(labels, values, "محدوده", "ریال")

    elif any(x in msg_lower for x in ["ماهانه", "ماه", "روند", "زمان"]):
        reply_parts.append("**📈 روند ماهانه:**\n")
        for m in sorted_months:
            reply_parts.append(f"▫️ {m}: {month_worker[m]:,.0f} ریال (هزینه: {month_desc[m]:,.0f} ریال)")

        labels = _json.dumps(sorted_months, ensure_ascii=False)
        w_vals = _json.dumps([round(month_worker[m]) for m in sorted_months])
        d_vals = _json.dumps([round(month_desc[m]) for m in sorted_months])
        chart_html = _grouped_chart(labels, w_vals, d_vals, "دریافتی", "هزینه", "ماه")

    elif any(x in msg_lower for x in ["خلاصه", "وضعیت", "سلامت", "کیفیت"]):
        errs = sum(1 for s in all_sheets if s.get("error_count", 0) > 0)
        warns = sum(1 for s in all_sheets if s.get("warn_count", 0) > 0)
        clean = len(all_sheets) - errs - warns
        reply_parts.append("**📋 خلاصه وضعیت شیت‌ها:**\n")
        reply_parts.append(f"✅ بدون نقص: {clean}")
        reply_parts.append(f"⚠️ با هشدار: {warns}")
        reply_parts.append(f"❌ با خطا: {errs}")
        reply_parts.append(f"\nکل شیت‌ها: {len(all_sheets)}")

        labels = _json.dumps(["بدون نقص", "هشدار", "خطا"], ensure_ascii=False)
        values = _json.dumps([clean, warns, errs])
        chart_html = _pie_chart(labels, values, "وضعیت شیت‌ها")

    elif any(x in msg_lower for x in ["رتبه", "بالاترین", "گران", "پرهزینه"]):
        items = sorted(foreman_totals.items(), key=lambda x: -x[1])[:5]
        reply_parts.append("**🏆 ۵ سرکارگر بالاترین هزینه:**\n")
        for i, (f, v) in enumerate(items, 1):
            reply_parts.append(f"{i}. {f}: {v:,.0f} ریال")

        labels = _json.dumps([x[0] for x in items], ensure_ascii=False)
        values = _json.dumps([round(x[1]) for x in items])
        chart_html = _bar_chart(labels, values, "بالاترین هزینه", "ریال")

    elif any(x in msg_lower for x in ["ردیف", "لیست", "تعداد", "کارگر"]):
        total_workers = sum(s.get("worker_rows", 0) for s in all_sheets)
        total_lists = len(set(s.get("list_no") for s in all_sheets if s.get("list_no")))
        reply_parts.append("**📊 آمار کلی:**\n")
        reply_parts.append(f"👥 تعداد کل کارگران: {total_workers:,}")
        reply_parts.append(f"📋 تعداد لیست‌ها: {total_lists}")
        reply_parts.append(f"📄 تعداد شیت‌ها: {len(all_sheets)}")
        reply_parts.append(f"🗓️ تعداد ماه‌ها: {len(sorted_months)}")

    else:
        reply_parts.append(
            "🤖 من می‌تونم این گزارش‌ها رو براتون بسازم:\n\n"
            "▫️ **«هزینه هر سرکارگر»** — جدول + نمودار میله‌ای\n"
            "▫️ **«هزینه هر چاه»** — تفکیک محدوده\n"
            "▫️ **«روند ماهانه»** — دریافتی و هزینه ماه به ماه\n"
            "▫️ **«خلاصه وضعیت»** — کیفیت شیت‌ها (خطا/هشدار/سالم)\n"
            "▫️ **«۵ سرکارگر پرهزینه»** — رتبه‌بندی\n"
            "▫️ **«آمار کلی»** — کارگران، لیست‌ها، ماه‌ها\n\n"
            "هرکدام رو بنویسید، گزارش + نمودار تحویل می‌دم 📈"
        )

    reply = "\n".join(reply_parts)

    # Save to history
    history = _load_chat()
    history.append({"role": "user", "message": msg, "ts": utc_now()})
    history.append({"role": "assistant", "reply": reply, "chart": chart_html, "ts": utc_now()})
    if len(history) > 50:
        history = history[-50:]
    _save_chat(history)

    return {"reply": reply, "chart": chart_html}


@app.get("/api/chat/history")
def api_chat_history(request: Request):
    require_role(request, ["accountant"])
    return {"messages": _load_chat()}


def _bar_chart(labels, values, xlabel, ylabel):
    """Generate Chart.js bar chart HTML snippet."""
    return f"""<div style="max-width:600px;margin:1rem 0">
<canvas id="chart_{abs(hash(labels+values)) % 100000}"></canvas></div>
<script>
new Chart(document.getElementById('chart_{abs(hash(labels+values)) % 100000}'), {{
type:'bar',
data:{{labels:{labels},datasets:[{{label:'{xlabel}',data:{values},backgroundColor:'#3b82f6',borderRadius:6}}]}},
options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,title:{{display:true,text:'{ylabel}'}}}}}}}}
}});
</script>"""


def _pie_chart(labels, values, title):
    colors = '["#4ade80","#fbbf24","#f87171"]'
    return f"""<div style="max-width:400px;margin:1rem 0">
<canvas id="pie_{abs(hash(labels+values)) % 100000}"></canvas></div>
<script>
new Chart(document.getElementById('pie_{abs(hash(labels+values)) % 100000}'), {{
type:'doughnut',
data:{{labels:{labels},datasets:[{{data:{values},backgroundColor:{colors},borderWidth:0}}]}},
options:{{responsive:true,plugins:{{legend:{{position:'bottom'}},title:{{display:true,text:'{title}'}}}}}}
}});
</script>"""


def _grouped_chart(labels, vals1, vals2, label1, label2, xlabel):
    return f"""<div style="max-width:600px;margin:1rem 0">
<canvas id="grp_{abs(hash(labels+vals1)) % 100000}"></canvas></div>
<script>
new Chart(document.getElementById('grp_{abs(hash(labels+vals1)) % 100000}'), {{
type:'bar',
data:{{
labels:{labels},
datasets:[
{{label:'{label1}',data:{vals1},backgroundColor:'#3b82f6',borderRadius:6}},
{{label:'{label2}',data:{vals2},backgroundColor:'#10b981',borderRadius:6}}
]}},
options:{{responsive:true,scales:{{y:{{beginAtZero:true}}}},plugins:{{legend:{{position:'top'}}}}}}
}});
</script>"""


def markdown_table_to_html(md: str) -> str:
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


# ── Fertilizer helpers ──

FERTILIZER_UPLOAD_DIR = UPLOAD_DIR / "fertilizer"


def load_fertilizer_index() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not FERTILIZER_INDEX_PATH.exists():
        return {"uploads": {}}
    return json.loads(FERTILIZER_INDEX_PATH.read_text(encoding="utf-8"))


def save_fertilizer_index(idx: dict[str, Any]) -> None:
    FERTILIZER_INDEX_PATH.write_text(
        json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _fertilizer_public_record(rec: dict[str, Any], month_key: str) -> dict[str, Any]:
    out = dict(rec)
    out["month_key"] = month_key
    if rec.get("highlight_file"):
        out["highlight_url"] = f"/api/fertilizer/download/{month_key}/highlighted"
    issues = out.get("issues", [])
    grouped: dict[str, dict] = {}
    for i in issues:
        code = i.get("code", "OTHER")
        grouped.setdefault(code, {"code": code, "count": 0, "items": []})
        grouped[code]["count"] += 1
        grouped[code]["items"].append(i)
    out["issues_grouped"] = list(grouped.values())
    return out


# ── Fertilizer Endpoints ──


@app.post("/api/fertilizer/upload")
async def api_fertilizer_upload(
    request: Request,
    file: UploadFile = File(...),
    month_key: str = Form(...),
    month_label: str = Form(""),
    replace: str = Form("false"),
    crop: str = Form(""),
    season: str = Form(""),
):
    require_role(request, ["operator", "accountant"])
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="فقط فایل .xlsx مجاز است")

    month_key = month_key.strip()
    if not re.match(r"^\d{4}-\d{2}$", month_key):
        raise HTTPException(status_code=400, detail="فرمت ماه نامعتبر (مثلاً 1405-03)")

    do_replace = replace.lower() in ("1", "true", "yes")
    idx = load_fertilizer_index()
    uploads = idx.setdefault("uploads", {})
    existing = uploads.get(month_key)

    if existing and not do_replace:
        return JSONResponse(
            status_code=409,
            content={
                "duplicate": True,
                "message": "این ماه قبلاً ثبت شده است",
                "existing": {
                    "month_label": existing.get("month_label"),
                    "filename": existing.get("filename"),
                    "uploaded_at": existing.get("uploaded_at"),
                },
            },
        )

    FERTILIZER_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^\w\u0600-\u06FF. ()-]+", "_", file.filename)
    local_name = f"{month_key}_{uuid.uuid4().hex[:8]}_{safe_name}"
    local_path = FERTILIZER_UPLOAD_DIR / local_name

    content = await file.read()
    local_path.write_bytes(content)

    # same-file check
    digest = file_sha256(local_path)
    for other_key, other in list(uploads.items()):
        if other_key != month_key and other.get("sha256") == digest and not do_replace:
            local_path.unlink(missing_ok=True)
            return JSONResponse(
                status_code=409,
                content={
                    "duplicate": True,
                    "message": "این فایل قبلاً برای ماه دیگری ثبت شده",
                    "existing": {
                        "month_key": other_key,
                        "month_label": other.get("month_label"),
                        "filename": other.get("filename"),
                    },
                },
            )

    highlight_path = FERTILIZER_UPLOAD_DIR / f"{month_key}_highlighted.xlsx"
    try:
        result = fert_audit_workbook(local_path)
        fert_write_highlighted(result, local_path, highlight_path)
        fert_ingest_result(result)
    except Exception as e:
        local_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"خطا در حسابرسی: {e}") from e

    # Drive backup
    drive_id = None
    drive_error = None
    try:
        folder = ensure_drive_folder()
        if existing and existing.get("drive_file_id"):
            try:
                delete_file(existing["drive_file_id"], permanent=True)
            except Exception:
                pass
        up = upload_file(
            local_path,
            parent=folder,
            name=f"{month_label or month_key} - کود - {safe_name}",
        )
        drive_id = up.get("id")
    except Exception as e:
        drive_error = str(e)

    # Cleanup old files
    if existing and existing.get("local_path"):
        try:
            Path(existing["local_path"]).unlink(missing_ok=True)
        except OSError:
            pass
    old_hl = existing.get("highlight_file") if existing else None
    if old_hl and Path(old_hl).exists() and Path(old_hl) != highlight_path:
        try:
            Path(old_hl).unlink(missing_ok=True)
        except OSError:
            pass

    errors = [i for i in result.issues if i.severity == "error"]
    warns = [i for i in result.issues if i.severity == "warn"]

    record = {
        "month_label": month_label.strip() or month_key,
        "crop": crop.strip(),
        "season": season.strip(),
        "filename": safe_name,
        "sha256": digest,
        "uploaded_at": utc_now(),
        "local_path": str(local_path),
        "highlight_file": str(highlight_path),
        "drive_file_id": drive_id,
        "drive_error": drive_error,
        "error_count": len(errors),
        "warn_count": len(warns),
        "issues": [asdict(i) for i in result.issues],
        "row_count": len(result.rows),
        "fertilizer_count": len(result.fertilizers),
    }
    uploads[month_key] = record
    save_fertilizer_index(idx)

    return {
        "ok": True,
        "error_count": len(errors),
        "warn_count": len(warns),
        "row_count": len(result.rows),
        "fertilizer_count": len(result.fertilizers),
        "issues": [asdict(i) for i in result.issues],
        "highlight_url": f"/api/fertilizer/download/{month_key}/highlighted"
        if highlight_path.exists()
        else None,
        "drive_id": drive_id,
        "drive_error": drive_error,
    }


@app.get("/api/fertilizer/months")
def api_fertilizer_months(request: Request):
    require_role(request, ["operator", "accountant"])
    idx = load_fertilizer_index()
    items = []
    for key, rec in sorted(idx.get("uploads", {}).items(), reverse=True):
        errors = rec.get("error_count", 0)
        warns = rec.get("warn_count", 0)
        if errors > 0:
            status_label = "error"
            status_text = f"{errors} خطا"
        elif warns > 0:
            status_label = "warn"
            status_text = f"{warns} هشدار"
        else:
            status_label = "ok"
            status_text = "تأیید"
        items.append({
            "month_key": key,
            "month_label": rec.get("month_label", key),
            "filename": rec.get("filename"),
            "uploaded_at": rec.get("uploaded_at"),
            "error_count": errors,
            "warn_count": warns,
            "status_label": status_label,
            "status_text": status_text,
            "row_count": rec.get("row_count", 0),
            "fertilizer_count": rec.get("fertilizer_count", 0),
        })

    total_errors = sum(
        r.get("error_count", 0) for r in idx.get("uploads", {}).values()
    )
    total_warns = sum(
        r.get("warn_count", 0) for r in idx.get("uploads", {}).values()
    )
    total_rows = sum(
        r.get("row_count", 0) for r in idx.get("uploads", {}).values()
    )

    return {
        "items": items,
        "summary": {
            "month_count": len(items),
            "total_errors": total_errors,
            "total_warns": total_warns,
            "total_rows": total_rows,
        },
    }


@app.get("/api/fertilizer/months/{key}")
def api_fertilizer_month_detail(key: str, request: Request):
    require_role(request, ["operator", "accountant"])
    idx = load_fertilizer_index()
    rec = idx.get("uploads", {}).get(key)
    if not rec:
        raise HTTPException(status_code=404, detail="ماه یافت نشد")
    return _fertilizer_public_record(rec, key)


@app.get("/api/archive")
def api_archive(request: Request):
    require_role(request, ["operator", "accountant"])
    workforce_idx = load_index()
    fertilizer_idx = load_fertilizer_index()

    workforce_uploads = [
        dict(
            rec,
            month_key=key,
            type="workforce",
            module_label="صورت کارگری",
            label=rec.get("month_label", key),
        )
        for key, rec in workforce_idx.get("uploads", {}).items()
    ]
    fertilizer_uploads = [
        dict(
            rec,
            month_key=key,
            type="fertilizer",
            module_label="مصرف کود",
            label=f"{rec.get('crop','')} - {rec.get('season','') or rec.get('month_label', key)}",
        )
        for key, rec in fertilizer_idx.get("uploads", {}).items()
    ]

    merged = sorted(
        workforce_uploads + fertilizer_uploads,
        key=lambda x: x.get("uploaded_at", ""),
        reverse=True,
    )

    return {
        "items": merged,
        "summary": {
            "workforce_count": len(workforce_uploads),
            "fertilizer_count": len(fertilizer_uploads),
            "total": len(merged),
        },
    }


@app.get("/api/fertilizer/download/{key}/highlighted")
def api_fertilizer_download_highlight(key: str, request: Request):
    require_role(request, ["operator", "accountant"])
    idx = load_fertilizer_index()
    rec = idx.get("uploads", {}).get(key)
    if not rec or not rec.get("highlight_file"):
        raise HTTPException(status_code=404)
    path = Path(rec["highlight_file"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="فایل موجود نیست")
    return FileResponse(
        path,
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def main():
    import uvicorn
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
