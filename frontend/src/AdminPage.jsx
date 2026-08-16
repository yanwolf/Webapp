import React, { useCallback, useEffect, useState } from 'react';
import api from './api';

function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

export default function AdminPage({ currentUserId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const fetchUsers = useCallback(async () => {
    try {
      const { data } = await api.get('/api/admin/users');
      setData(data);
    } catch (e) {
      setError(e?.response?.data?.detail || '載入失敗');
    }
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  const removeUser = async (id, username) => {
    if (!window.confirm(`確定要刪除帳號「${username}」嗎？這會一併清除他的追蹤清單與 Telegram 設定，無法復原。`)) return;
    setBusyId(id);
    try {
      await api.delete(`/api/admin/users/${id}`);
      fetchUsers();
    } catch (e) {
      alert(e?.response?.data?.detail || '刪除失敗');
    } finally {
      setBusyId(null);
    }
  };

  if (error) return <div className="error-box">{error}</div>;
  if (!data) return <div className="panel">載入中…</div>;

  return (
    <div>
      <p className="hero-sub" style={{ marginLeft: 0 }}>
        目前 {data.current_count} / {data.max_users} 人（開放註冊上限由後端環境變數 MAX_USERS 控制）。
      </p>

      <div className="chart-panel">
        <div className="chart-panel-title">
          已註冊使用者 <span className="badge">共 {data.users.length} 人</span>
        </div>
        <div className="table-wrap">
          <table className="trades">
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>帳號</th>
                <th style={{ textAlign: 'left' }}>註冊時間</th>
                <th>Telegram</th>
                <th>追蹤項目數</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.users.map((u) => (
                <tr key={u.id}>
                  <td style={{ textAlign: 'left' }}>
                    {u.username}
                    {u.id === currentUserId && <span className="badge" style={{ marginLeft: 6 }}>你自己</span>}
                  </td>
                  <td style={{ textAlign: 'left', color: 'var(--text-faint)' }}>{fmtDate(u.created_at)}</td>
                  <td>{u.telegram_linked ? '✅ 已連結' : '—'}</td>
                  <td>{u.watchlist_count}</td>
                  <td>
                    {u.id !== currentUserId && (
                      <button
                        onClick={() => removeUser(u.id, u.username)}
                        disabled={busyId === u.id}
                        style={{ background: 'none', border: 'none', color: 'var(--up)', cursor: 'pointer', fontSize: 12 }}
                      >
                        {busyId === u.id ? '刪除中…' : '刪除'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <footer className="note">
        管理員身分由後端環境變數 ADMIN_USERNAME 指定；若未設定，則第一個註冊的帳號自動視為管理員。
        刪除使用者會一併清除他的追蹤清單與 Telegram Bot 設定，且無法復原。
      </footer>
    </div>
  );
}
