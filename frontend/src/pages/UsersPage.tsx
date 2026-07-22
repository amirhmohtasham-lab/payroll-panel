import { type FormEvent, useEffect, useState } from 'react';
import { Layout } from '../components/Layout';
import { api, ApiError } from '../api/client';
import type { UserOut, UserRole } from '../api/types';
import { ACCOUNTANT_NAV } from '../lib/nav';

export function UsersPage() {
  const [users, setUsers] = useState<UserOut[] | null>(null);
  const [error, setError] = useState('');

  async function load() {
    try {
      const d = await api.get<UserOut[]>('/api/users');
      setUsers(d);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'خطا در بارگذاری کاربران');
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleDelete(id: string) {
    if (!confirm('این کاربر حذف شود؟')) return;
    try {
      await api.delete(`/api/users/${id}`);
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'خطا در حذف کاربر');
    }
  }

  return (
    <Layout title="مدیریت کاربران" navItems={ACCOUNTANT_NAV}>
      <div className="card">
        <h2>➕ افزودن کاربر</h2>
        <CreateUserForm onCreated={load} />
      </div>

      <div className="card">
        <h2>👤 کاربران</h2>
        {error && <div className="msg err">{error}</div>}
        {!users && !error && <div className="loading">در حال بارگذاری…</div>}
        {users && (
          <table>
            <thead>
              <tr>
                <th>نام کاربری</th>
                <th>نام</th>
                <th>نقش</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>{u.name}</td>
                  <td>{u.role === 'operator' ? 'اپراتور' : 'حسابدار'}</td>
                  <td>
                    <button className="secondary" onClick={() => handleDelete(u.id)}>
                      حذف
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

function CreateUserForm({ onCreated }: { onCreated: () => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState<UserRole>('operator');
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await api.post('/api/users', { username, password, name, role });
      setMessage({ ok: true, text: '✅ کاربر ایجاد شد.' });
      setUsername('');
      setPassword('');
      setName('');
      onCreated();
    } catch (e) {
      setMessage({ ok: false, text: e instanceof ApiError ? e.message : 'خطا' });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>نام کاربری</label>
      <input value={username} onChange={(e) => setUsername(e.target.value)} required />
      <label style={{ marginTop: '.5rem' }}>نام نمایشی</label>
      <input value={name} onChange={(e) => setName(e.target.value)} required />
      <label style={{ marginTop: '.5rem' }}>رمز عبور</label>
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
      <label style={{ marginTop: '.5rem' }}>نقش</label>
      <select value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
        <option value="operator">اپراتور</option>
        <option value="accountant">حسابدار</option>
      </select>
      <p style={{ marginTop: '.75rem' }}>
        <button className="primary" disabled={submitting} type="submit">
          ایجاد کاربر
        </button>
      </p>
      {message && <div className={`msg ${message.ok ? 'ok' : 'err'}`}>{message.text}</div>}
    </form>
  );
}
