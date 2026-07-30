import { useState } from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import '../lib/chartSetup';
import { Layout } from '../components/Layout';
import { api } from '../api/client';
import type { MonthListResponse, ReportsDataResponse } from '../api/types';
import { formatNumber } from '../lib/months';
import { ACCOUNTANT_NAV } from '../lib/nav';

const REPORTS = [
  { icon: '👷', title: 'سرکارگر', desc: 'جمع دریافتی هر سرکارگر', key: 'foreman' },
  { icon: '🌊', title: 'چاه/محدوده', desc: 'هزینه به تفکیک محل', key: 'well' },
  { icon: '📈', title: 'روند ماهانه', desc: 'دریافتی و هزینه ماه به ماه', key: 'monthly' },
  { icon: '📋', title: 'خلاصه وضعیت', desc: 'خطا/هشدار/سالم', key: 'status' },
  { icon: '🏆', title: '۵ پرهزینه', desc: 'بالاترین هزینه', key: 'top5' },
  { icon: '📊', title: 'آمار کلی', desc: 'کارگران، لیست‌ها', key: 'general' },
] as const;

type ReportKey = (typeof REPORTS)[number]['key'];
const BAR_COLORS = ['#d0a830','#055d43','#3f8a6d','#e0bd55','#004733','#a88418','#7aa68f','#c49a28','#2f6f56','#f0d27a'];

export function ReportsPage() {
  const [tab, setTab] = useState<'payroll' | 'fertilizer'>('payroll');
  return (
    <Layout title="گزارش‌ها" navItems={ACCOUNTANT_NAV}>
      <div className="type-selector" style={{ marginBottom: '1.5rem' }}>
        <button
          className={`type-pill${tab === 'payroll' ? ' active' : ''}`}
          onClick={() => setTab('payroll')}
        ><span className="icon">👷</span> صورت کارگری</button>
        <button
          className={`type-pill${tab === 'fertilizer' ? ' active' : ''}`}
          onClick={() => setTab('fertilizer')}
        ><span className="icon">🧪</span> مدیریت کود</button>
      </div>
      {tab === 'payroll' ? <PayrollReports /> : <FertilizerPivot />}
    </Layout>
  );
}

function PayrollReports() {
  const [active, setActive] = useState<ReportKey | null>(null);
  const [data, setData] = useState<ReportsDataResponse | null>(null);
  const [totalWorkers, setTotalWorkers] = useState(0);
  const [loading, setLoading] = useState(false);

  async function runReport(key: ReportKey) {
    setLoading(true);
    setActive(key);
    try {
      const d = await api.get<ReportsDataResponse>('/api/reports/data');
      setData(d);
      if (key === 'general') {
        const months = await api.get<MonthListResponse>('/api/months');
        setTotalWorkers(months.items.reduce((sum, r) => sum + (r.worker_rows || 0), 0));
      }
    } finally {
      setLoading(false);
    }
  }

  const meta = REPORTS.find((r) => r.key === active);

  return (
    <>
      <section className="page-intro reports-intro">
        <div>
          <span className="eyebrow">اتاق تصمیم‌گیری</span>
          <h2>گزارش صورت کارگری</h2>
          <p>از هزینه‌های هر محدوده تا روند ماهانه</p>
        </div>
        <span className="season-mark" aria-hidden="true">گزارش</span>
      </section>
      <div className="report-grid">
        {REPORTS.map((r) => (
          <div
            key={r.key}
            className={`report-tile${active === r.key ? ' active' : ''}`}
            onClick={() => runReport(r.key)}
          >
            <div style={{ fontSize: '1.4rem' }}>{r.icon}</div>
            <div style={{ fontWeight: 500, margin: '.3rem 0' }}>{r.title}</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '.78rem' }}>{r.desc}</div>
          </div>
        ))}
      </div>
      {!active && <p style={{ color: 'var(--text-muted)', fontSize: '.85rem' }}>روی یک کارت کلیک کنید.</p>}
      

{loading && <div className="loading">در حال بارگذاری…</div>}
      {!loading && data && meta && (
        <div className="card">
          <h3 style={{ fontWeight: 500, marginBottom: '.5rem' }}>{meta.icon} {meta.title}</h3>
          <ReportBody reportKey={active as ReportKey} data={data} totalWorkers={totalWorkers} />
        </div>
      )}
    </>
  );
}

// ─── Fertilizer PivotTable ──────────────────────────────────────────────────

// ─── Advanced Fertilizer PivotTable ──────────────────────────────────────────

// ─── Advanced Fertilizer PivotTable ──────────────────────────────────────────

function FertilizerPivot() {
  const [allData, setAllData] = useState<any[]>([]);
  const [columns, setColumns] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [rowField, setRowField] = useState('نام کود');
  const [colField, setColField] = useState('ماه');
  const [valField, setValField] = useState('مصرفی/وزنی');
  const [agg, setAgg] = useState<'sum' | 'avg' | 'count'>('sum');
  const [filterField, setFilterField] = useState('');
  const [filterValue, setFilterValue] = useState('');
  const [chartMode, setChartMode] = useState(false);
  const chartRef = useState<any>(null);

  // ── Shamsi date filter ──
  const dateCols = ['تاریخ توصیه', 'تاریخ اجرا'];
  const [dateFilterCol, setDateFilterCol] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  async function loadData() {
    setLoading(true);
    try {
      const res: any = await api.get('/api/fertilizer/reports/data');
      setColumns(res.columns);
      setAllData(res.rows);
    } catch (e: any) {
      alert('خطا در بارگذاری: ' + (e.message || 'نامشخص'));
    } finally {
      setLoading(false);
    }
  }

  useState(() => { loadData(); });

  // ── Shamsi date helpers ──
  function isValidShamsi(s: string): boolean {
    return /^\d{4}\/\d{2}\/\d{2}$/.test(s) || /^\d{4}-\d{2}-\d{2}$/.test(s);
  }
  function normalizeShamsi(s: string): string {
    return s.replace(/-/g, '/'); // 1405-01-19 → 1405/01/19
  }

  // ── Apply filters ──
  let filtered = allData;
  // Regular filter
  if (filterField && filterValue) {
    filtered = filtered.filter((r: any) => String(r[filterField] ?? '') === filterValue);
  }
  // Date range filter
  if (dateFilterCol) {
    filtered = filtered.filter((r: any) => {
      const val = String(r[dateFilterCol] ?? '').trim();
      if (!val || val === '-' || !isValidShamsi(val)) return true; // skip invalid
      const d = normalizeShamsi(val);
      if (dateFrom && d < normalizeShamsi(dateFrom)) return false;
      if (dateTo && d > normalizeShamsi(dateTo)) return false;
      return true;
    });
  }

  // ── Build pivot ──
  const rowSet = new Set<string>();
  const colSet = new Set<string>();
  const pivotMap: Record<string, Record<string, {value:number;date:string}[]>> = {};

  filtered.forEach((row: any) => {
    const rk = String(row[rowField] ?? '(بدون مقدار)');
    const ck = String(row[colField] ?? '(بدون مقدار)');
    rowSet.add(rk);
    colSet.add(ck);
    if (!pivotMap[rk]) pivotMap[rk] = {};
    if (!pivotMap[rk][ck]) pivotMap[rk][ck] = [];
    const v = parseFloat(row[valField]) || 0;
    const d = String(row['تاریخ اجرا'] || row['تاریخ توصیه'] || '');
    pivotMap[rk][ck].push({value: v, date: d});
  });

  const rowLabels = Array.from(rowSet);
  const colLabels = Array.from(colSet);

  function aggregate(vals: {value:number;date:string}[]): number {
    if (vals.length === 0) return 0;
    if (agg === 'count') return vals.length;
    if ((agg as string) === 'last') {
      // Sort by date descending, pick the latest
      const sorted = [...vals].sort((a, b) => b.date.localeCompare(a.date));
      return sorted[0].value;
    }
    const s = vals.reduce((a, b) => a + b.value, 0);
    if (agg === 'avg') return Math.round((s / vals.length) * 100) / 100;
    return Math.round(s * 100) / 100;
  }

  function rowTotal(rk: string): number {
    const cells = pivotMap[rk] || {};
    let total = 0;
    colLabels.forEach((ck) => { total += aggregate(cells[ck] || []); });
    return total;
  }

  function grandTotal(): number {
    let total = 0;
    rowLabels.forEach((rk) => { total += rowTotal(rk); });
    return total;
  }

  // ── Export CSV ──
  function exportExcel() {
    const header = [rowField, ...colLabels, 'جمع کل'].join(',');
    const rows = rowLabels.map(rk => {
      const vals = colLabels.map(ck => aggregate(pivotMap[rk]?.[ck] || []));
      return [rk, ...vals, rowTotal(rk)].join(',');
    });
    const footer = ['جمع کل', ...colLabels.map(ck => {
      let t = 0;
      rowLabels.forEach(rk => { t += aggregate(pivotMap[rk]?.[ck] || []); });
      return t;
    }), grandTotal()].join(',');
    const csv = [header, ...rows, footer].join('\n');
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pivot_report.csv';
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── Download chart as JPG ──
  function downloadChart() {
    const canvas = document.querySelector('.chart-wrapper canvas') as HTMLCanvasElement;
    if (!canvas) { alert('نموداری برای دانلود وجود ندارد.'); return; }
    const link = document.createElement('a');
    link.download = 'pivot_chart.jpg';
    link.href = canvas.toDataURL('image/jpeg', 0.95);
    link.click();
  }

  // ── Chart data ──
  const chartLabels = rowLabels;
  const chartDatasets = colLabels.map((ck, i) => ({
    label: ck,
    data: rowLabels.map(rk => aggregate(pivotMap[rk]?.[ck] || [])),
    backgroundColor: ['#d0a830','#055d43','#3f8a6d','#e0bd55','#004733','#a88418','#7aa68f','#c49a28','#2f6f56','#f0d27a'][i % 10],
    borderRadius: 4,
  }));

  const filterOptions = filterField
    ? Array.from(new Set(allData.map((r: any) => String(r[filterField] ?? '')))).sort()
    : [];

  const numericCols = columns.filter(c =>
    c.includes('قیمت') || c.includes('توصیه') || c.includes('مصرف') ||
    c.includes('موجودی') || c.includes('مازاد') || c.includes('تحقق') ||
    c.includes('فاصله') || c.includes('مساحت')
  );

  return (
    <>
            {/* ── Quick Reports ── */}
      <div className="quick-reports">
        <button onClick={() => { setRowField("شماره چاه"); setColField("نام کود"); setValField("مصرفی/وزنی"); setAgg("sum"); setFilterField(""); setFilterValue(""); setDateFilterCol(""); setDateFrom(""); setDateTo(""); setChartMode(false); }}>
          📍 مصرف به تفکیک چاه <span className="sub">وزنی</span>
        </button>
        <button onClick={() => { setRowField("شماره چاه"); setColField("نام کود"); setValField("مصرفی/ریالی"); setAgg("sum"); setFilterField(""); setFilterValue(""); setDateFilterCol(""); setDateFrom(""); setDateTo(""); setChartMode(false); }}>
          📍 مصرف به تفکیک چاه <span className="sub">ریالی</span>
        </button>
        <button onClick={() => { setRowField("ماه شمسی"); setColField("نام کود"); setValField("مصرفی/وزنی"); setAgg("sum"); setFilterField(""); setFilterValue(""); setDateFilterCol(""); setDateFrom(""); setDateTo(""); setChartMode(false); }}>
          📅 مصرف به تفکیک ماه <span className="sub">وزنی</span>
        </button>
        <button onClick={() => { setRowField("واریته (ترکیبی)"); setColField("نام کود"); setValField("مصرفی/وزنی"); setAgg("sum"); setFilterField(""); setFilterValue(""); setDateFilterCol(""); setDateFrom(""); setDateTo(""); setChartMode(false); }}>
          🌱 مصرف به تفکیک واریته <span className="sub">ترکیبی</span>
        </button>
                      <button onClick={() => { setRowField("مساحت (هکتار)"); setColField("نام کود"); setValField("مصرفی/وزنی"); setAgg("sum"); setFilterField("شماره چاه"); setFilterValue("2"); setDateFilterCol(""); setDateFrom(""); setDateTo(""); setChartMode(false); }}>
          🌾 مصرف کود در هر قطعه هر چاه <span className="sub">وزنی</span>
        </button>
</div>

<section className="page-intro reports-intro">
        <div>
          <span className="eyebrow">تحلیل مصرف کود</span>
          <h2>PivotTable پیشرفته</h2>
          <p>بر اساس شیت Cleaned Data — با فیلتر تاریخ شمسی و دانلود نمودار</p>
        </div>
        <span className="season-mark" aria-hidden="true">کود</span>
      </section>

      {loading && <div className="loading">در حال بارگذاری…</div>}

      {!loading && (
        <>
          <div className="card">
            <h3>⚙ تنظیمات PivotTable</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label>📌 ردیف</label>
                <select value={rowField} onChange={(e) => setRowField(e.target.value)}>
                  {columns.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label>📌 ستون</label>
                <select value={colField} onChange={(e) => setColField(e.target.value)}>
                  {columns.filter(c => c !== rowField).map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label>🔢 مقدار</label>
                <select value={valField} onChange={(e) => setValField(e.target.value)}>
                  {numericCols.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              <div>
                <label>⚡ عملیات</label>
                <select value={agg} onChange={(e) => setAgg(e.target.value as any)}>
                  <option value="sum">🗂 جمع (Sum)</option>
                  <option value="avg">📊 میانگین (Average)</option>
                  <option value="count">🔢 تعداد (Count)</option>
                  <option value="last">📌 آخرین مقدار (Last)</option>
                </select>
              </div>
              <div>
                <label>🔍 فیلتر</label>
                <select value={filterField} onChange={(e) => { setFilterField(e.target.value); setFilterValue(''); }}>
                  <option value="">— بدون فیلتر —</option>
                  {columns.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              {filterField && (
                <div>
                  <label>مقدار فیلتر</label>
                  <select value={filterValue} onChange={(e) => setFilterValue(e.target.value)}>
                    <option value="">— همه —</option>
                    {filterOptions.map((v) => <option key={v} value={v}>{v}</option>)}
                  </select>
                </div>
              )}
              <div>
                <label>📅 فیلتر تاریخ شمسی</label>
                <select value={dateFilterCol} onChange={(e) => { setDateFilterCol(e.target.value); setDateFrom(''); setDateTo(''); }}>
                  <option value="">— بدون فیلتر تاریخ —</option>
                  {dateCols.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
              {dateFilterCol && (
                <div style={{ display: 'flex', gap: '.5rem', alignItems: 'end' }}>
                  <div>
                    <label>از تاریخ (مثال: 1405/01/01)</label>
                    <input placeholder="1405/01/01" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
                  </div>
                  <div>
                    <label>تا تاریخ (مثال: 1405/06/31)</label>
                    <input placeholder="1405/06/31" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
                  </div>
                </div>
              )}
            </div>
            <div style={{ marginTop: '.75rem' }}>
              <button className="secondary" onClick={loadData}>🔄 بروزرسانی</button>
            </div>
          </div>

          {allData.length === 0 && (
            <div className="card"><p style={{ color: 'var(--text-muted)' }}>داده‌ای موجود نیست. ابتدا فایل مصرف کود آپلود کنید.</p></div>
          )}

          {allData.length > 0 && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '.5rem', flexWrap: 'wrap', gap: '.5rem' }}>
                <h3 style={{ margin: 0 }}>
                  📊 PivotTable <span style={{ fontSize: '.8rem', color: 'var(--text-muted)' }}>
                    ({rowLabels.length} ردیف × {colLabels.length} ستون)
                  </span>
                </h3>
                <div style={{ display: 'flex', gap: '.35rem' }}>
                  <button className="secondary" onClick={() => setChartMode(!chartMode)} style={{ padding: '.35rem .6rem', fontSize: '.82rem' }}>
                    {chartMode ? '📋 جدول' : '📈 نمودار'}
                  </button>
                  {chartMode && (
                    <button className="secondary" onClick={downloadChart} style={{ padding: '.35rem .6rem', fontSize: '.82rem' }}>
                      🖼 دانلود JPG
                    </button>
                  )}
                  <button className="secondary" onClick={exportExcel} style={{ padding: '.35rem .6rem', fontSize: '.82rem' }}>
                    📥 خروجی CSV
                  </button>
                </div>
              </div>

              {chartMode ? (
                <div className="chart-wrapper">
                  <Bar
                    ref={(ref: any) => { if (ref) chartRef[1](ref); }}
                    data={{ labels: chartLabels, datasets: chartDatasets }}
                    options={{
                      responsive: true,
                      plugins: { legend: { position: 'bottom' } },
                      scales: { y: { beginAtZero: true } },
                    }}
                  />
                </div>
              ) : (
                <div style={{ overflowX: 'auto', maxHeight: '500px', overflowY: 'auto' }}>
                  <table style={{ fontSize: '.8rem' }}>
                    <thead>
                      <tr>
                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2 }}>{rowField}</th>
                        {colLabels.map((ck) => (
                          <th key={ck} style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2 }}>{ck}</th>
                        ))}
                        <th style={{ position: 'sticky', top: 0, background: 'var(--bg-card)', zIndex: 2 }}>جمع کل</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rowLabels.map((rk) => (
                        <tr key={rk}>
                          <td style={{ fontWeight: 500 }}>{rk}</td>
                          {colLabels.map((ck) => (
                            <td key={ck} style={{ textAlign: 'left', direction: 'ltr' }}>
                              {agg === 'count' ? aggregate(pivotMap[rk]?.[ck] || []) : aggregate(pivotMap[rk]?.[ck] || []).toLocaleString()}
                            </td>
                          ))}
                          <td style={{ fontWeight: 600, textAlign: 'left', direction: 'ltr' }}>
                            {agg === 'count' ? rowTotal(rk) : rowTotal(rk).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr style={{ fontWeight: 700, background: 'var(--bg-subtle)' }}>
                        <td>جمع کل</td>
                        {colLabels.map((ck) => {
                          let t = 0;
                          rowLabels.forEach(rk => { t += aggregate(pivotMap[rk]?.[ck] || []); });
                          return <td key={ck} style={{ textAlign: 'left', direction: 'ltr' }}>{agg === 'count' ? t : t.toLocaleString()}</td>;
                        })}
                        <td style={{ textAlign: 'left', direction: 'ltr' }}>{agg === 'count' ? grandTotal() : grandTotal().toLocaleString()}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </>
  );
}

function ReportBody({ reportKey, data, totalWorkers }: { reportKey: ReportKey; data: ReportsDataResponse; totalWorkers: number }) {
  if (reportKey === 'foreman') {
    const ft = data.foreman_totals;
    return (<><SimpleTable headers={['سرکارگر','جمع دریافتی']} rows={ft.labels.map((l,i)=>[l,formatNumber(ft.values[i])])} /><div className="chart-wrapper"><Bar data={{labels:ft.labels,datasets:[{label:'ریال',data:ft.values,backgroundColor:'#d0a830',borderRadius:6}]}} options={{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true}}}}/></div></>);
  }
  if (reportKey === 'well') {
    const wt = data.well_totals;
    const labels = wt.labels.slice(0,10);
    const values = wt.values.slice(0,10);
    return (<><SimpleTable headers={['محدوده','هزینه']} rows={labels.map((l,i)=>[l,formatNumber(values[i])])} /><div className="chart-wrapper" style={{maxWidth:400}}><Doughnut data={{labels,datasets:[{data:values,backgroundColor:BAR_COLORS,borderWidth:0}]}} options={{responsive:true,plugins:{legend:{position:'bottom'}}}}/></div></>);
  }
  if (reportKey === 'monthly') {
    const mo = data.monthly;
    return (<><SimpleTable headers={['ماه','دریافتی','هزینه']} rows={mo.labels.map((l,i)=>[l,formatNumber(mo.worker[i]),formatNumber(mo.desc[i])])} /><div className="chart-wrapper"><Bar data={{labels:mo.labels,datasets:[{label:'دریافتی',data:mo.worker,backgroundColor:'#d0a830',borderRadius:6},{label:'هزینه',data:mo.desc,backgroundColor:'#055d43',borderRadius:6}]}} options={{responsive:true,scales:{y:{beginAtZero:true}}}}/></div></>);
  }
  if (reportKey === 'status') {
    const st = data.status;
    return (<><SimpleTable headers={['وضعیت','تعداد']} rows={[['✅ بدون نقص',String(st.clean)],['⚠️ هشدار',String(st.warn)],['❌ خطا',String(st.error)]]} /><div className="chart-wrapper" style={{maxWidth:320}}><Doughnut data={{labels:['بدون نقص','هشدار','خطا'],datasets:[{data:[st.clean,st.warn,st.error],backgroundColor:['#055d43','#d0a830','#b54637'],borderWidth:0}]}} options={{responsive:true,plugins:{legend:{position:'bottom'}}}}/></div></>);
  }
  if (reportKey === 'top5') {
    const ft = data.foreman_totals;
    const labels = ft.labels.slice(0,5);
    const values = ft.values.slice(0,5);
    return (<><SimpleTable headers={['#','سرکارگر','جمع دریافتی']} rows={labels.map((l,i)=>[String(i+1),l,formatNumber(values[i])])} /><div className="chart-wrapper"><Bar data={{labels,datasets:[{label:'ریال',data:values,backgroundColor:BAR_COLORS,borderRadius:6}]}} options={{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true}}}}/></div></>);
  }
  if (reportKey === 'general') {
    const st = data.status;
    const mo = data.monthly;
    return (<SimpleTable headers={['آمار','مقدار']} rows={[['ماه‌های ثبت‌شده',String(mo.labels.length)],['مجموع کارگران',formatNumber(totalWorkers)],['فایل‌های بدون نقص',String(st.clean)],['فایل‌های خطا',String(st.error)],['فایل‌های هشدار',String(st.warn)]]} />);
  }
  return null;
}

function SimpleTable({ headers, rows }: { headers: string[]; rows: (string | number)[][] }) {
  return (
    <div style={{ overflowX: 'auto', marginBottom: '1rem' }}>
      <table>
        <thead><tr>{headers.map((h,i)=><th key={i}>{h}</th>)}</tr></thead>
        <tbody>{rows.map((row,i)=><tr key={i}>{row.map((v,j)=><td key={j}>{v}</td>)}</tr>)}</tbody>
      </table>
    </div>
  );
}
