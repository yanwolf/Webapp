import React, { useEffect, useState } from 'react';
import api from '../api';

export default function TelegramLink() {
  const [status, setStatus] = useState(null);
  const [botToken, setBotToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saveResult, setSaveResult] = useState(null);
  const [showGuide, setShowGuide] = useState(false);

  const fetchStatus = async () => {
    try {
      const { data } = await api.get('/api/telegram/status');
      setStatus(data);
    } catch (e) {
      setStatus(null);
    }
  };

  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 6000);
    return () => clearInterval(timer);
  }, []);

  const saveToken = async () => {
    if (!botToken.trim()) return;
    setLoading(true);
    setError(null);
    setSaveResult(null);
    try {
      const { data } = await api.post('/api/telegram/config', { bot_token: botToken.trim() });
      setSaveResult(data);
      setBotToken('');
      fetchStatus();
    } catch (e) {
      setError(e?.response?.data?.detail || '儲存失敗');
    } finally {
      setLoading(false);
    }
  };

  const unlink = async () => {
    await api.delete('/api/telegram/config');
    setSaveResult(null);
    fetchStatus();
  };

  if (!status) {
    return <div className="panel" style={{ marginBottom: 24 }}>載入 Telegram 連結狀態中…</div>;
  }

  return (
    <div className="panel" style={{ marginBottom: 24 }}>
      <div className="chart-panel-title" style={{ marginBottom: 4 }}>Telegram 通知</div>
      <button
        onClick={() => setShowGuide((s) => !s)}
        style={{ background: 'none', border: 'none', color: 'var(--cyan)', fontSize: 12.5, cursor: 'pointer', padding: 0, marginBottom: 14 }}
      >
        {showGuide ? '收起設定教學 ▲' : '不知道怎麼設定？點這裡看教學 ▼'}
      </button>

      {showGuide && (
        <ol style={{ color: 'var(--text-muted)', fontSize: 13.5, lineHeight: 2, paddingLeft: 20, marginBottom: 20 }}>
          <li>打開 Telegram，搜尋 <b style={{ color: 'var(--text)' }}>@BotFather</b>，點進去對話</li>
          <li>傳送 <code>/newbot</code>，依指示幫你的 Bot 取一個名字</li>
          <li>接著幫它取一個 username，<b>結尾必須是 bot</b>（例如 <code>tzujen_signal_bot</code>）</li>
          <li>完成後 BotFather 會回你一長串 <b style={{ color: 'var(--text)' }}>Bot Token</b>（長得像 <code>123456:ABC-xyz...</code>），複製起來</li>
          <li>貼到下面的欄位，按「儲存並啟用」——系統會自動幫你註冊好連線</li>
          <li>回 Telegram 搜尋你剛建立的 Bot，傳送 <code>/start</code> 給它，完成最後連結</li>
        </ol>
      )}

      {status.linked ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <span style={{ color: 'var(--down)', fontSize: 14 }}>
            ✅ 已連結 @{status.bot_username}，訊號會發送到你的 Telegram
          </span>
          <button className="run-btn" style={{ background: 'var(--panel-raised)', color: 'var(--text)' }} onClick={unlink}>
            解除連結
          </button>
        </div>
      ) : status.configured ? (
        <div>
          <p style={{ color: 'var(--text-muted)', fontSize: 13.5, marginTop: 0, marginBottom: 14 }}>
            已設定 Bot <b style={{ color: 'var(--text)' }}>@{status.bot_username}</b>，但還沒收到你的訊息。
            回 Telegram 傳送 <code>/start</code> 給它完成最後連結。
          </p>
        </div>
      ) : (
        <div>
          <div className="field" style={{ marginBottom: 14 }}>
            <label>Bot Token</label>
            <input
              type="text"
              value={botToken}
              onChange={(e) => setBotToken(e.target.value)}
              placeholder="貼上從 @BotFather 拿到的 Token"
            />
          </div>
          <button className="run-btn" onClick={saveToken} disabled={loading || !botToken.trim()}>
            {loading ? '儲存中…' : '儲存並啟用'}
          </button>

          {error && <div className="error-box" style={{ marginTop: 14 }}>{error}</div>}

          {saveResult && (
            <div className="info-box" style={{ marginTop: 14 }}>
              ✅ 已儲存，Bot：@{saveResult.bot_username}
              {saveResult.webhook_registered
                ? '，連線已自動註冊完成。回 Telegram 傳送 /start 給它完成連結。'
                : `，但連線註冊失敗：${saveResult.webhook_error || '請稍後再試一次'}`}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
