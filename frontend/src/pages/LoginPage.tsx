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
      <div className="login-story" aria-hidden="true">
        <span className="eyebrow">دفتر مزرعه</span>
        <strong>عددها را<br />به زمین برگردان.</strong>
        <span className="login-story-line" />
        <span>حقوق، محصول و هزینه<br />در یک قاب آرام.</span>
      </div>
      <form className="login-card" onSubmit={handleSubmit}>
        <span className="eyebrow">ورود امن</span>
        <h1>گندم دشت</h1>
        <p className="login-subtitle">به دفتر مالی مزرعه خوش آمدید</p>
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
