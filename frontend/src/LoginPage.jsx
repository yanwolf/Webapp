import React, { useState } from 'react';
import api from './api';

export default function LoginPage({ onLoggedIn }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [form, setForm] = useState({ username: '', password: '', invite_code: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const update = (key) => (e) => setForm((p) => ({ ...p, [key]: e.target.value }));

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const path = mode === 'login' ? '/api/auth/login' : '/api/auth/register';
      const payload = mode === 'login'
        ? { username: form.username, password: form.password }
        : form;
      const { data } = await api.post(path, payload);
      localStorage.setItem('token', data.token);
      localStorage.setItem('username', data.username);
      onLoggedIn(data.username);
    } catch (e) {
      setError(e?.response?.data?.detail || '發生錯誤，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') submit();
  };

  return (
    <div className="app-shell login-shell">
      <div className="hero" style={{ justifyContent: 'center' }}>
        <div className="hero-mark">
          <svg viewBox="0 0 34 34" fill="none">
            <circle cx="17" cy="17" r="14" stroke="#d4b06a" strokeWidth="1.2" fill="rgba(212,176,106,0.06)" />
            <circle cx="17" cy="17" r="10.2" stroke="#6ee7df" strokeWidth="0.5" opacity="0.45" />
            <polygon points="17,6.5 20.3,17 17,17" fill="#d4b06a" />
            <polygon points="17,6.5 13.7,17 17,17" fill="#e8cd94" opacity="0.85" />
            <polygon points="17,27.5 20.3,17 17,17" fill="#6ee7df" opacity="0.65" />
            <polygon points="17,27.5 13.7,17 17,17" fill="#6ee7df" opacity="0.35" />
            <circle cx="17" cy="17" r="1.7" fill="#08090b" stroke="#d4b06a" strokeWidth="0.8" />
          </svg>
        </div>
        <h1>策略實驗室</h1>
      </div>

      <div className="panel" style={{ marginTop: 24 }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          <button
            className={`tab-btn ${mode === 'login' ? 'active' : ''}`}
            style={{ marginRight: 8 }}
            onClick={() => { setMode('login'); setError(null); }}
          >
            登入
          </button>
          <button
            className={`tab-btn ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setError(null); }}
          >
            註冊新帳號
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }} onKeyDown={handleKeyDown}>
          <div className="field">
            <label>帳號</label>
            <input type="text" value={form.username} onChange={update('username')} placeholder="3-20 字元英數字" />
          </div>
          <div className="field">
            <label>密碼</label>
            <input type="password" value={form.password} onChange={update('password')} placeholder="至少 6 碼" />
          </div>
          {mode === 'register' && (
            <div className="field">
              <label>邀請碼</label>
              <input type="text" value={form.invite_code} onChange={update('invite_code')} placeholder="向管理員索取" />
            </div>
          )}

          {error && <div className="error-box">{error}</div>}

          <button className="run-btn" onClick={submit} disabled={loading || !form.username || !form.password}>
            {loading ? '處理中…' : mode === 'login' ? '登入' : '註冊'}
          </button>
        </div>
      </div>
    </div>
  );
}
