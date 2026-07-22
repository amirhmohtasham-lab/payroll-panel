"""Chat-based report assistant: simple NL routing over ingested payroll data.

Ported from the legacy app.py's /api/chat handler; persists history to the DB
(`chat_messages` table) instead of chat_history.json.
"""
from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.models.chat import ChatMessage
from app.models.upload import Upload, UploadType
from app.models.user import User

_MAX_HISTORY = 50


def _sheets_for_all_uploads(db: DbSession) -> list[dict[str, Any]]:
    uploads = list(
        db.execute(select(Upload).where(Upload.upload_type == UploadType.PAYROLL)).scalars()
    )
    all_sheets: list[dict[str, Any]] = []
    for u in uploads:
        for s in (u.audit_summary or {}).get("sheets", []):
            s_copy = dict(s)
            s_copy["_month"] = u.month_key
            all_sheets.append(s_copy)
    return all_sheets


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


def _bar_chart(labels: str, values: str, xlabel: str, ylabel: str) -> str:
    chart_id = abs(hash(labels + values)) % 100000
    return f"""<div style="max-width:600px;margin:1rem 0">
<canvas id="chart_{chart_id}"></canvas></div>
<script>
new Chart(document.getElementById('chart_{chart_id}'), {{
type:'bar',
data:{{labels:{labels},datasets:[{{label:'{xlabel}',data:{values},backgroundColor:'#3b82f6',borderRadius:6}}]}},
options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,title:{{display:true,text:'{ylabel}'}}}}}}}}
}});
</script>"""


def _pie_chart(labels: str, values: str, title: str) -> str:
    chart_id = abs(hash(labels + values)) % 100000
    colors = '["#4ade80","#fbbf24","#f87171"]'
    return f"""<div style="max-width:400px;margin:1rem 0">
<canvas id="pie_{chart_id}"></canvas></div>
<script>
new Chart(document.getElementById('pie_{chart_id}'), {{
type:'doughnut',
data:{{labels:{labels},datasets:[{{data:{values},backgroundColor:{colors},borderWidth:0}}]}},
options:{{responsive:true,plugins:{{legend:{{position:'bottom'}},title:{{display:true,text:'{title}'}}}}}}
}});
</script>"""


def _grouped_chart(labels: str, vals1: str, vals2: str, label1: str, label2: str, xlabel: str) -> str:
    chart_id = abs(hash(labels + vals1)) % 100000
    return f"""<div style="max-width:600px;margin:1rem 0">
<canvas id="grp_{chart_id}"></canvas></div>
<script>
new Chart(document.getElementById('grp_{chart_id}'), {{
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


def answer(db: DbSession, *, message: str, user: User) -> tuple[str, str]:
    msg = message.strip()
    if not msg:
        return "لطفاً درخواست خود را بنویسید. مثلاً: «هزینه هر سرکارگر به تفکیک ماه»", ""

    all_sheets = _sheets_for_all_uploads(db)
    if not all_sheets:
        return "⚠️ هنوز هیچ فایلی آپلود نشده. اول یک ماه آپلود کنید.", ""

    msg_lower = msg.replace(" ", "")

    foreman_totals: dict[str, float] = defaultdict(float)
    well_totals: dict[str, float] = defaultdict(float)
    month_worker: dict[str, float] = defaultdict(float)
    month_desc: dict[str, float] = defaultdict(float)

    for s in all_sheets:
        f = s.get("foreman") or "نامشخص"
        w = s.get("workplace") or "نامشخص"
        m = s["_month"]
        wg = _to_float(s.get("worker_gross"))
        dg = _to_float(s.get("desc_gross"))
        foreman_totals[f] += wg
        well_totals[w] += dg
        month_worker[m] += wg
        month_desc[m] += dg

    sorted_months = sorted(month_worker.keys())
    reply_parts: list[str] = []
    chart_html = ""

    if any(x in msg_lower for x in ["سرکارگر", "هرکارگر", "پیمانکار"]):
        items = sorted(foreman_totals.items(), key=lambda x: -x[1])
        reply_parts.append("**📊 جمع دریافتی به تفکیک سرکارگر:**\n")
        for f, v in items:
            reply_parts.append(f"▫️ {f}: {v:,.0f} ریال")
        total = sum(v for _, v in items)
        reply_parts.append(f"\n**جمع کل:** {total:,.0f} ریال")
        labels = json.dumps([x[0] for x in items], ensure_ascii=False)
        values = json.dumps([round(x[1]) for x in items])
        chart_html = _bar_chart(labels, values, "سرکارگر", "ریال")

    elif any(x in msg_lower for x in ["چاه", "محل", "محدوده", "مزرعه"]):
        items = sorted(well_totals.items(), key=lambda x: -x[1])
        reply_parts.append("**📊 هزینه به تفکیک چاه / محدوده:**\n")
        for w, v in items:
            reply_parts.append(f"▫️ {w}: {v:,.0f} ریال")
        total = sum(v for _, v in items)
        reply_parts.append(f"\n**جمع کل:** {total:,.0f} ریال")
        labels = json.dumps([x[0] for x in items[:10]], ensure_ascii=False)
        values = json.dumps([round(x[1]) for x in items[:10]])
        chart_html = _bar_chart(labels, values, "محدوده", "ریال")

    elif any(x in msg_lower for x in ["ماهانه", "ماه", "روند", "زمان"]):
        reply_parts.append("**📈 روند ماهانه:**\n")
        for m in sorted_months:
            reply_parts.append(
                f"▫️ {m}: {month_worker[m]:,.0f} ریال (هزینه: {month_desc[m]:,.0f} ریال)"
            )
        labels = json.dumps(sorted_months, ensure_ascii=False)
        w_vals = json.dumps([round(month_worker[m]) for m in sorted_months])
        d_vals = json.dumps([round(month_desc[m]) for m in sorted_months])
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
        labels = json.dumps(["بدون نقص", "هشدار", "خطا"], ensure_ascii=False)
        values = json.dumps([clean, warns, errs])
        chart_html = _pie_chart(labels, values, "وضعیت شیت‌ها")

    elif any(x in msg_lower for x in ["رتبه", "بالاترین", "گران", "پرهزینه"]):
        items = sorted(foreman_totals.items(), key=lambda x: -x[1])[:5]
        reply_parts.append("**🏆 ۵ سرکارگر بالاترین هزینه:**\n")
        for i, (f, v) in enumerate(items, 1):
            reply_parts.append(f"{i}. {f}: {v:,.0f} ریال")
        labels = json.dumps([x[0] for x in items], ensure_ascii=False)
        values = json.dumps([round(x[1]) for x in items])
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

    db.add(ChatMessage(role="user", message=msg, user_id=user.id))
    db.add(ChatMessage(role="assistant", reply=reply, chart_html=chart_html, user_id=user.id))
    db.commit()

    _trim_history(db)
    return reply, chart_html


def _trim_history(db: DbSession) -> None:
    count = db.execute(select(ChatMessage.id)).scalars().all()
    if len(count) <= _MAX_HISTORY:
        return
    excess = len(count) - _MAX_HISTORY
    oldest = db.execute(
        select(ChatMessage).order_by(ChatMessage.created_at.asc()).limit(excess)
    ).scalars()
    for row in oldest:
        db.delete(row)
    db.commit()


def history(db: DbSession) -> list[ChatMessage]:
    return list(db.execute(select(ChatMessage).order_by(ChatMessage.created_at.asc())).scalars())
