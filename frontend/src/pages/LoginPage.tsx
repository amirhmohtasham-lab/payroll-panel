import { type FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ApiError } from '../api/client';

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const res = await login(username, password);
      navigate(res.role === 'operator' ? '/operator' : '/');
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'خطا در ورود');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>🌾 گندم دشت — ورود</h1>
        <label>نام کاربری</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
        <label>رمز عبور</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <div className="msg err">{error}</div>}
        <button className="primary" type="submit" disabled={submitting}>
          {submitting ? 'در حال ورود…' : 'ورود'}
        </button>
      </form>
    </div>
  );
}
