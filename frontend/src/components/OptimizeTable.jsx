import React from 'react';

function pct(v) {
  if (v == null) return '—';
  return `${(v * 100).toFixed(2)}%`;
}
function num(v) {
  if (v == null) return '—';
  return v.toFixed(2);
}
function fmtParamVal(v) {
  if (typeof v === 'number') return Number.isInteger(v) ? v : v.toFixed(2);
  return String(v);
}

export default function OptimizeTable({ data }) {
  if (!data) return null;
  const {
    results, buy_hold_metrics, param_keys, param_labels,
    ticker_resolved, strategy_label, interval, date_range,
    total_combos, tested_combos, skipped_insufficient_data,
  } = data;

  return (
    <div className="chart-panel">
      <div className="chart-panel-title">
        參數最佳化結果
        <span className="badge">{ticker_resolved} · {strategy_label} · {interval} · {date_range[0]} ~ {date_range[1]}</span>
      </div>
      <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 0, marginBottom: 14 }}>
        共測試 {tested_combos} / {total_combos} 組參數組合
        {skipped_insufficient_data > 0 && `（${skipped_insufficient_data} 組因資料量不足被跳過）`}，
        依年化報酬率(CAGR)排序，只顯示前 {results.length} 名。
        買進持有基準 CAGR = {pct(buy_hold_metrics?.cagr)}。
      </p>
      {results.length === 0 ? (
        <div className="empty-state">沒有找到任何有效的參數組合，可能是資料量不足，試著拉長回測區間</div>
      ) : (
        <div className="table-wrap">
          <table className="trades">
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>排名</th>
                {param_keys.map((k) => (
                  <th key={k} style={{ textAlign: 'left' }}>{param_labels[k] || k}</th>
                ))}
                <th>CAGR</th>
                <th>Sharpe</th>
                <th>最大回撤</th>
                <th>勝率</th>
                <th>交易次數</th>
                <th>贏過買進持有</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i} style={i === 0 ? { background: 'rgba(212,176,106,0.06)' } : undefined}>
                  <td style={{ textAlign: 'left', color: i === 0 ? 'var(--gold)' : 'var(--text-faint)', fontWeight: i === 0 ? 700 : 400 }}>
                    {i === 0 ? '🏆 1' : i + 1}
                  </td>
                  {param_keys.map((k) => (
                    <td key={k} style={{ textAlign: 'left' }}>{fmtParamVal(r.params[k])}</td>
                  ))}
                  {r.metrics ? (
                    <>
                      <td className={r.metrics.cagr >= 0 ? 'up' : 'down'}>{pct(r.metrics.cagr)}</td>
                      <td>{num(r.metrics.sharpe)}</td>
                      <td className="down">{pct(r.metrics.max_dd)}</td>
                      <td>{pct(r.metrics.win_rate)}</td>
                      <td>{r.metrics.n_trades}</td>
                      <td>
                        {r.beats_buy_hold ? (
                          <span className="side-tag long">✓ 贏</span>
                        ) : (
                          <span className="side-tag short">✗ 輸</span>
                        )}
                      </td>
                    </>
                  ) : (
                    <td colSpan={6} style={{ color: 'var(--text-faint)' }}>無法計算</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
