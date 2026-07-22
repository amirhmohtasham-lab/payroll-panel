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

const BAR_COLORS = ['#b88916', '#6f8b57', '#586b3f', '#d3aa45', '#6f4e37', '#879b68', '#9a7b2f', '#a66b4f', '#7e8f52', '#c59b3c'];

export function ReportsPage() {
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
    <Layout title="گزارش‌های پیش‌فرض" navItems={ACCOUNTANT_NAV}>
      <section className="page-intro reports-intro">
        <div>
          <span className="eyebrow">اتاق تصمیم‌گیری</span>
          <h2>گزارش را بر اساس پرسش خود انتخاب کنید</h2>
          <p>از هزینه‌های هر محدوده تا روند ماهانه، تصویر روشن‌تری از عملیات بسازید.</p>
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

      {!active && (
        <p style={{ color: 'var(--text-muted)', fontSize: '.85rem' }}>روی یک کارت کلیک کنید.</p>
      )}
      {loading && <div className="loading">در حال بارگذاری…</div>}

      {!loading && data && meta && (
        <div className="card">
          <h3 style={{ fontWeight: 500, marginBottom: '.5rem' }}>
            {meta.icon} {meta.title}
          </h3>
          <ReportBody reportKey={active as ReportKey} data={data} totalWorkers={totalWorkers} />
        </div>
      )}
    </Layout>
  );
}

function ReportBody({
  reportKey,
  data,
  totalWorkers,
}: {
  reportKey: ReportKey;
  data: ReportsDataResponse;
  totalWorkers: number;
}) {
  if (reportKey === 'foreman') {
    const ft = data.foreman_totals;
    return (
      <>
        <SimpleTable
          headers={['سرکارگر', 'جمع دریافتی']}
          rows={ft.labels.map((l, i) => [l, formatNumber(ft.values[i])])}
        />
        <div className="chart-wrapper">
          <Bar
            data={{
              labels: ft.labels,
              datasets: [{ label: 'ریال', data: ft.values, backgroundColor: '#b88916', borderRadius: 6 }],
            }}
            options={{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }}
          />
        </div>
      </>
    );
  }

  if (reportKey === 'well') {
    const wt = data.well_totals;
    const labels = wt.labels.slice(0, 10);
    const values = wt.values.slice(0, 10);
    return (
      <>
        <SimpleTable headers={['محدوده', 'هزینه']} rows={labels.map((l, i) => [l, formatNumber(values[i])])} />
        <div className="chart-wrapper" style={{ maxWidth: 400 }}>
          <Doughnut
            data={{ labels, datasets: [{ data: values, backgroundColor: BAR_COLORS, borderWidth: 0 }] }}
            options={{ responsive: true, plugins: { legend: { position: 'bottom' } } }}
          />
        </div>
      </>
    );
  }

  if (reportKey === 'monthly') {
    const mo = data.monthly;
    return (
      <>
        <SimpleTable
          headers={['ماه', 'دریافتی', 'هزینه']}
          rows={mo.labels.map((l, i) => [l, formatNumber(mo.worker[i]), formatNumber(mo.desc[i])])}
        />
        <div className="chart-wrapper">
          <Bar
            data={{
              labels: mo.labels,
              datasets: [
                { label: 'دریافتی', data: mo.worker, backgroundColor: '#b88916', borderRadius: 6 },
                { label: 'هزینه', data: mo.desc, backgroundColor: '#10b981', borderRadius: 6 },
              ],
            }}
            options={{ responsive: true, scales: { y: { beginAtZero: true } } }}
          />
        </div>
      </>
    );
  }

  if (reportKey === 'status') {
    const st = data.status;
    return (
      <>
        <SimpleTable
          headers={['وضعیت', 'تعداد']}
          rows={[
            ['✅ بدون نقص', String(st.clean)],
            ['⚠️ هشدار', String(st.warn)],
            ['❌ خطا', String(st.error)],
          ]}
        />
        <div className="chart-wrapper" style={{ maxWidth: 320 }}>
          <Doughnut
            data={{
              labels: ['بدون نقص', 'هشدار', 'خطا'],
              datasets: [{ data: [st.clean, st.warn, st.error], backgroundColor: ['#27a644', '#fbbf24', '#f87171'], borderWidth: 0 }],
            }}
            options={{ responsive: true, plugins: { legend: { position: 'bottom' } } }}
          />
        </div>
      </>
    );
  }

  if (reportKey === 'top5') {
    const ft = data.foreman_totals;
    const labels = ft.labels.slice(0, 5);
    const values = ft.values.slice(0, 5);
    return (
      <>
        <SimpleTable
          headers={['#', 'سرکارگر', 'جمع دریافتی']}
          rows={labels.map((l, i) => [String(i + 1), l, formatNumber(values[i])])}
        />
        <div className="chart-wrapper">
          <Bar
            data={{
              labels,
              datasets: [{ label: 'ریال', data: values, backgroundColor: BAR_COLORS, borderRadius: 6 }],
            }}
            options={{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }}
          />
        </div>
      </>
    );
  }

  return (
    <SimpleTable
      headers={['شاخص', 'مقدار']}
      rows={[
        ['🗓️ ماه‌ها', String(data.month_count)],
        ['📄 شیت‌ها', String(data.sheet_count)],
        ['👥 کارگران', formatNumber(totalWorkers)],
        ['📋 سرکارگران', String(data.foreman_totals.labels.length)],
      ]}
    />
  );
}

function SimpleTable({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <table>
      <thead>
        <tr>
          {headers.map((h) => (
            <th key={h}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i}>
            {row.map((c, j) => (
              <td key={j}>{c}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
