import React from 'react';

function pct(v) {
  if (v == null) return '—';
  const s = (v * 100).toFixed(2);
  return `${v >= 0 ? '+' : ''}${s}%`;
}
function num(v) {
  if (v == null) return '—';
  return Math.round(v).toLocaleString('zh-TW');
}
function flowNum(v) {
  // 資金流向數字：加上方向箭頭 + 正負號，一起顯示
  if (v == null) return { text: '—', cls: '' };
  const arrow = v > 0 ? '▲' : v < 0 ? '▼' : '';
  const cls = v > 0 ? 'flow-up' : v < 0 ? 'flow-down' : '';
  return { text: `${arrow} ${v >= 0 ? '+' : ''}${Math.round(v).toLocaleString('zh-TW')}`, cls };
}

const POSITION_META = {
  long: { label: '偏多（模擬持有多單）', cls: 'long' },
  short: { label: '偏空（模擬持有空單）', cls: 'short' },
  flat: { label: '中性（目前空手）', cls: null },
};

export default function StockAnalysisResult({ data }) {
  if (!data) return null;
  const {
    ticker_resolved, stock_name, current_price, price_date, is_intraday,
    prev_close, prev_close_date, day_change_pct, tally, signals,
    fundamentals, institutional_daily, margin_daily, volume_stats, summary_text,
  } = data;

  const latestInst = institutional_daily && institutional_daily.length ? institutional_daily[institutional_daily.length - 1] : null;
  const latestMargin = margin_daily && margin_daily.length ? margin_daily[margin_daily.length - 1] : null;

  return (
    <div>
      <div className="panel" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', flexWrap: 'wrap', gap: 10 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>
              {ticker_resolved}
              {stock_name && <span style={{ fontSize: 15, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>{stock_name}</span>}
            </div>
            <div style={{ color: 'var(--text-faint)', fontSize: 12 }}>
              {is_intraday ? `${price_date} 盤中報價` : `${price_date} 收盤`}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div className="mono" style={{ fontSize: 26, fontWeight: 700 }}>{current_price?.toFixed(2)}</div>
            <div className={day_change_pct >= 0 ? 'up' : 'down'} style={{ fontSize: 13, fontFamily: 'var(--font-mono)' }}>
              {pct(day_change_pct)}
            </div>
            {prev_close != null && (
              <div style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 2 }}>
                昨收 {prev_close.toFixed(2)}（{prev_close_date}）
              </div>
            )}
          </div>
        </div>
      </div>

      {summary_text && (
        <div className="chart-panel">
          <div className="chart-panel-title">
            <span className="section-title-icon">📋</span>整理摘要 <span className="badge">規則統計，非AI生成</span>
          </div>
          <p style={{ color: 'var(--text)', fontSize: 13.5, lineHeight: 1.9, marginTop: 8 }}>{summary_text}</p>
        </div>
      )}

      <div className="chart-panel">
        <div className="chart-panel-title"><span className="section-title-icon">🎯</span>技術面總覽</div>
        <div className="stat-row">
          <div className="stat-box">
            <div className="stat-box-label">偏多策略數</div>
            <div className="stat-box-value up">{tally.bullish}</div>
          </div>
          <div className="stat-box">
            <div className="stat-box-label">偏空策略數</div>
            <div className="stat-box-value down">{tally.bearish}</div>
          </div>
          <div className="stat-box">
            <div className="stat-box-label">中性策略數</div>
            <div className="stat-box-value">{tally.neutral}</div>
          </div>
          <div className="stat-box">
            <div className="stat-box-label">共檢視策略</div>
            <div className="stat-box-value" style={{ color: 'var(--gold)' }}>{signals.length}</div>
          </div>
        </div>
      </div>

      {fundamentals && (
        <div className="chart-panel">
          <div className="chart-panel-title"><span className="section-title-icon">💹</span>基本面（FinMind）</div>
          <div className="stat-row">
            <div className="stat-box">
              <div className="stat-box-label">本益比 PER</div>
              <div className="stat-box-value">{fundamentals.per ?? '—'}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">股價淨值比 PBR</div>
              <div className="stat-box-value">{fundamentals.pbr ?? '—'}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">殖利率</div>
              <div className="stat-box-value">{fundamentals.dividend_yield != null ? `${fundamentals.dividend_yield}%` : '—'}</div>
            </div>
          </div>
        </div>
      )}

      {!fundamentals && (
        <div className="info-box" style={{ marginBottom: 24 }}>
          ℹ️ 基本面資料未顯示，可能是後端尚未設定 FINMIND_API_TOKEN，或這檔標的暫時查不到相關資料。
        </div>
      )}

      {volume_stats && volume_stats.vol_ratio != null && (
        <div className="chart-panel">
          <div className="chart-panel-title"><span className="section-title-icon">📈</span>量能與波動</div>
          <div className="stat-row">
            <div className="stat-box">
              <div className="stat-box-label">近5日均量</div>
              <div className="stat-box-value" style={{ fontSize: 16 }}>{num(volume_stats.vol_5d)}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">近20日均量</div>
              <div className="stat-box-value" style={{ fontSize: 16 }}>{num(volume_stats.vol_20d)}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">量比（5日/20日）</div>
              <div className="stat-box-value" style={{ fontSize: 16 }}>{volume_stats.vol_ratio.toFixed(2)}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">近20日平均振幅</div>
              <div className="stat-box-value" style={{ fontSize: 16 }}>
                {volume_stats.avg_swing_20d != null ? `${(volume_stats.avg_swing_20d * 100).toFixed(1)}%` : '—'}
              </div>
            </div>
          </div>
        </div>
      )}

      {latestInst && (
        <div className="chart-panel">
          <div className="chart-panel-title">
            <span className="section-title-icon">🏦</span>三大法人買賣超 <span className="badge">{latestInst.date}</span>
          </div>
          <div className="stat-row">
            <div className="stat-box">
              <div className="stat-box-label">外資</div>
              <div className={`stat-box-value ${flowNum(latestInst.foreign).cls}`}>{flowNum(latestInst.foreign).text}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">投信</div>
              <div className={`stat-box-value ${flowNum(latestInst.trust).cls}`}>{flowNum(latestInst.trust).text}</div>
            </div>
            <div className="stat-box">
              <div className="stat-box-label">自營商</div>
              <div className={`stat-box-value ${flowNum(latestInst.dealer).cls}`}>{flowNum(latestInst.dealer).text}</div>
            </div>
          </div>
          <div className="stat-inline-row">
            <span className="stat-inline-label">三大法人合計</span>
            <span className={`stat-inline-value ${flowNum(latestInst.total).cls}`}>{flowNum(latestInst.total).text} 張</span>
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--text-faint)', marginTop: 4 }}>單位：張。正數買超（綠）、負數賣超（紅），收盤後公布</div>

          {institutional_daily.length > 1 && (
            <details className="collapse-detail">
              <summary>查看近{institutional_daily.length}日詳細數字</summary>
              <div className="table-wrap">
                <table className="trades">
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>日期</th>
                      <th>外資</th><th>投信</th><th>自營</th><th>合計</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...institutional_daily].reverse().map((row) => (
                      <tr key={row.date}>
                        <td style={{ textAlign: 'left' }}>{row.date}</td>
                        <td className={flowNum(row.foreign).cls}>{flowNum(row.foreign).text}</td>
                        <td className={flowNum(row.trust).cls}>{flowNum(row.trust).text}</td>
                        <td className={flowNum(row.dealer).cls}>{flowNum(row.dealer).text}</td>
                        <td className={flowNum(row.total).cls} style={{ fontWeight: 700 }}>{flowNum(row.total).text}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </div>
      )}

      {latestMargin && (
        <div className="chart-panel">
          <div className="chart-panel-title">
            <span className="section-title-icon">💰</span>融資融券 <span className="badge">{latestMargin.date}</span>
          </div>
          <div className="stat-inline-row">
            <span className="stat-inline-label">融資餘額</span>
            <span className="stat-inline-value">{num(latestMargin.margin_balance)} 張</span>
          </div>
          <div className="stat-inline-row">
            <span className="stat-inline-label">融資較前日</span>
            <span className={`stat-inline-value ${flowNum(latestMargin.margin_change).cls}`}>{flowNum(latestMargin.margin_change).text} 張</span>
          </div>
          <div className="stat-inline-row">
            <span className="stat-inline-label">融券餘額</span>
            <span className="stat-inline-value">{num(latestMargin.short_balance)} 張</span>
          </div>
          <div className="stat-inline-row">
            <span className="stat-inline-label">融券較前日</span>
            <span className={`stat-inline-value ${flowNum(latestMargin.short_change).cls}`}>{flowNum(latestMargin.short_change).text} 張</span>
          </div>

          {margin_daily.length > 1 && (
            <details className="collapse-detail">
              <summary>查看近{margin_daily.length}日詳細數字</summary>
              <div className="table-wrap">
                <table className="trades">
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>日期</th>
                      <th>融資餘額</th><th>較前日</th><th>融券餘額</th><th>較前日</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...margin_daily].reverse().map((row) => (
                      <tr key={row.date}>
                        <td style={{ textAlign: 'left' }}>{row.date}</td>
                        <td>{num(row.margin_balance)}</td>
                        <td className={flowNum(row.margin_change).cls}>{flowNum(row.margin_change).text}</td>
                        <td>{num(row.short_balance)}</td>
                        <td className={flowNum(row.short_change).cls}>{flowNum(row.short_change).text}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </div>
      )}

      <div className="chart-panel">
        <div className="chart-panel-title"><span className="section-title-icon">📊</span>各策略目前狀態</div>
        <div className="table-wrap" style={{ marginTop: 8 }}>
          <table className="trades">
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>策略</th>
                <th style={{ textAlign: 'left' }}>週期</th>
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
                    <td style={{ textAlign: 'left', color: s.interval === '1H' ? 'var(--cyan)' : 'var(--text-faint)', fontSize: 11.5 }}>
                      {s.interval}
                    </td>
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
