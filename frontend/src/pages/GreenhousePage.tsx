// Greenhouse hydroponic climate analysis — frontend page (updated)
// - All setpoints configurable in the upload form
// - Charts per department (A-D) with department colors
// - Bar charts (Min/Avg/Max) per department on a selected date

import { useEffect, useMemo, useState } from 'react';
import { Layout } from '../components/Layout';
import { ACCOUNTANT_NAV } from '../lib/nav';
import '../lib/chartSetup';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  BarElement,
  Filler,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import {
  ArrowPath,
  Bolt,
  CalendarDays,
  ChartBar,
  Check,
  Search,
  Trash,
  Upload,
  XCircle,
  GhDownloadZip,
  GhLeaf,
  GhSettings,
} from '../ui/icons';

ChartJS.register(LineElement, PointElement, BarElement, Filler);

// ─── Constants (match Python DEPARTMENT_COLORS / STATISTIC_COLORS) ───
const DEPS = ['A', 'B', 'C', 'D'];
const DEPT_COLORS: Record<string, string> = { A: '#1f77b4', B: '#ff7f0e', C: '#2ca02c', D: '#d62728' };
const STAT_COLORS = { Min: '#2563eb', Avg: '#f59e0b', Max: '#dc2626' };

// ─── Types ───
interface RunSummary {
  id: string;
  temp_filename: string;
  humi_filename: string;
  row_count: number | null;
  metrics: Record<string, any> | null;
  uploaded_at: string;
}

interface RunDetail extends RunSummary {
  tables: Record<string, any[]> | null;
}

interface Row {
  [key: string]: any;
}

function fmt(n: any, digits = 1): string {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return '—';
  return Number(n).toLocaleString('fa-IR', { maximumFractionDigits: digits });
}

function isInRange(dateStr: string, from: string, to: string): boolean {
  if (!from && !to) return true;
  const d = String(dateStr).slice(0, 10);
  if (from && d < from) return false;
  if (to && d > to) return false;
  return true;
}

// ─── Small table ───
function DataTable({ rows, title }: { rows: Row[]; title?: string }) {
  if (!rows || rows.length === 0) return null;
  const cols = Object.keys(rows[0]);
  return (
    <div style={{ overflowX: 'auto', marginBottom: '1rem' }}>
      {title && <h4 style={{ margin: '.4rem 0 .35rem', fontSize: '.85rem' }}>{title}</h4>}
      <div style={{ maxHeight: 380, overflowY: 'auto' }}>
        <table>
          <thead>
            <tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                {cols.map((c) => <td key={c}>{fmt(r[c])}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Settings input helpers ───
function NumField({ label, value, onChange, step = 0.5, min }: {
  label: string; value: number; onChange: (v: number) => void; step?: number; min?: number;
}) {
  return (
    <div>
      <label>{label}</label>
      <input type="number" step={step} min={min} value={value} onChange={(e) => onChange(parseFloat(e.target.value) || 0)} />
    </div>
  );
}

export function GreenhousePage() {
  const [tempFile, setTempFile] = useState<File | null>(null);
  const [humiFile, setHumiFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  // analysis settings
  const [temperatureScale, setTemperatureScale] = useState(10);
  const [condensationMargin, setCondensationMargin] = useState(2);
  const [vpdLow, setVpdLow] = useState(0.8);
  const [vpdHigh, setVpdHigh] = useState(1.1);
  const [tempDayLow, setTempDayLow] = useState(20);
  const [tempDayHigh, setTempDayHigh] = useState(35);
  const [tempNightLow, setTempNightLow] = useState(14);
  const [tempNightHigh, setTempNightHigh] = useState(18);
  const [rhLow, setRhLow] = useState(40);
  const [rhHigh, setRhHigh] = useState(75);
  const [dayStart, setDayStart] = useState(7);
  const [dayEnd, setDayEnd] = useState(19);
  const [irrStart, setIrrStart] = useState(8.5);
  const [irrEnd, setIrrEnd] = useState(14.5);
  const [showSettings, setShowSettings] = useState(false);

  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // filters
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [dayFilter, setDayFilter] = useState('');
  const [selectedDepts, setSelectedDepts] = useState<string[]>(['A', 'B', 'C', 'D']);

  async function loadRuns() {
    try {
      const res = await fetch('/api/greenhouse/runs');
      if (!res.ok) throw new Error('خطا در دریافت لیست');
      const data = await res.json();
      setRuns(data.items || []);
    } catch (e: any) {
      setMessage({ ok: false, text: e.message || 'خطا در دریافت لیست تحلیل‌ها' });
    }
  }

  useEffect(() => { loadRuns(); }, []);

  async function loadDetail(id: string) {
    setSelectedId(id);
    setLoadingDetail(true);
    setDetail(null);
    try {
      const res = await fetch(`/api/greenhouse/runs/${id}`);
      if (!res.ok) throw new Error('خطا در دریافت نتایج');
      const data = await res.json();
      setDetail(data);
    } catch (e: any) {
      setMessage({ ok: false, text: e.message || 'خطا در دریافت نتایج' });
    } finally {
      setLoadingDetail(false);
    }
  }

  function toggleDept(d: string) {
    setSelectedDepts((prev) => prev.includes(d) ? prev.filter((x) => x !== d) : [...prev, d]);
  }

  async function handleAnalyze(e: React.FormEvent) {
    e.preventDefault();
    if (!tempFile || !humiFile) {
      setMessage({ ok: false, text: 'هر دو فایل دما و رطوبت را انتخاب کنید.' });
      return;
    }
    // validation mirrors backend
    if (vpdLow >= vpdHigh) { setMessage({ ok: false, text: 'VPD minimum باید کمتر از maximum باشد.' }); return; }
    if (tempDayLow >= tempDayHigh || tempNightLow >= tempNightHigh) { setMessage({ ok: false, text: 'هر حداقل دما باید کمتر از حداکثر باشد.' }); return; }
    if (rhLow >= rhHigh) { setMessage({ ok: false, text: 'RH minimum باید کمتر از RH maximum باشد.' }); return; }
    if (dayStart >= dayEnd || irrStart >= irrEnd) { setMessage({ ok: false, text: 'زمان شروع باید قبل از پایان باشد.' }); return; }

    setAnalyzing(true);
    setMessage(null);
    try {
      const fd = new FormData();
      fd.append('temperature', tempFile);
      fd.append('humidity', humiFile);
      fd.append('temperature_scale', String(temperatureScale));
      fd.append('condensation_margin', String(condensationMargin));
      fd.append('vpd_low', String(vpdLow));
      fd.append('vpd_high', String(vpdHigh));
      fd.append('temp_day_low', String(tempDayLow));
      fd.append('temp_day_high', String(tempDayHigh));
      fd.append('temp_night_low', String(tempNightLow));
      fd.append('temp_night_high', String(tempNightHigh));
      fd.append('rh_low', String(rhLow));
      fd.append('rh_high', String(rhHigh));
      fd.append('day_start', String(dayStart));
      fd.append('day_end', String(dayEnd));
      fd.append('irrigation_start', String(irrStart));
      fd.append('irrigation_end', String(irrEnd));
      const res = await fetch('/api/greenhouse/upload', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'خطا در تحلیل فایل‌ها');
      }
      setMessage({ ok: true, text: 'تحلیل با موفقیت انجام شد.' });
      setTempFile(null);
      setHumiFile(null);
      await loadRuns();
      if (data.id) await loadDetail(data.id);
    } catch (err: any) {
      setMessage({ ok: false, text: err.message || 'خطا در تحلیل فایل‌ها' });
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleDelete(id: string) {
    if (!window.confirm('حذف این تحلیل؟')) return;
    try {
      const res = await fetch(`/api/greenhouse/runs/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('خطا در حذف');
      if (selectedId === id) { setSelectedId(null); setDetail(null); }
      await loadRuns();
    } catch (e: any) {
      setMessage({ ok: false, text: (e as Error).message });
    }
  }

  const tables = detail?.tables || {};
  const metrics = detail?.metrics || null;

  // ─── Filtered data ───
  const filteredDaily = useMemo(() => {
    const rows = tables['daily_summary'] || [];
    return rows.filter((r: Row) =>
      isInRange(r.Date, dateFrom, dateTo) &&
      (!dayFilter || String(r.Date).slice(0, 10) === dayFilter) &&
      selectedDepts.includes(r.Dept)
    );
  }, [tables, dateFrom, dateTo, dayFilter, selectedDepts]);

  const filteredBreaches = useMemo(() => {
    const rows = tables['breaches'] || [];
    return rows.filter((r: Row) =>
      isInRange(r.Date, dateFrom, dateTo) && selectedDepts.includes(r.Dept)
    );
  }, [tables, dateFrom, dateTo, selectedDepts]);

  const filteredDayNightTemp = useMemo(() => {
    const rows = tables['daynight_temperature'] || [];
    return rows.filter((r: Row) =>
      isInRange(r.PeriodDate, dateFrom, dateTo) && selectedDepts.includes(r.Dept)
    );
  }, [tables, dateFrom, dateTo, selectedDepts]);

  const filteredDayNightHumi = useMemo(() => {
    const rows = tables['daynight_humidity'] || [];
    return rows.filter((r: Row) =>
      isInRange(r.PeriodDate, dateFrom, dateTo) && selectedDepts.includes(r.Dept)
    );
  }, [tables, dateFrom, dateTo, selectedDepts]);

  const filteredZones = useMemo(() => {
    const rows = tables['vpd_zones'] || [];
    return rows.filter((r: Row) =>
      isInRange(r.Date, dateFrom, dateTo) && selectedDepts.includes(r.Dept)
    );
  }, [tables, dateFrom, dateTo, selectedDepts]);

  // ─── Per-department chart builders ───
  // ── Per-department daily series (for the per-dept line charts) ──
  const tempSeries = useMemo(() => {
    const rows = (tables['daily_temperature'] || []) as Row[];
    const byDept: Record<string, Row[]> = {};
    for (const d of DEPS) byDept[d] = rows.filter((r) => r.Dept === d);
    return byDept;
  }, [tables]);

  const humiSeries = useMemo(() => {
    const rows = (tables['daily_humidity'] || []) as Row[];
    const byDept: Record<string, Row[]> = {};
    for (const d of DEPS) byDept[d] = rows.filter((r) => r.Dept === d);
    return byDept;
  }, [tables]);

  const vpdSeries = useMemo(() => {
    const rows = (tables['daily_summary'] || []) as Row[];
    const byDept: Record<string, Row[]> = {};
    for (const d of DEPS) byDept[d] = rows.filter((r) => r.Dept === d);
    return byDept;
  }, [tables]);

  const gdhSeries = useMemo(() => {
    const rows = (tables['daily_summary'] || []) as Row[];
    const byDept: Record<string, Row[]> = {};
    for (const d of DEPS) byDept[d] = rows.filter((r) => r.Dept === d);
    return byDept;
  }, [tables]);

  // Day/night bar data for a given date (or first available)
  const dayNightDate = dayFilter || (() => {
    const rows = (tables['daynight_temperature'] || []) as Row[];
    return rows.length ? String(rows[0].PeriodDate).slice(0, 10) : '';
  })();

  const dayNightTempBars = useMemo(() => {
    const rows = (tables['daynight_temperature'] || []) as Row[];
    const date = dayNightDate;
    const filtered = rows.filter((r) => String(r.PeriodDate).slice(0, 10) === date && selectedDepts.includes(r.Dept));
    const periods = Array.from(new Set(filtered.map((r) => String(r.Period))));
    const datasets = ['Min', 'Avg', 'Max'].map((stat) => ({
      label: stat,
      data: DEPS.map((d) => {
        const rec = filtered.find((r) => r.Dept === d && String(r.Period) === periods[0]);
        return rec ? Number(rec[stat]) || 0 : 0;
      }),
      backgroundColor: STAT_COLORS[stat as keyof typeof STAT_COLORS],
    }));
    return { labels: DEPS, datasets };
  }, [tables, dayNightDate, selectedDepts]);

  const dayNightHumiBars = useMemo(() => {
    const rows = (tables['daynight_humidity'] || []) as Row[];
    const date = dayNightDate;
    const filtered = rows.filter((r) => String(r.PeriodDate).slice(0, 10) === date && selectedDepts.includes(r.Dept));
    const datasets = ['Min', 'Avg', 'Max'].map((stat) => ({
      label: stat,
      data: DEPS.map((d) => {
        const rec = filtered.find((r) => r.Dept === d);
        return rec ? Number(rec[stat]) || 0 : 0;
      }),
      backgroundColor: STAT_COLORS[stat as keyof typeof STAT_COLORS],
    }));
    return { labels: DEPS, datasets };
  }, [tables, dayNightDate, selectedDepts]);

  const barOpts = (title: string, yLabel: string) => ({
    responsive: true,
    plugins: { legend: { position: 'bottom' as const }, title: { display: true, text: title } },
    scales: {
      y: { beginAtZero: false, title: { display: true, text: yLabel } },
      x: { title: { display: true, text: 'دپارتمان' } },
    },
  });

  const lineOpts = (title: string, yLabel: string) => ({
    responsive: true,
    plugins: { legend: { display: false }, title: { display: true, text: title } },
    scales: {
      y: { beginAtZero: false, title: { display: true, text: yLabel } },
      x: { title: { display: true, text: 'تاریخ' } },
    },
  });

  // dept pills row
  const deptPills = (
    <div style={{ display: 'flex', gap: '.4rem', flexWrap: 'wrap', marginBottom: '.75rem' }}>
      {DEPS.map((d) => (
        <button
          key={d}
          type="button"
          onClick={() => toggleDept(d)}
          style={{
            background: selectedDepts.includes(d) ? DEPT_COLORS[d] : 'transparent',
            color: selectedDepts.includes(d) ? '#fff' : 'var(--text-sec)',
            border: `1.5px solid ${DEPT_COLORS[d]}`,
            borderRadius: 'var(--radius-xs)',
            padding: '.3rem .85rem',
            fontSize: '.8rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'all .15s ease',
          }}
        >
          Dept {d}
        </button>
      ))}
      <button
        type="button"
        onClick={() => setSelectedDepts(selectedDepts.length === DEPS.length ? [] : [...DEPS])}
        style={{
          background: 'transparent',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-xs)',
          padding: '.3rem .85rem',
          fontSize: '.8rem',
          cursor: 'pointer',
        }}
      >
        {selectedDepts.length === DEPS.length ? 'عدم انتخاب' : 'انتخاب همه'}
      </button>
    </div>
  );

  // ─── Render ───
  return (
    <Layout title="گلخانه هیدروپونیک" navItems={ACCOUNTANT_NAV}>
      <section className="page-intro">
        <div>
          <span className="eyebrow">Greenhouse Climate Analysis</span>
          <h2>گلخانه هیدروپونیک — تحلیل اقلیم</h2>
          <p>آپلود خروجی‌های دما و رطوبت، تحلیل VPD، نقطه شبنم، GDH و هشدارهای Setpoint — تفکیک دپارتمان‌های A تا D</p>
        </div>
        <span className="season-mark" style={{ fontSize: '2.2rem' }}><GhLeaf size={40} /></span>
      </section>

      {/* ─── Upload ─── */}
      <div className="card">
        <h3><Upload size={16} /> آپلود داده‌های گلخانه</h3>
        <form onSubmit={handleAnalyze}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
            <div>
              <label>فایل دما (TEMP A1–D4)</label>
              <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setTempFile(e.target.files?.[0] || null)} />
            </div>
            <div>
              <label>فایل رطوبت (HUMI A1–D2)</label>
              <input type="file" accept=".csv,.xlsx,.xls" onChange={(e) => setHumiFile(e.target.files?.[0] || null)} />
            </div>
          </div>

          <button
            type="button"
            className="secondary"
            style={{ marginTop: '.8rem', display: 'inline-flex', alignItems: 'center', gap: '.35rem' }}
            onClick={() => setShowSettings(!showSettings)}
          >
            <GhSettings size={16} /> تنظیمات تحلیل {showSettings ? '— بستن' : '— باز کردن'}
          </button>

          {showSettings && (
            <div style={{ marginTop: '.9rem', padding: '1rem', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', background: 'rgba(5,93,67,.03)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '.75rem' }}>
                <NumField label="مقیاس دما (تقسیم بر)" value={temperatureScale} onChange={setTemperatureScale} step={0.5} min={0.1} />
                <NumField label="حاشیه تراکم (°C)" value={condensationMargin} onChange={setCondensationMargin} step={0.5} min={0} />
                <NumField label="VPD حداقل (kPa)" value={vpdLow} onChange={setVpdLow} step={0.1} min={0} />
                <NumField label="VPD حداکثر (kPa)" value={vpdHigh} onChange={setVpdHigh} step={0.1} min={0} />
              </div>
              <h4 style={{ margin: '.8rem 0 .3rem', fontSize: '.82rem', color: 'var(--text-sec)' }}>ست‌پوینت دما</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '.75rem' }}>
                <NumField label="روز حداقل (°C)" value={tempDayLow} onChange={setTempDayLow} step={0.5} />
                <NumField label="روز حداکثر (°C)" value={tempDayHigh} onChange={setTempDayHigh} step={0.5} />
                <NumField label="شب حداقل (°C)" value={tempNightLow} onChange={setTempNightLow} step={0.5} />
                <NumField label="شب حداکثر (°C)" value={tempNightHigh} onChange={setTempNightHigh} step={0.5} />
              </div>
              <h4 style={{ margin: '.8rem 0 .3rem', fontSize: '.82rem', color: 'var(--text-sec)' }}>رطوبت و زمان‌بندی</h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '.75rem' }}>
                <NumField label="RH حداقل (%)" value={rhLow} onChange={setRhLow} step={1} min={0} />
                <NumField label="RH حداکثر (%)" value={rhHigh} onChange={setRhHigh} step={1} min={0} />
                <NumField label="شروع روز (ساعت)" value={dayStart} onChange={setDayStart} step={0.5} min={0} />
                <NumField label="پایان روز (ساعت)" value={dayEnd} onChange={setDayEnd} step={0.5} min={0.5} />
                <NumField label="شروع آبیاری (ساعت)" value={irrStart} onChange={setIrrStart} step={0.5} min={0} />
                <NumField label="پایان آبیاری (ساعت)" value={irrEnd} onChange={setIrrEnd} step={0.5} min={0.5} />
              </div>
            </div>
          )}

          <div style={{ marginTop: '.9rem' }}>
            <button className="primary" type="submit" disabled={analyzing} style={{ width: '100%' }}>
              {analyzing ? <><ArrowPath size={16} /> در حال تحلیل…</> : <><Bolt size={16} /> اجرای تحلیل کامل</>}
            </button>
          </div>
        </form>
        {message && (
          <div className={`msg ${message.ok ? 'ok' : 'err'}`} style={{ marginTop: '.8rem' }}>
            {message.ok ? <Check size={16} /> : <XCircle size={16} />} {message.text}
          </div>
        )}
      </div>

      {/* ─── Runs list ─── */}
      <div className="card">
        <h3><ChartBar size={16} /> تحلیل‌های قبلی</h3>
        {runs.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '.84rem' }}>هنوز تحلیلی ثبت نشده است.</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '.5rem' }}>
            {runs.map((r) => (
              <div key={r.id} style={{
                display: 'flex', alignItems: 'center', gap: '.5rem',
                border: `1px solid ${selectedId === r.id ? 'var(--olive)' : 'var(--border)'}`,
                background: selectedId === r.id ? 'rgba(5,93,67,.06)' : 'transparent',
                borderRadius: 'var(--radius-xs)', padding: '.4rem .6rem', cursor: 'pointer',
              }} onClick={() => loadDetail(r.id)}>
                <CalendarDays size={16} />
                <span style={{ fontSize: '.78rem' }}>{new Date(r.uploaded_at).toLocaleDateString('fa-IR')}</span>
                <span style={{ fontSize: '.72rem', color: 'var(--text-muted)' }}>{r.row_count} روز</span>
                <button type="button" className="danger" style={{ padding: '.15rem .4rem', margin: 0 }} onClick={(e) => { e.stopPropagation(); handleDelete(r.id); }}>
                  <Trash size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ─── Results ─── */}
      {loadingDetail && <div className="loading">در حال بارگذاری نتایج…</div>}

      {detail && metrics && (
        <>
          <div className="dash-cards" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>
            <div className="dash-card"><div className="value">{fmt(metrics.days, 0)}</div><div className="label">روزهای تحلیل</div></div>
            <div className="dash-card"><div className="value">{fmt(metrics.departments, 0)}</div><div className="label">بخش‌ها (Dept)</div></div>
            <div className="dash-card"><div className="value">{fmt(metrics.temp_mean)} °C</div><div className="label">میانگین دما</div></div>
            <div className="dash-card"><div className="value">{fmt(metrics.vpd_mean, 2)} kPa</div><div className="label">میانگین VPD</div></div>
            <div className="dash-card"><div className="value">{fmt(metrics.rh_mean)} %</div><div className="label">میانگین رطوبت</div></div>
            <div className="dash-card"><div className="value">{fmt(metrics.gdh_total, 0)}</div><div className="label">مجموع GDH</div></div>
            <div className="dash-card"><div className="value">{fmt(metrics.condensation_days, 0)}</div><div className="label">روزهای ریسک تراکم</div></div>
          </div>

          <div style={{ marginBottom: '1rem', display: 'flex', gap: '.5rem', flexWrap: 'wrap' }}>
            <a className="primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '.4rem', textDecoration: 'none' }} href={`/api/greenhouse/runs/${detail.id}/download`}>
              <GhDownloadZip size={16} /> دانلود همه نتایج (ZIP)
            </a>
          </div>

          {/* Filters */}
          <div className="card">
            <h3><Search size={16} /> فیلتر نتایج</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '.75rem' }}>
              <div>
                <label>از تاریخ</label>
                <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
              </div>
              <div>
                <label>تا تاریخ</label>
                <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
              </div>
              <div>
                <label>انتخاب روز (نمودارهای میله‌ای)</label>
                <input type="date" value={dayFilter} onChange={(e) => setDayFilter(e.target.value)} />
              </div>
            </div>
            <div style={{ marginTop: '.7rem' }}>
              <label>نمایش دپارتمان‌ها</label>
              {deptPills}
            </div>
          </div>

          {/* ─── Per-department charts ─── */}
          <div className="card">
            <h3><ChartBar size={16} /> نمودارهای روزانه به تفکیک دپارتمان</h3>

            {DEPS.filter((d) => selectedDepts.includes(d)).map((d) => {
              const color = DEPT_COLORS[d];
              const tRows = (tempSeries[d] || []).filter((r) => isInRange(r.Day, dateFrom, dateTo));
              const hRows = (humiSeries[d] || []).filter((r) => isInRange(r.Day, dateFrom, dateTo));
              const vRows = (vpdSeries[d] || []).filter((r) => isInRange(r.Date, dateFrom, dateTo));
              const gRows = (gdhSeries[d] || []).filter((r) => isInRange(r.Date, dateFrom, dateTo));
              if (!tRows.length && !hRows.length && !vRows.length) return null;

              const shade = (opacity: number) => {
                const hex = color.replace('#', '');
                const r = parseInt(hex.slice(0, 2), 16), g = parseInt(hex.slice(2, 4), 16), b = parseInt(hex.slice(4, 6), 16);
                return `rgba(${r},${g},${b},${opacity})`;
              };

              const mkLine = (labels: string[], min: number[], avg: number[], max: number[]) => ({
                labels,
                datasets: [
                  { label: 'Min', data: min, borderColor: shade(0.5), backgroundColor: shade(0.5), tension: 0.3, pointRadius: 2, borderDash: [4, 3] },
                  { label: 'Avg', data: avg, borderColor: color, backgroundColor: color, tension: 0.3, pointRadius: 2 },
                  { label: 'Max', data: max, borderColor: shade(0.5), backgroundColor: shade(0.5), tension: 0.3, pointRadius: 2, borderDash: [4, 3] },
                ],
              });

              return (
                <div key={d} style={{
                  border: `1.5px solid ${shade(0.35)}`,
                  borderRadius: 'var(--radius-sm)',
                  padding: '1rem',
                  marginBottom: '1rem',
                  background: 'rgba(255,255,255,.5)',
                }}>
                  <h4 style={{ margin: '0 0 .6rem', color, fontWeight: 700, display: 'flex', alignItems: 'center', gap: '.4rem' }}>
                    <span style={{ width: 12, height: 12, borderRadius: 3, background: color, display: 'inline-block' }} />
                    Department {d}
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                    {tRows.length > 0 && (
                      <div>
                        <Line data={mkLine(tRows.map((r) => String(r.Day).slice(0, 10)), tRows.map((r) => r.Min), tRows.map((r) => r.Avg), tRows.map((r) => r.Max))} options={lineOpts(`دما — Dept ${d} (°C)`, 'دما (°C)')} />
                      </div>
                    )}
                    {hRows.length > 0 && (
                      <div>
                        <Line data={mkLine(hRows.map((r) => String(r.Day).slice(0, 10)), hRows.map((r) => r.Min), hRows.map((r) => r.Avg), hRows.map((r) => r.Max))} options={lineOpts(`رطوبت — Dept ${d} (%)`, 'رطوبت نسبی (%)')} />
                      </div>
                    )}
                    {vRows.length > 0 && (
                      <div>
                        <Line data={mkLine(vRows.map((r) => String(r.Date).slice(0, 10)), vRows.map((r) => r.VPD_min), vRows.map((r) => r.VPD_mean), vRows.map((r) => r.VPD_max))} options={lineOpts(`VPD — Dept ${d} (kPa)`, 'VPD (kPa)')} />
                      </div>
                    )}
                    {gRows.length > 0 && (
                      <div>
                        <Line data={{
                          labels: gRows.map((r) => String(r.Date).slice(0, 10)),
                          datasets: [{ label: 'GDH', data: gRows.map((r) => r.GDH_base10_sum), borderColor: color, backgroundColor: shade(0.25), tension: 0.3, fill: true, pointRadius: 2 }],
                        }} options={lineOpts(`GDH — Dept ${d}`, 'GDH (Heat Units)')} />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* ─── Day/Night bar charts (selected date) ─── */}
          {dayNightDate && (
            <div className="card">
              <h3><ChartBar size={16} /> آمار روز/شب — {dayNightDate} (Min / Avg / Max)</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
                <div>
                  <Bar data={dayNightTempBars} options={barOpts('دما روز/شب (°C) — Min/Avg/Max به تفکیک دپارتمان', 'دما (°C)')} />
                </div>
                <div>
                  <Bar data={dayNightHumiBars} options={barOpts('رطوبت روز/شب (%) — Min/Avg/Max به تفکیک دپارتمان', 'رطوبت نسبی (%)')} />
                </div>
              </div>
              <p style={{ fontSize: '.75rem', color: 'var(--text-muted)', marginTop: '.5rem' }}>
                تاریخ را از فیلتر «انتخاب روز» تغییر دهید. نمودار میله‌ای برای هر دپارتمان (A–D) در تاریخ انتخابی نمایش داده می‌شود.
              </p>
            </div>
          )}

          {/* ─── Tables ─── */}
          <div className="card">
            <h3>جدول‌های تحلیل</h3>
            <DataTable rows={filteredDaily} title="خلاصه روزانه اقلیم (دما / رطوبت / VPD / GDH / Setpoint)" />
            <DataTable rows={tables['daily_temperature']?.filter((r: Row) => selectedDepts.includes(r.Dept)) || []} title="آمار روزانه دما" />
            <DataTable rows={tables['daily_humidity']?.filter((r: Row) => selectedDepts.includes(r.Dept)) || []} title="آمار روزانه رطوبت" />
            <DataTable rows={filteredBreaches} title="تخطی‌های دما" />
            <DataTable rows={filteredZones} title="توزیع روزانه مناطق VPD" />
            <DataTable rows={filteredDayNightTemp} title="دما روز/شب" />
            <DataTable rows={filteredDayNightHumi} title="رطوبت روز/شب" />
          </div>
        </>
      )}
    </Layout>
  );
}
