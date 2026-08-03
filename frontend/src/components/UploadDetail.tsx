// Upload result panel — shows audit issues after a file upload.

import type { UploadRecord } from '../api/types';
import { formatNumber } from '../lib/months';

export function UploadDetail({ record, kind }: { record: UploadRecord; kind: 'payroll' | 'fertilizer' }) {
  const icon = kind === 'payroll' ? '' : '';
  const sheets = record.audit_summary?.sheets ?? [];
  const issues = record.issues_grouped.flatMap((g) => g.items);

  return (
    <div className="card">
      <h3>
        {icon} {record.month_label}
      </h3>
      <p style={{ color: 'var(--text-muted)', fontSize: '.85rem' }}>
        {record.original_filename}
        {kind === 'fertilizer' && (record.crop || record.season)
          ? ` | ${record.crop ?? ''}${record.season ? ' — ' + record.season : ''}`
          : ''}{' '}
        — خطا: {record.error_count} / هشدار: {record.warn_count}
      </p>
      {record.highlight_url && (
        <p style={{ marginTop: '.5rem' }}>
          <a href={record.highlight_url}> دانلود اکسل هایلایت‌شده</a>
        </p>
      )}
      {record.drive_error && (
        <p className="msg warn" style={{ marginTop: '.5rem' }}>
           پشتیبان‌گیری Drive: {record.drive_error}
        </p>
      )}
      {sheets.length > 0 && (
        <table style={{ marginTop: '.75rem' }}>
          <thead>
            <tr>
              <th>شیت</th>
              <th>جمع کارگری</th>
              <th>جمع توضیحات</th>
              <th>وضعیت</th>
            </tr>
          </thead>
          <tbody>
            {sheets.map((s) => (
              <tr key={s.name}>
                <td>{s.name}</td>
                <td>{formatNumber(s.worker_gross)}</td>
                <td>{formatNumber(s.desc_gross)}</td>
                <td>
                  {s.error_count > 0 ? (
                    <span className="badge err">{s.error_count} خطا</span>
                  ) : s.warn_count > 0 ? (
                    <span className="badge warn">{s.warn_count} هشدار</span>
                  ) : (
                    <span className="badge ok">تأیید</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {issues.length > 0 ? (
        <>
          <h4 style={{ marginTop: '.75rem', fontWeight: 500, fontSize: '.9rem' }}>خطاها</h4>
          {issues.map((i, idx) => (
            <div
              key={idx}
              style={{
                padding: '.25rem 0',
                fontSize: '.82rem',
                borderBottom: '1px solid var(--border-subtle)',
              }}
            >
              <span className={`badge ${i.severity === 'error' ? 'err' : 'warn'}`}>{i.severity}</span>{' '}
              <b>{i.code}</b> — {i.sheet}: {i.message}
            </div>
          ))}
        </>
      ) : (
        <p style={{ color: 'var(--green)', marginTop: '.5rem' }}> بدون نقص</p>
      )}
    </div>
  );
}
