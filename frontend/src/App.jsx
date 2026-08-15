import React, { useEffect, useState } from 'react';
import api from './api';
import './App.css';
import ControlPanel from './components/ControlPanel';
import MetricsGrid from './components/MetricsGrid';
import PriceChart from './components/PriceChart';
import { RsiChart, MacdChart } from './components/OscillatorChart';
import EquityChart from './components/EquityChart';
import TradesTable from './components/TradesTable';
import WatchlistPage from './WatchlistPage';
import ComparePage from './ComparePage';
import LoginPage from './LoginPage';

function defaultDates() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 8);
  const fmt = (d) => d.toISOString().slice(0, 10);
  return { start: fmt(start), end: fmt(end) };
}

const STRATEGY_SUBTITLE = {
  bollinger: '擠壓突破 · 貼軌趨勢跟隨 · W底/M頭背離確認',
  ma3: 'EMA快中慢三線排列 · 黃金/死亡交叉 · 貼刀拉回進場',
  ma_cross: '雙均線黃金/死亡交叉 · 經典趨勢跟隨',
  donchian: 'N日高低點突破 · 海龜交易法則簡化版',
  rsi: 'RSI超買超賣反彈 · 經典均值回歸',
  macd: 'MACD/訊號線交叉 · 經典動能指標',
  buy_hold: '第一根K棒買進、全程持有到底 · 用來檢驗策略是否真的打敗大盤',
};

export default function App() {
  const [username, setUsername] = useState(() => localStorage.getItem('username'));
  const [tab, setTab] = useState('backtest');
  const { start, end } = defaultDates();
  const [form, setForm] = useState({
    strategy: 'bollinger',
    market: 'us',
    ticker: 'SPY',
    interval: '1d',
    start,
    end,
    capital: 1000000,
    allow_short: true,
    ma_fast: 20,
    ma_mid: 60,
    ma_slow: 240,
    cross_fast: 20,
    cross_slow: 60,
    cross_ma_type: 'sma',
    cross_stop_pct: 0.08,
    donch_entry_window: 20,
    donch_exit_window: 10,
    rsi_period: 14,
    rsi_oversold: 30,
    rsi_overbought: 70,
    rsi_stop_pct: 0.06,
    macd_fast: 12,
    macd_slow: 26,
    macd_signal: 9,
    macd_stop_pct: 0.08,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const numericKeys = [
    'capital', 'ma_fast', 'ma_mid', 'ma_slow',
    'cross_fast', 'cross_slow', 'cross_stop_pct',
    'donch_entry_window', 'donch_exit_window',
    'rsi_period', 'rsi_oversold', 'rsi_overbought', 'rsi_stop_pct',
    'macd_fast', 'macd_slow', 'macd_signal', 'macd_stop_pct',
  ];

  const runBacktest = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = { ...form, end: form.end || undefined };
      numericKeys.forEach((k) => { payload[k] = Number(form[k]); });
      const { data } = await api.post('/api/backtest', payload);
      setResult(data);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setError(detail || e.message || '發生未知錯誤');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const chartType = result?.chart_type;

  useEffect(() => {
    const onExpired = () => setUsername(null);
    window.addEventListener('auth-expired', onExpired);
    return () => window.removeEventListener('auth-expired', onExpired);
  }, []);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setUsername(null);
  };

  if (!username) {
    return <LoginPage onLoggedIn={setUsername} />;
  }

  return (
    <div className="app-shell">
      <div className="hero" style={{ justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div className="hero-mark">
            <svg viewBox="0 0 34 34" fill="none">
              <polygon points="17,2 30,12 24,32 10,32 4,12" stroke="#d4b06a" strokeWidth="1.2" fill="rgba(212,176,106,0.08)" />
              <polygon points="17,2 30,12 17,17" fill="rgba(110,231,223,0.18)" />
              <line x1="17" y1="2" x2="17" y2="32" stroke="#6ee7df" strokeWidth="0.6" opacity="0.6" />
            </svg>
          </div>
          <h1>黑鑽策略回測</h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ color: 'var(--text-faint)', fontSize: 13 }}>{username}</span>
          <button
            onClick={logout}
            style={{ background: 'none', border: '1px solid var(--border)', color: 'var(--text-muted)', borderRadius: 7, padding: '6px 12px', fontSize: 12.5, cursor: 'pointer' }}
          >
            登出
          </button>
        </div>
      </div>

      <div className="tab-row">
        <button className={`tab-btn ${tab === 'backtest' ? 'active' : ''}`} onClick={() => setTab('backtest')}>回測</button>
        <button className={`tab-btn ${tab === 'compare' ? 'active' : ''}`} onClick={() => setTab('compare')}>策略比較</button>
        <button className={`tab-btn ${tab === 'watchlist' ? 'active' : ''}`} onClick={() => setTab('watchlist')}>追蹤清單</button>
      </div>

      {tab === 'watchlist' ? (
        <WatchlistPage />
      ) : tab === 'compare' ? (
        <ComparePage />
      ) : (
      <>
      <p className="hero-sub">
        {STRATEGY_SUBTITLE[form.strategy]} — 輸入任一美股、台股或加密貨幣代碼，立即檢視策略歷史績效。
      </p>

      <ControlPanel form={form} setForm={setForm} onSubmit={runBacktest} loading={loading} />

      {loading && (
        <div className="status-line">
          <span className="spinner" />
          正在抓取資料並執行回測，資料範圍越長需要的時間越久…
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {result && result.notes && result.notes.length > 0 && (
        <div className="info-box">
          {result.notes.map((n, i) => <div key={i}>ℹ️ {n}</div>)}
        </div>
      )}

      {!result && !loading && !error && (
        <div className="empty-state">設定好參數後按「執行回測」，結果會顯示在這裡</div>
      )}

      {result && !loading && (
        <>
          <MetricsGrid metrics={result.metrics} />

          <PriceChart
            priceSeries={result.price_series}
            trades={result.trades}
            chartType={chartType}
            overlayKeys={result.overlay_keys}
            strategyLabel={result.strategy_label}
          />

          {chartType === 'oscillator_rsi' && (
            <RsiChart priceSeries={result.price_series} oversold={form.rsi_oversold} overbought={form.rsi_overbought} />
          )}
          {chartType === 'oscillator_macd' && (
            <MacdChart priceSeries={result.price_series} />
          )}

          <EquityChart equitySeries={result.equity_series} />
          <TradesTable trades={result.trades} />
        </>
      )}

      <footer className="note">
        資料來源：Yahoo Finance（經 yfinance 抓取）。策略邏輯為量化重建，僅供研究與策略驗證使用，不構成投資建議；歷史績效不代表未來表現。
      </footer>
      </>
      )}
    </div>
  );
}
