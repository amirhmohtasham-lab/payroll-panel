// Operator panel — simplified upload entry for the operator role.

import { useState } from 'react';
import { Layout } from '../components/Layout';
import { UploadDetail } from '../components/UploadDetail';
import { DuplicateModal } from '../components/DuplicateModal';
import { api, ApiError } from '../api/client';
import type { DuplicateInfo, UploadRecord, UploadResultResponse } from '../api/types';
import { CROPS, monthOptions } from '../lib/months';
import { Upload, User, Beaker, Search } from '../ui/icons';

const NAV = [{ to: '/operator', icon: 'upload', label: 'بارگذاری' }];
const MONTHS = monthOptions();

export function OperatorPage() {
  const [activeType, setActiveType] = useState<'payroll' | 'fertilizer'>('payroll');

  return (
    <Layout title="پنل اپراتور" navItems={NAV}>
      <div className="card">
        <h2><Upload size={18} /> Upload Hub — مرکز بارگذاری</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '.85rem', marginBottom: '.75rem' }}>
          نوع فایل مورد نظر را انتخاب کنید.
        </p>
        <div className="type-selector">
          <button
            className={`type-pill${activeType === 'payroll' ? ' active' : ''}`}
            onClick={() => setActiveType('payroll')}
          >
            <span className="icon"><User size={18} /></span> صورت کارگری
          </button>
          <button
            className={`type-pill${activeType === 'fertilizer' ? ' active' : ''}`}
            onClick={() => setActiveType('fertilizer')}
          >
            <span className="icon"><Beaker size={18} /></span> مصرف کود
          </button>
        </div>
        {activeType === 'payroll' ? <PayrollUploadForm /> : <FertilizerUploadForm />}
      </div>
    </Layout>
  );
}

function PayrollUploadForm() {
  const [monthKey, setMonthKey] = useState(MONTHS[0]?.value ?? '');
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [record, setRecord] = useState<UploadRecord | null>(null);
  const [duplicate, setDuplicate] = useState<DuplicateInfo | null>(null);

  const monthLabel = MONTHS.find((m) => m.value === monthKey)?.label ?? monthKey;

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
      form.append('month_label', monthLabel);
      form.append('replace', replace ? 'true' : 'false');
      const res = await api.postForm<UploadResultResponse | DuplicateInfo>('/api/upload', form);
      if ('duplicate' in res) {
        setDuplicate(res);
        return;
      }
      setDuplicate(null);
      setMessage({
        ok: res.error_count === 0,
        text: `ثبت شد. خطا: ${res.error_count} | هشدار: ${res.warn_count}`,
      });
      setRecord(res.record);
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
      <label style={{ marginTop: '.5rem' }}>فایل اکسل</label>
      <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <p style={{ marginTop: '.75rem' }}>
        <button className="primary" disabled={submitting} onClick={() => submit(false)}>
          <Search size={16} /> بررسی و بارگذاری
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

function FertilizerUploadForm() {
  const [monthKey, setMonthKey] = useState(MONTHS[0]?.value ?? '');
  const [crop, setCrop] = useState(CROPS[0]);
  const [season, setSeason] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [record, setRecord] = useState<UploadRecord | null>(null);
  const [duplicate, setDuplicate] = useState<DuplicateInfo | null>(null);

  const monthLabel = MONTHS.find((m) => m.value === monthKey)?.label ?? monthKey;

  async function submit(replace: boolean) {
    if (!file) {
      setMessage({ ok: false, text: 'فایل را انتخاب کنید.' });
      return;
    }
    if (!season.trim()) {
      setMessage({ ok: false, text: 'فصل را وارد کنید.' });
      return;
    }
    setSubmitting(true);
    setMessage(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('month_key', monthKey);
      form.append('month_label', monthLabel);
      form.append('crop', crop);
      form.append('season', season.trim());
      form.append('replace', replace ? 'true' : 'false');
      const res = await api.postForm<
        | (UploadResultResponse & { row_count: number; fertilizer_count: number })
        | DuplicateInfo
      >('/api/fertilizer/upload', form);
      if ('duplicate' in res) {
        setDuplicate(res);
        return;
      }
      setDuplicate(null);
      setMessage({
        ok: res.error_count === 0,
        text: `ثبت شد. خطا: ${res.error_count} | هشدار: ${res.warn_count}`,
      });
      setRecord(res.record);
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
      <label style={{ marginTop: '.5rem' }}>محصول</label>
      <select value={crop} onChange={(e) => setCrop(e.target.value)}>
        {CROPS.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <label style={{ marginTop: '.5rem' }}>فصل</label>
      <input
        placeholder="مثال: بهار ۱۴۰۵"
        value={season}
        onChange={(e) => setSeason(e.target.value)}
      />
      <label style={{ marginTop: '.5rem' }}>فایل اکسل</label>
      <input type="file" accept=".xlsx" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <p style={{ marginTop: '.75rem' }}>
        <button className="primary" disabled={submitting} onClick={() => submit(false)}>
          <Search size={16} /> بررسی و بارگذاری
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
