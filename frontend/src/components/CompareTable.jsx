import React from 'react';

function pct(v) {
  if (v == null) return '—';
  return `${(v * 100).toFixed(2)}%`;
}
function num(v) {
  if (v == null) return '—';
  return v.toFixed(2);
}

export default function CompareTable({ data }) {
  if (!data) return null;
  const { results, buy_hold_cagr, ticker_resolved, interval, date_range, style_label } = data;

  return (
    <div className="chart-panel">
      <div className="chart-panel-title">
        策略績效排名
        <span className="badge">{ticker_resolved} · {style_label} · {interval} · {date_range[0]} ~ {date_range[1]}</span>
      </div>
      <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 0, marginBottom: 16 }}>
        依年化報酬率(CAGR)由高到低排序。「贏過買進持有」代表這個策略在這段時間、這檔標的上，
        報酬率有超過單純買進抱著不動（買進持有 CAGR = {pct(buy_hold_cagr)}）。
      </p>
      <div className="table-wrap">
        <table className="trades">
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>排名</th>
              <th style={{ textAlign: 'left' }}>策略</th>
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
              <tr key={r.strategy}>
                <td style={{ textAlign: 'left', color: 'var(--text-faint)' }}>{i + 1}</td>
                <td style={{ textAlign: 'left' }}>
                  {r.strategy_label}
                  {r.strategy === 'buy_hold' && <span className="badge" style={{ marginLeft: 6 }}>基準</span>}
                </td>
                {r.metrics ? (
                  <>
                    <td className={r.metrics.cagr >= 0 ? 'up' : 'down'}>{pct(r.metrics.cagr)}</td>
                    <td>{num(r.metrics.sharpe)}</td>
                    <td className="down">{pct(r.metrics.max_dd)}</td>
                    <td>{pct(r.metrics.win_rate)}</td>
                    <td>{r.metrics.n_trades}</td>
                    <td>
                      {r.strategy === 'buy_hold' ? (
                        <span style={{ color: 'var(--text-faint)' }}>—</span>
                      ) : r.beats_buy_hold ? (
                        <span className="side-tag long">✓ 贏</span>
                      ) : (
                        <span className="side-tag short">✗ 輸</span>
                      )}
                    </td>
                  </>
                ) : (
                  <td colSpan={6} style={{ color: 'var(--text-faint)' }}>{r.error}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
