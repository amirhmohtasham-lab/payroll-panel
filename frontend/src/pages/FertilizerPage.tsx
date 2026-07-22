import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { UploadDetail } from '../components/UploadDetail';
import { DuplicateModal } from '../components/DuplicateModal';
import { api, ApiError } from '../api/client';
import type { DuplicateInfo, MonthListResponse, UploadRecord } from '../api/types';
import { monthOptions } from '../lib/months';
import { ACCOUNTANT_NAV } from '../lib/nav';

const MONTHS = monthOptions();

export function FertilizerPage() {
  const [months, setMonths] = useState<MonthListResponse | null>(null);
  const [record, setRecord] = useState<UploadRecord | null>(null);
  const [searchParams] = useSearchParams();

  async function loadMonths() {
    try {
      const d = await api.get<MonthListResponse>('/api/fertilizer/months');
      setMonths(d);
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    loadMonths();
  }, []);

  useEffect(() => {
    const monthParam = searchParams.get('month');
    if (monthParam) {
      api
        .get<UploadRecord>(`/api/fertilizer/months/${encodeURIComponent(monthParam)}`)
        .then(setRecord)
        .catch(() => {});
    }
  }, [searchParams]);

  return (
    <Layout title="🧪 مدیریت کود" navItems={ACCOUNTANT_NAV}>
      <div className="card">
        <h2>🧪 بارگذاری مصرف کود</h2>
        <UploadForm
          onUploaded={(rec) => {
            setRecord(rec);
            loadMonths();
          }}
        />
      </div>

      <div className="card">
        <h2>ماه‌های ثبت‌شده</h2>
        {!months && <div className="loading">در حال بارگذاری…</div>}
        {months && months.items.length === 0 && (
          <p style={{ color: 'var(--text-muted)' }}>هنوز فایلی ثبت نشده.</p>
        )}
        {months && months.items.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>ماه</th>
                <th>فایل</th>
                <th>وضعیت</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {months.items.map((m) => (
                <tr key={m.month_key}>
                  <td>{m.month_label}</td>
                  <td>{m.filename}</td>
                  <td>
                    <span className={`badge ${m.status_label}`}>{m.status_text}</span>
                  </td>
                  <td>
                    <button
                      className="secondary"
                      onClick={() =>
                        api
                          .get<UploadRecord>(`/api/fertilizer/months/${encodeURIComponent(m.month_key)}`)
                          .then(setRecord)
                      }
                    >
                      جزئیات
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {record && <UploadDetail record={record} kind="fertilizer" />}
    </Layout>
  );
}

function UploadForm({ onUploaded }: { onUploaded: (rec: UploadRecord) => void }) {
  const [monthKey, setMonthKey] = useState(MONTHS[0]?.value ?? '');
  const [monthLabel, setMonthLabel] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
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
      const res = await api.postForm<
        { ok: true; error_count: number; warn_count: number; record: UploadRecord } | DuplicateInfo
      >('/api/fertilizer/upload', form);
      if ('duplicate' in res) {
        setDuplicate(res);
        return;
      }
      setDuplicate(null);
      setMessage({
        ok: res.error_count === 0,
        text: `✅ ثبت شد. خطا: ${res.error_count} | هشدار: ${res.warn_count}`,
      });
      onUploaded(res.record);
    } catch (e) {
      setMessage({ ok: false, text: e instanceof ApiError ? e.message : 'خطا' });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <label>ماه (شمسی)</label>
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
