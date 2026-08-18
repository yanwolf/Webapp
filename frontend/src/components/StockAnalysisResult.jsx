import React from 'react';

function pct(v) {
  if (v == null) return '—';
  const s = (v * 100).toFixed(2);
  return `${v >= 0 ? '+' : ''}${s}%`;
}
function num(v) {
  if (v == null) return '—';
  return v.toLocaleString('zh-TW');
}
function signedNum(v) {
  if (v == null) return '—';
  return `${v >= 0 ? '+' : ''}${v.toLocaleString('zh-TW')}`;
}

const POSITION_META = {
  long: { label: '偏多（模擬持有多單）', cls: 'long' },
  short: { label: '偏空（模擬持有空單）', cls: 'short' },
  flat: { label: '中性（目前空手）', cls: null },
};

export default function StockAnalysisResult({ data }) {
  if (!data) return null;
  const {
    ticker_resolved, current_price, price_date, day_change_pct, tally, signals,
    fundamentals, institutional_daily, margin_daily, volume_stats, summary_text,
  } = data;

  return (
    <div>
      <div className="panel" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 10 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{ticker_resolved}</div>
            <div style={{ color: 'var(--text-faint)', fontSize: 12 }}>{price_date} 收盤</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div className="mono" style={{ fontSize: 26, fontWeight: 700 }}>{current_price?.toFixed(2)}</div>
            <div className={day_change_pct >= 0 ? 'up' : 'down'} style={{ fontSize: 13, fontFamily: 'var(--font-mono)' }}>
              {pct(day_change_pct)}
            </div>
          </div>
        </div>
      </div>

      {summary_text && (
        <div className="chart-panel">
          <div className="chart-panel-title">整理摘要 <span className="badge">規則統計，非AI生成</span></div>
          <p style={{ color: 'var(--text)', fontSize: 13.5, lineHeight: 1.9, marginTop: 8 }}>{summary_text}</p>
        </div>
      )}

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">偏多策略數</div>
          <div className="metric-value up">{tally.bullish}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">偏空策略數</div>
          <div className="metric-value down">{tally.bearish}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">中性策略數</div>
          <div className="metric-value">{tally.neutral}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">共檢視策略</div>
          <div className="metric-value">{signals.length}</div>
        </div>
      </div>

      {fundamentals ? (
        <div className="chart-panel">
          <div className="chart-panel-title">基本面（FinMind）</div>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginTop: 10 }}>
            <div>
              <div className="metric-label">本益比 PER</div>
              <div className="mono" style={{ fontSize: 18 }}>{fundamentals.per ?? '—'}</div>
            </div>
            <div>
              <div className="metric-label">股價淨值比 PBR</div>
              <div className="mono" style={{ fontSize: 18 }}>{fundamentals.pbr ?? '—'}</div>
            </div>
            <div>
              <div className="metric-label">殖利率</div>
              <div className="mono" style={{ fontSize: 18 }}>{fundamentals.dividend_yield != null ? `${fundamentals.dividend_yield}%` : '—'}</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="info-box" style={{ marginBottom: 24 }}>
          ℹ️ 基本面資料未顯示，可能是後端尚未設定 FINMIND_API_TOKEN，或這檔標的暫時查不到相關資料。
        </div>
      )}

      {volume_stats && (volume_stats.vol_ratio != null) && (
        <div className="chart-panel">
          <div className="chart-panel-title">量能與波動</div>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', marginTop: 10 }}>
            <div>
              <div className="metric-label">近5日均量</div>
              <div className="mono" style={{ fontSize: 16 }}>{num(Math.round(volume_stats.vol_5d))}</div>
            </div>
            <div>
              <div className="metric-label">近20日均量</div>
              <div className="mono" style={{ fontSize: 16 }}>{num(Math.round(volume_stats.vol_20d))}</div>
            </div>
            <div>
              <div className="metric-label">量比（5日/20日）</div>
              <div className="mono" style={{ fontSize: 16 }}>{volume_stats.vol_ratio.toFixed(2)}</div>
            </div>
            <div>
              <div className="metric-label">近20日平均振幅</div>
              <div className="mono" style={{ fontSize: 16 }}>{volume_stats.avg_swing_20d != null ? `${(volume_stats.avg_swing_20d * 100).toFixed(1)}%` : '—'}</div>
            </div>
          </div>
        </div>
      )}

      {institutional_daily && institutional_daily.length > 0 && (
        <div className="chart-panel">
          <div className="chart-panel-title">
            近期三大法人買賣超 <span className="badge">單位：張，正數買超、負數賣超</span>
          </div>
          <div className="table-wrap" style={{ marginTop: 8 }}>
            <table className="trades">
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>日期</th>
                  <th>外資</th>
                  <th>投信</th>
                  <th>自營</th>
                  <th>合計</th>
                </tr>
              </thead>
              <tbody>
                {[...institutional_daily].reverse().map((row) => (
                  <tr key={row.date}>
                    <td style={{ textAlign: 'left' }}>{row.date}</td>
                    <td className={row.foreign >= 0 ? 'up' : 'down'}>{signedNum(row.foreign)}</td>
                    <td className={row.trust >= 0 ? 'up' : 'down'}>{signedNum(row.trust)}</td>
                    <td className={row.dealer >= 0 ? 'up' : 'down'}>{signedNum(row.dealer)}</td>
                    <td className={row.total >= 0 ? 'up' : 'down'} style={{ fontWeight: 700 }}>{signedNum(row.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {margin_daily && margin_daily.length > 0 && (
        <div className="chart-panel">
          <div className="chart-panel-title">
            融資融券餘額 <span className="badge">單位：張</span>
          </div>
          <div className="table-wrap" style={{ marginTop: 8 }}>
            <table className="trades">
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>日期</th>
                  <th>融資餘額</th>
                  <th>較前日</th>
                  <th>融券餘額</th>
                  <th>較前日</th>
                </tr>
              </thead>
              <tbody>
                {[...margin_daily].reverse().map((row) => (
                  <tr key={row.date}>
                    <td style={{ textAlign: 'left' }}>{row.date}</td>
                    <td>{num(row.margin_balance)}</td>
                    <td className={row.margin_change > 0 ? 'up' : row.margin_change < 0 ? 'down' : undefined}>
                      {row.margin_change != null ? signedNum(row.margin_change) : '—'}
                    </td>
                    <td>{num(row.short_balance)}</td>
                    <td className={row.short_change > 0 ? 'up' : row.short_change < 0 ? 'down' : undefined}>
                      {row.short_change != null ? signedNum(row.short_change) : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="chart-panel">
        <div className="chart-panel-title">8種策略目前狀態</div>
        <div className="table-wrap" style={{ marginTop: 8 }}>
          <table className="trades">
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>策略</th>
                <th style={{ textAlign: 'left' }}>狀態</th>
                <th style={{ textAlign: 'left' }}>說明</th>
                <th>進場日</th>
                <th>進場價</th>
                <th>浮動報酬</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((s) => {
                const meta = POSITION_META[s.position] || POSITION_META.flat;
                return (
                  <tr key={s.strategy}>
                    <td style={{ textAlign: 'left' }}>{s.strategy_label}</td>
                    <td style={{ textAlign: 'left' }}>
                      {meta.cls ? <span className={`side-tag ${meta.cls}`}>{meta.label}</span> : <span style={{ color: 'var(--text-faint)' }}>{meta.label}</span>}
                    </td>
                    <td style={{ textAlign: 'left', color: 'var(--text-muted)', fontFamily: 'var(--font-ui)' }}>{s.detail}</td>
                    <td>{s.entry_date || '—'}</td>
                    <td>{s.entry_price != null ? s.entry_price.toFixed(2) : '—'}</td>
                    <td className={s.unrealized_return >= 0 ? 'up' : s.unrealized_return < 0 ? 'down' : undefined}>
                      {pct(s.unrealized_return)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
