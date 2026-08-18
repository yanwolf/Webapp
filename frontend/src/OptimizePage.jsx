import React, { useState } from 'react';
import api from './api';
import OptimizeForm from './components/OptimizeForm';
import OptimizeTable from './components/OptimizeTable';

const DATA_SOURCE_LABELS = {
  finmind: 'FinMind（台股）',
  twelve_data: 'Twelve Data（美股）',
  binance: 'Binance（加密貨幣）',
  yfinance: 'Yahoo Finance（備援）',
};

function defaultDates() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 5);
  const fmt = (d) => d.toISOString().slice(0, 10);
  return { start: fmt(start), end: fmt(end) };
}

export default function OptimizePage() {
  const { start, end } = defaultDates();
  const [form, setForm] = useState({
    strategy: 'bollinger', market: 'us', ticker: 'SPY', interval: '1d',
    start, end, capital: 1000000, allow_short: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = { ...form, capital: Number(form.capital), end: form.end || undefined };
      const { data } = await api.post('/api/optimize-strategy', payload);
      setData(data);
    } catch (e) {
      setError(e?.response?.data?.detail || '發生未知錯誤');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <p className="hero-sub" style={{ marginLeft: 0 }}>
        選一個策略，系統會自動掃過一組預先設計好的參數組合（週期、門檻、倍數等），
        找出這檔標的、這段時間裡歷史表現較好的參數設定。
      </p>

      <OptimizeForm form={form} setForm={setForm} onSubmit={run} loading={loading} />

      {loading && (
        <div className="status-line">
          <span className="spinner" />
          正在測試多組參數組合，數量較多時可能需要十幾秒…
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {data && data.notes && data.notes.length > 0 && (
        <div className="info-box">{data.notes.map((n, i) => <div key={i}>ℹ️ {n}</div>)}</div>
      )}

      {!data && !loading && !error && (
        <div className="empty-state">設定好參數後按「開始最佳化」，結果會顯示在這裡</div>
      )}

      {data && !loading && (
        <>
          <div style={{ color: 'var(--text-faint)', fontSize: 12, marginBottom: 10 }}>
            資料來源：{DATA_SOURCE_LABELS[data.data_source] || data.data_source || '未知'}
          </div>
          <OptimizeTable data={data} />
        </>
      )}

      <footer className="note">
        這是針對「這一檔標的、這一段歷史區間」找出來的最佳參數，換一檔標的或換一段時間，
        最佳參數很可能完全不一樣——這是歷史資料過度配適(overfitting)的常見現象，
        找到的參數不保證未來也最好，建議用不同時間區間分別測試，選擇在多段區間都相對穩定的參數，
        而不是只看單一區間報酬率最高的那一組。
      </footer>
    </div>
  );
}
