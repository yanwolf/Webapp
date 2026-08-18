import React from 'react';
import TickerInput from './TickerInput';

const MARKET_META = {
  us: { label: '美股', placeholder: '例如 SPY / AAPL / QQQ' },
  tw: { label: '台股', placeholder: '例如 2330 / 0050 / ^TWII' },
  crypto: { label: '加密貨幣', placeholder: '例如 BTC / ETH' },
};

const STRATEGY_META = {
  bollinger: '布林通道策略',
  ma3: '均線三刀流',
  ma_cross: '均線黃金/死亡交叉',
  donchian: '唐奇安通道突破',
  rsi: 'RSI 超買超賣',
  macd: 'MACD 動量策略',
  atr_channel: 'ATR 通道突破',
  fvg: 'FVG 缺口回補',
};

const INTERVAL_META = {
  '1d': '日K', '4h': '4小時K', '1h': '1小時K', '15m': '15分K', '5m': '5分K', '1m': '1分K',
};

export default function OptimizeForm({ form, setForm, onSubmit, loading }) {
  const update = (key) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((p) => ({ ...p, [key]: val }));
  };

  return (
    <div className="panel control-panel">
      <div className="field">
        <label>策略</label>
        <select value={form.strategy} onChange={update('strategy')}>
          {Object.entries(STRATEGY_META).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>
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
        <TickerInput
          market={form.market}
          value={form.ticker}
          onChange={(v) => setForm((p) => ({ ...p, ticker: v }))}
          placeholder={MARKET_META[form.market].placeholder}
        />
      </div>
      <div className="field">
        <label>K線週期</label>
        <select value={form.interval} onChange={update('interval')}>
          {Object.entries(INTERVAL_META).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>
      <div className="field">
        <label>開始日期</label>
        <input type="date" value={form.start} onChange={update('start')} />
      </div>
      <div className="field">
        <label>結束日期</label>
        <input type="date" value={form.end} onChange={update('end')} />
      </div>
      <div className="field">
        <label>初始資金</label>
        <input type="number" value={form.capital} onChange={update('capital')} min={1} step={10000} />
      </div>
      <div className="field">
        <label>交易方式</label>
        <select
          value={form.allow_short ? 'short' : 'cash'}
          onChange={(e) => setForm((p) => ({ ...p, allow_short: e.target.value === 'short' }))}
        >
          <option value="cash">現股買賣（只做多）</option>
          <option value="short">現股 + 做空</option>
        </select>
      </div>
      <button className="run-btn" onClick={onSubmit} disabled={loading || !form.ticker.trim()}>
        {loading ? '最佳化中…' : '開始最佳化'}
      </button>
    </div>
  );
}
