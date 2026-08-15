import React, { useState } from 'react';
import api from '../api';

const MARKET_META = {
  us: { label: '美股', placeholder: '例如 SPY / AAPL' },
  tw: { label: '台股', placeholder: '例如 2330 / ^TWII' },
  crypto: { label: '加密貨幣', placeholder: '例如 BTC / ETH' },
};

const STRATEGY_META = {
  bollinger: '布林通道策略',
  ma3: '均線三刀流',
  ma_cross: '均線黃金/死亡交叉',
  donchian: '唐奇安通道突破',
  rsi: 'RSI 超買超賣',
  macd: 'MACD 動量策略',
};

const INTERVAL_META = {
  '1d': '日K', '4h': '4小時K', '1h': '1小時K', '15m': '15分K', '5m': '5分K', '1m': '1分K',
};

export default function WatchlistForm({ onAdded }) {
  const [form, setForm] = useState({
    market: 'us', ticker: '', strategy: 'bollinger', interval: '1d', allow_short: true,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const update = (key) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((p) => ({ ...p, [key]: val }));
  };

  const submit = async () => {
    if (!form.ticker.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await api.post(`/api/watchlist`, form);
      setForm((p) => ({ ...p, ticker: '' }));
      onAdded && onAdded();
    } catch (e) {
      setError(e?.response?.data?.detail || '新增失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel control-panel" style={{ marginBottom: 24 }}>
      <div className="field">
        <label>市場</label>
        <select value={form.market} onChange={update('market')}>
          <option value="us">美股</option>
          <option value="tw">台股</option>
          <option value="crypto">加密貨幣</option>
        </select>
      </div>
      <div className="field">
        <label>代碼</label>
        <input type="text" value={form.ticker} onChange={update('ticker')} placeholder={MARKET_META[form.market].placeholder} />
      </div>
      <div className="field">
        <label>策略</label>
        <select value={form.strategy} onChange={update('strategy')}>
          {Object.entries(STRATEGY_META).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>
      <div className="field">
        <label>K線週期</label>
        <select value={form.interval} onChange={update('interval')}>
          {Object.entries(INTERVAL_META).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>
      <div className="field field-checkbox">
        <input type="checkbox" id="wl_allow_short" checked={form.allow_short} onChange={update('allow_short')} />
        <label htmlFor="wl_allow_short">允許做空</label>
      </div>
      <button className="run-btn" onClick={submit} disabled={loading || !form.ticker.trim()}>
        {loading ? '新增中…' : '加入追蹤'}
      </button>
      {error && <div className="error-box" style={{ gridColumn: '1 / -1' }}>{error}</div>}
    </div>
  );
}
