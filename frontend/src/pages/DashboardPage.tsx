import { useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { UploadDetail } from '../components/UploadDetail';
import { DuplicateModal } from '../components/DuplicateModal';
import { api, ApiError } from '../api/client';
import type {
  DuplicateInfo,
  MonthListResponse,
  UploadRecord,
  UploadResultResponse,
} from '../api/types';
import { CROPS, formatNumber, monthOptions } from '../lib/months';
import { ACCOUNTANT_NAV } from '../lib/nav';

const MONTHS = monthOptions();

export function DashboardPage() {
  const [summary, setSummary] = useState<MonthListResponse['summary'] | null>(null);
  const [uploadType, setUploadType] = useState<'payroll' | 'fertilizer'>('payroll');

  async function loadSummary() {
    try {
      const d = await api.get<MonthListResponse>('/api/months');
      setSummary(d.summary);
    } catch {
      // silent — dashboard cards are non-critical
    }
  }

  useEffect(() => {
    loadSummary();
  }, []);

  return (
    <Layout title="Upload Hub" navItems={ACCOUNTANT_NAV}>
      <section className="page-intro">
        <div>
          <span className="eyebrow">نبض مالی مزرعه</span>
          <h2>کار امروز را از همین‌جا شروع کنید</h2>
          <p>فایل‌های حقوق و مصرف کود را با یک بررسی دقیق وارد کنید.</p>
        </div>
        <span className="season-mark" aria-hidden="true">۱۴۰۵</span>
      </section>
      <div className="dash-cards">
        <DashCard value={summary?.month_count ?? 0} label="ماه ثبت‌شده" />
        <DashCard
          value={summary?.total_errors ?? 0}
          label="خطاهای فعال"
          color={summary && summary.total_errors > 0 ? 'var(--err)' : 'var(--green)'}
        />
        <DashCard value={summary?.total_warns ?? 0} label="هشدارها" color="var(--warn)" />
        <DashCard value={formatNumber(summary?.total_workers ?? 0)} label="کارگران" />
      </div>

      <div className="card">
        <h2>📤 Upload Hub</h2>
        <div className="type-selector">
          <button
            className={`type-pill${uploadType === 'payroll' ? ' active' : ''}`}
            onClick={() => setUploadType('payroll')}
          >
            <span className="icon">👷</span> صورت کارگری
          </button>
          <button
            className={`type-pill${uploadType === 'fertilizer' ? ' active' : ''}`}
            onClick={() => setUploadType('fertilizer')}
          >
            <span className="icon">🧪</span> مصرف کود
          </button>
        </div>
        {uploadType === 'payroll' ? (
          <PayrollUploadForm onUploaded={loadSummary} />
        ) : (
          <FertilizerUploadForm onUploaded={loadSummary} />
        )}
      </div>
    </Layout>
  );
}

function DashCard({
  value,
  label,
  color,
}: {
  value: string | number;
  label: string;
  color?: string;
}) {
  return (
    <div className="dash-card">
      <div className="value" style={color ? { color } : undefined}>
        {value}
      </div>
      <div className="label">{label}</div>
    </div>
  );
}

function PayrollUploadForm({ onUploaded }: { onUploaded: () => void }) {
  const [monthKey, setMonthKey] = useState(MONTHS[0]?.value ?? '');
  const [monthLabel, setMonthLabel] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [record, setRecord] = useState<UploadRecord | null>(null);
  const [duplicate, setDuplicate] = useState<DuplicateInfo | null>(null);

  const defaultLabel = MONTHS.find((m) => m.value === monthKey)?.label ?? monthKey;

  async function submit(replace: boolean) {
    if (!file) {
      setMessage({ ok: false, text: 'فایل را انتخاب کنید.' });
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('month_key', monthKey);
      form.append('month_label', monthLabel || defaultLabel);
      form.append('replace', replace ? 'true' : 'false');
      const res = await api.postForm<UploadResultResponse | DuplicateInfo>('/api/upload', form);
      if ('duplicate' in res) {
        setDuplicate(res);
        return;
      }
      setDuplicate(null);
      setMessage({
        ok: res.error_count === 0,
        text: `✅ ثبت شد. خطا: ${res.error_count} | هشدار: ${res.warn_count}`,
      });
      setRecord(res.record);
      onUploaded();
    } catch (e) {
      setMessage({ ok: false, text: e instanceof ApiError ? e.message : 'خطا' });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      
      <label style={{ marginTop: '.6rem' }}>ماه (شمسی)</label>
      <select value={monthKey} onChange={(e) => setMonthKey(e.target.value)}>
        {MONTHS.map((m) => (
          <option key={m.value} value={m.value}>
            {m.label}
          </option>
        ))}
      </select>
      <label style={{ marginTop: '.6rem' }}>برچسب نمایشی</label>
      <input
        placeholder={`مثلاً ${defaultLabel}`}
        value={monthLabel}
        onChange={(e) => setMonthLabel(e.target.value)}
      />
      <label style={{ marginTop: '.6rem' }}>فایل اکسل</label>
      <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <p style={{ marginTop: '.75rem' }}>
        <button className="primary" disabled={submitting} onClick={() => submit(false)}>
          🔍 بررسی و بارگذاری
        </button>
      </p>
      {message && <div className={`msg ${message.ok ? 'ok' : 'err'}`}>{message.text}</div>}
      {record && <UploadDetail record={record} kind="payroll" />}
      {duplicate && (
        <DuplicateModal
          info={duplicate}
          onConfirm={() => {
            setDuplicate(null);
            submit(true);
          }}
          onCancel={() => setDuplicate(null)}
        />
      )}
    </div>
  );
}

function FertilizerUploadForm({ onUploaded }: { onUploaded: () => void }) {
  const [crop, setCrop] = useState(CROPS[0]);
  const [season, setSeason] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [record, setRecord] = useState<UploadRecord | null>(null);
  const [duplicate, setDuplicate] = useState<DuplicateInfo | null>(null);

  const autoMonthKey = String(new Date().getFullYear() - 621) + "-" + String(Date.now() % 100).padStart(2, "0");

  async function submit(replace: boolean) {
    if (!file) {
      setMessage({ ok: false, text: 'فایل را انتخاب کنید.' });
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('month_key', autoMonthKey);
      form.append('month_label', '');
      form.append('crop', crop);
      form.append('season', season.trim());
      form.append('replace', replace ? 'true' : 'false');
      const res = await api.postForm<{ ok: true; error_count: number; warn_count: number; record: UploadRecord } | DuplicateInfo>(
        '/api/fertilizer/upload',
        form,
      );
      if ('duplicate' in res) {
        setDuplicate(res);
        return;
      }
      setDuplicate(null);
      setMessage({
        ok: res.error_count === 0,
        text: `✅ ثبت شد. خطا: ${res.error_count} | هشدار: ${res.warn_count}`,
      });
      setRecord(res.record);
      onUploaded();
    } catch (e) {
      setMessage({ ok: false, text: e instanceof ApiError ? e.message : 'خطا' });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <label>محصول</label>
      <select value={crop} onChange={(e) => setCrop(e.target.value)}>
        {CROPS.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <label style={{ marginTop: '.6rem' }}>فصل</label>
      <input value={season} onChange={(e) => setSeason(e.target.value)} placeholder="مثلاً بهار ۱۴۰۵" />
      
      <label style={{ marginTop: '.6rem' }}>فایل اکسل</label>
      <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <p style={{ marginTop: '.75rem' }}>
        <button className="primary" disabled={submitting} onClick={() => submit(false)}>
          🔍 بررسی و بارگذاری
        </button>
      </p>
      {message && <div className={`msg ${message.ok ? 'ok' : 'err'}`}>{message.text}</div>}
      {record && <UploadDetail record={record} kind="fertilizer" />}
      {duplicate && (
        <DuplicateModal
          info={duplicate}
          onConfirm={() => {
            setDuplicate(null);
            submit(true);
          }}
          onCancel={() => setDuplicate(null)}
        />
      )}
    </div>
  );
}
