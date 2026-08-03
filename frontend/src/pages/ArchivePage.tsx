// Archive — unified list of uploaded files with delete + details.

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { api } from '../api/client';
import type { ArchiveResponse } from '../api/types';
import { ACCOUNTANT_NAV } from '../lib/nav';
import { Trash, Clipboard, ArchFolder, ArchFertilizer } from '../ui/icons';

export function ArchivePage() {
  const [data, setData] = useState<ArchiveResponse | null>(null);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    api
      .get<ArchiveResponse>('/api/archive')
      .then(setData)
      .catch(() => setError('خطا در بارگذاری آرشیو'));
  }, []);

  return (
    <Layout title="آرشیو اطلاعات" navItems={ACCOUNTANT_NAV}>
      <div className="card">
        <h2><ArchFolder size={18} /> آرشیو اطلاعات</h2>
        {error && <div className="msg err">{error}</div>}
        {!data && !error && <div className="loading">در حال بارگذاری…</div>}
        {data && data.items.length === 0 && (
          <p style={{ color: 'var(--text-muted)' }}>هنوز فایلی ثبت نشده.</p>
        )}
        {data && data.items.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>نوع</th>
                <th>عنوان</th>
                <th>خطا</th>
                <th>هشدار</th>
                <th>تاریخ آپلود</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={`${r.type}-${r.month_key}`}>
                  <td>
                    {r.type === 'fertilizer' ? <ArchFertilizer size={18} /> : <Clipboard size={18} />} {r.module_label}
                  </td>
                  <td>{r.label}</td>
                  <td>
                    {r.error_count > 0 ? (
                      <span className="badge err">{r.error_count}</span>
                    ) : (
                      <span className="badge ok">۰</span>
                    )}
                  </td>
                  <td>
                    {r.warn_count > 0 ? (
                      <span className="badge warn">{r.warn_count}</span>
                    ) : (
                      <span className="badge ok">۰</span>
                    )}
                  </td>
                  <td>{new Date(r.uploaded_at).toLocaleString('fa-IR')}</td>
                  <td>
                    <button
                      className="secondary"
                      onClick={() =>
                        navigate(
                          r.type === 'fertilizer'
                            ? `/fertilizer?month=${encodeURIComponent(r.month_key)}`
                            : `/?month=${encodeURIComponent(r.month_key)}`,
                        )
                      }
                    >
                      جزئیات
                    </button>
                    
                    <button
                      className="danger"
                      onClick={async () => {
                        if (!confirm('آیا از حذف فایل «' + r.label + '» اطمینان دارید؟')) return;
                        try {
                          const url = r.type === 'fertilizer'
                            ? '/api/fertilizer/upload/' + encodeURIComponent(r.month_key)
                            : '/api/upload/' + encodeURIComponent(r.month_key);
                          await api.delete(url);
                          // Refresh list
                          const d: any = await api.get('/api/archive');
                          setData(d);
                        } catch (e: any) {
                          alert('خطا در حذف: ' + (e.message || 'unknown'));
                        }
                      }}
                    >
                      <Trash size={16} /> حذف
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Layout>
  );
}
