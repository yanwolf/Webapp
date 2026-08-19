import React, { useEffect, useState } from 'react';
import api from './api';
import './App.css';
import NavDrawer from './NavDrawer';
import ControlPanel from './components/ControlPanel';
import MetricsGrid from './components/MetricsGrid';
import OpenPositionBanner from './components/OpenPositionBanner';
import PriceChart from './components/PriceChart';
import { RsiChart, MacdChart } from './components/OscillatorChart';
import EquityChart from './components/EquityChart';
import TradesTable from './components/TradesTable';
import WatchlistPage from './WatchlistPage';
import ComparePage from './ComparePage';
import OptimizePage from './OptimizePage';
import StockAnalysisPage from './StockAnalysisPage';
import FuturesWatchPage from './FuturesWatchPage';
import HomePage from './HomePage';
import AdminPage from './AdminPage';
import LoginPage from './LoginPage';

function defaultDates() {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 8);
  const fmt = (d) => d.toISOString().slice(0, 10);
  return { start: fmt(start), end: fmt(end) };
}

const DATA_SOURCE_LABELS = {
  finmind: 'FinMind（台股）',
  twelve_data: 'Twelve Data（美股）',
  binance: 'Binance（加密貨幣）',
  yfinance: 'Yahoo Finance（備援）',
};

const STRATEGY_SUBTITLE = {
  bollinger: '擠壓突破 · 貼軌趨勢跟隨 · W底/M頭背離確認',
  ma3: 'EMA快中慢三線排列 · 黃金/死亡交叉 · 貼刀拉回進場',
  ma_cross: '雙均線黃金/死亡交叉 · 經典趨勢跟隨',
  donchian: 'N日高低點突破 · 海龜交易法則簡化版',
  rsi: 'RSI超買超賣反彈 · 經典均值回歸',
  macd: 'MACD/訊號線交叉 · 經典動能指標',
  atr_channel: '中軌±ATR倍數畫出通道 · 用波動度定義突破',
  fvg: '偵測三根K棒缺口 · 等待回補反轉確認進場',
  pivot: '突破經確認的轉折高低點 · 無濾網無停損 · 靠反向訊號翻單，永遠有部位',
  ma60_filter: '收盤站上60日均線且大方向偏多才進場 · 只做多 · 規則最單純',
  buy_hold: '第一根K棒買進、全程持有到底 · 用來檢驗策略是否真的打敗大盤',
};

export default function App() {
  const [username, setUsername] = useState(() => localStorage.getItem('username'));
  const [me, setMe] = useState(null);
  const [tab, setTab] = useState('home');
  const [drawerOpen, setDrawerOpen] = useState(false);
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
    ma_type: 'sma',
    cross_fast: 20,
    cross_slow: 60,
    cross_ma_type: 'sma',
    donch_entry_window: 20,
    donch_exit_window: 10,
    rsi_period: 14,
    rsi_oversold: 30,
    rsi_overbought: 70,
    macd_fast: 12,
    macd_slow: 26,
    macd_signal: 9,
    stop_type: 'pct',
    stop_pct: 0.08,
    atr_period: 14,
    atr_mult: 2.0,
    atr_ch_period: 14,
    atr_ch_ma_window: 20,
    atr_ch_mult: 2.0,
    fvg_atr_period: 14,
    fvg_max_wait: 20,
    fvg_atr_stop_mult: 1.5,
    fvg_atr_target_mult: 3.0,
    pivot_left: 2,
    pivot_right: 5,
    ma60_period: 60,
    ma60_filter_period: 200,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const numericKeys = [
    'capital', 'ma_fast', 'ma_mid', 'ma_slow',
    'cross_fast', 'cross_slow',
    'donch_entry_window', 'donch_exit_window',
    'rsi_period', 'rsi_oversold', 'rsi_overbought',
    'macd_fast', 'macd_slow', 'macd_signal',
    'stop_pct', 'atr_period', 'atr_mult',
    'atr_ch_period', 'atr_ch_ma_window', 'atr_ch_mult',
    'fvg_atr_period', 'fvg_max_wait', 'fvg_atr_stop_mult', 'fvg_atr_target_mult',
    'pivot_left', 'pivot_right', 'ma60_period', 'ma60_filter_period',
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

  useEffect(() => {
    if (!username) { setMe(null); return; }
    api.get('/api/auth/me').then(({ data }) => setMe(data)).catch(() => setMe(null));
  }, [username]);

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
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <button className="hamburger-btn" onClick={() => setDrawerOpen(true)} aria-label="開啟選單">☰</button>
          <h1>策略實驗室</h1>
        </div>
      </div>

      <NavDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        tab={tab}
        setTab={setTab}
        isAdmin={!!me?.is_admin}
        username={username}
        onLogout={logout}
      />

      <div style={{ display: tab === 'home' ? 'block' : 'none' }}>
        <HomePage onNavigate={setTab} />
      </div>
      <div style={{ display: tab === 'watchlist' ? 'block' : 'none' }}>
        <WatchlistPage />
      </div>
      <div style={{ display: tab === 'compare' ? 'block' : 'none' }}>
        <ComparePage />
      </div>
      <div style={{ display: tab === 'optimize' ? 'block' : 'none' }}>
        <OptimizePage />
      </div>
      <div style={{ display: tab === 'stockcheck' ? 'block' : 'none' }}>
        <StockAnalysisPage />
      </div>
      <div style={{ display: tab === 'futures' ? 'block' : 'none' }}>
        <FuturesWatchPage />
      </div>
      {me?.is_admin && (
        <div style={{ display: tab === 'admin' ? 'block' : 'none' }}>
          <AdminPage currentUserId={me?.id} />
        </div>
      )}
      <div style={{ display: tab === 'backtest' ? 'block' : 'none' }}>
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
          <div style={{ color: 'var(--text-faint)', fontSize: 12, marginBottom: 10 }}>
            資料來源：{DATA_SOURCE_LABELS[result.data_source] || result.data_source || '未知'}
          </div>
          <MetricsGrid metrics={result.metrics} />
          <OpenPositionBanner position={result.open_position} />

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
      </div>
    </div>
  );
}
