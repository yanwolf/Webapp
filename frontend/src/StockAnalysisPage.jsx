import React, { useState } from 'react';
import api from './api';
import TickerInput from './components/TickerInput';
import StockAnalysisResult from './components/StockAnalysisResult';

export default function StockAnalysisPage() {
  const [ticker, setTicker] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const run = async () => {
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post('/api/analyze-stock', { ticker: ticker.trim() });
      setData(data);
    } catch (e) {
      setError(e?.response?.data?.detail || '發生未知錯誤');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') run();
  };

  return (
    <div>
      <p className="hero-sub" style={{ marginLeft: 0 }}>
        輸入一檔台股代碼，把多種策略目前的判斷、以及本益比、法人買賣超等基本面資訊整理給你看，
        幫助你自己判斷值不值得留意——不會直接告訴你「買」或「不買」。
      </p>

      <div className="panel control-panel" style={{ gridTemplateColumns: '2fr auto' }}>
        <div className="field" onKeyDown={handleKeyDown}>
          <label>台股代碼</label>
          <TickerInput market="tw" value={ticker} onChange={setTicker} placeholder="例如 2330 / 台積電 / 0050" />
        </div>
        <button className="run-btn" onClick={run} disabled={loading || !ticker.trim()}>
          {loading ? '分析中…' : '開始分析'}
        </button>
      </div>

      {loading && (
        <div className="status-line">
          <span className="spinner" />
          正在跑完所有策略並查詢基本面資料…
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {data && data.notes && data.notes.length > 0 && (
        <div className="info-box">{data.notes.map((n, i) => <div key={i}>ℹ️ {n}</div>)}</div>
      )}

      {!data && !loading && !error && (
        <div className="empty-state">輸入代碼後按「開始分析」，結果會顯示在這裡</div>
      )}

      {data && !loading && <StockAnalysisResult data={data} />}

      <footer className="note">
        這裡顯示的是「如果你在過去用這個策略邏輯操作這檔股票，現在會是什麼倉位」，是歷史規則套用到今天的結果，
        不是對未來走勢的預測，也不構成投資建議。基本面資料（本益比、法人買賣超）僅供參考，實際決策請自行評估或諮詢專業意見。
      </footer>
    </div>
  );
}
