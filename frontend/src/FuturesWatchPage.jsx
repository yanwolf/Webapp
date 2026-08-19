import React, { useEffect, useState } from 'react';
import api from './api';
import FuturesWatchCard from './components/FuturesWatchCard';

export default function FuturesWatchPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get('/api/futures-watch');
      setData(data.results);
    } catch (e) {
      setError(e?.response?.data?.detail || '發生未知錯誤');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <p className="hero-sub" style={{ marginLeft: 0 }}>
        美股期貨用均線三刀流（1小時K，近24小時交易含盤前盤後）判斷目前排列狀態。
      </p>

      <div style={{ marginBottom: 16 }}>
        <button className="run-btn" onClick={load} disabled={loading}>
          {loading ? '更新中…' : '重新整理'}
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}

      {loading && !data && (
        <div className="status-line"><span className="spinner" />載入中…</div>
      )}

      {data && data.map((item) => (
        <FuturesWatchCard key={item.ticker} label={item.label} snapshot={item.snapshot} />
      ))}

      <footer className="note">
        期貨近24小時交易，資料每次重新整理即時抓取，不像股票有明確收盤時間。
        排列判斷邏輯跟台股個股分析的均線三刀流完全共用同一套程式碼。僅供研究參考，不構成投資建議。
      </footer>
    </div>
  );
}
