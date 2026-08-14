import React, { useState } from 'react';
import axios from 'axios';
import './App.css';
import { API_BASE_URL } from './config';
import ControlPanel from './components/ControlPanel';
import MetricsGrid from './components/MetricsGrid';
import PriceChart from './components/PriceChart';
import EquityChart from './components/EquityChart';
import TradesTable from './components/TradesTable';

function defaultDates() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 8);
  const fmt = (d) => d.toISOString().slice(0, 10);
  return { start: fmt(start), end: fmt(end) };
}

export default function App() {
  const { start, end } = defaultDates();
  const [form, setForm] = useState({
    market: 'us',
    ticker: 'SPY',
    start,
    end,
    capital: 1000000,
    allow_short: true,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        ...form,
        capital: Number(form.capital),
        end: form.end || undefined,
      };
      const { data } = await axios.post(`${API_BASE_URL}/api/backtest`, payload);
      setResult(data);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setError(detail || e.message || '發生未知錯誤');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="hero">
        <div className="hero-mark">
          <svg viewBox="0 0 34 34" fill="none">
            <polygon points="17,2 30,12 24,32 10,32 4,12" stroke="#d4b06a" strokeWidth="1.2" fill="rgba(212,176,106,0.08)" />
            <polygon points="17,2 30,12 17,17" fill="rgba(110,231,223,0.18)" />
            <line x1="17" y1="2" x2="17" y2="32" stroke="#6ee7df" strokeWidth="0.6" opacity="0.6" />
          </svg>
        </div>
        <h1>黑鑽布林策略回測</h1>
      </div>
      <p className="hero-sub">
        擠壓突破 · 貼軌趨勢跟隨 · W底/M頭背離確認 — 輸入任一美股、台股或加密貨幣代碼，立即檢視策略歷史績效。
      </p>

      <ControlPanel form={form} setForm={setForm} onSubmit={runBacktest} loading={loading} />

      {loading && (
        <div className="status-line">
          <span className="spinner" />
          正在抓取資料並執行回測，資料範圍越長需要的時間越久…
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {!result && !loading && !error && (
        <div className="empty-state">設定好參數後按「執行回測」，結果會顯示在這裡</div>
      )}

      {result && !loading && (
        <>
          <MetricsGrid metrics={result.metrics} />
          <PriceChart priceSeries={result.price_series} trades={result.trades} />
          <EquityChart equitySeries={result.equity_series} />
          <TradesTable trades={result.trades} />
        </>
      )}

      <footer className="note">
        資料來源：Yahoo Finance（經 yfinance 抓取）。策略邏輯為教學影片重點之量化重建，僅供研究與策略驗證使用，不構成投資建議；歷史績效不代表未來表現。
      </footer>
    </div>
  );
}
