import React, { useState } from 'react';
import api from './api';
import CompareForm from './components/CompareForm';
import CompareTable from './components/CompareTable';

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

export default function ComparePage() {
  const { start, end } = defaultDates();
  const [form, setForm] = useState({
    style: 'swing', market: 'us', ticker: 'SPY', start, end, capital: 1000000, allow_short: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = { ...form, capital: Number(form.capital), end: form.end || undefined };
      const { data } = await api.post('/api/compare-strategies', payload);
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
        選一檔標的、挑你的交易風格，一次跑完所有策略，看哪個策略真的打敗買進持有。
      </p>

      <CompareForm form={form} setForm={setForm} onSubmit={run} loading={loading} />

      {loading && (
        <div className="status-line">
          <span className="spinner" />
          正在跑完所有策略，稍等一下…
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {data && data.notes && data.notes.length > 0 && (
        <div className="info-box">{data.notes.map((n, i) => <div key={i}>ℹ️ {n}</div>)}</div>
      )}

      {!data && !loading && !error && (
        <div className="empty-state">設定好參數後按「比較所有策略」，結果會顯示在這裡</div>
      )}

      {data && !loading && (
        <>
          <div style={{ color: 'var(--text-faint)', fontSize: 12, marginBottom: 10 }}>
            資料來源：{DATA_SOURCE_LABELS[data.data_source] || data.data_source || '未知'}
          </div>
          <CompareTable data={data} />
        </>
      )}

      <footer className="note">
        提醒：這是歷史回測排名，不代表未來績效一定維持同樣順序。短沖用1小時K，歷史資料受 Yahoo Finance 限制約只能回溯2年，樣本數較少時排名的參考價值會降低；長線波段用日K資料較長，統計上更可信一些。
      </footer>
    </div>
  );
}
