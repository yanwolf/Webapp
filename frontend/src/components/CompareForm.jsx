import React, { useState } from 'react';

const MARKET_META = {
  us: { label: '美股', placeholder: '例如 SPY / AAPL / QQQ' },
  tw: { label: '台股', placeholder: '例如 2330 / 0050 / ^TWII' },
  crypto: { label: '加密貨幣', placeholder: '例如 BTC / ETH' },
};

export default function CompareForm({ form, setForm, onSubmit, loading }) {
  const update = (key) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((p) => ({ ...p, [key]: val }));
  };

  return (
    <div className="panel control-panel">
      <div className="field">
        <label>交易風格</label>
        <select value={form.style} onChange={update('style')}>
          <option value="swing">長線波段（日K）</option>
          <option value="short">短沖（1小時K）</option>
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
        <input type="text" value={form.ticker} onChange={update('ticker')} placeholder={MARKET_META[form.market].placeholder} />
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
      <div className="field field-checkbox">
        <input type="checkbox" id="cmp_allow_short" checked={form.allow_short} onChange={update('allow_short')} />
        <label htmlFor="cmp_allow_short">允許做空</label>
      </div>
      <button className="run-btn" onClick={onSubmit} disabled={loading || !form.ticker.trim()}>
        {loading ? '比較中…' : '比較所有策略'}
      </button>
    </div>
  );
}
