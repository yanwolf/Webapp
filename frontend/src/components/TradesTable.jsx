import React from 'react';

function pct(v) {
  if (v == null) return '—';
  return `${(v * 100).toFixed(2)}%`;
}
function money(v) {
  if (v == null) return '—';
  return v.toLocaleString('zh-TW', { maximumFractionDigits: 0 });
}

export default function TradesTable({ trades }) {
  return (
    <div className="chart-panel">
      <div className="chart-panel-title">
        逐筆交易明細 <span className="badge">共 {trades.length} 筆</span>
      </div>
      {trades.length === 0 ? (
        <div className="empty-state" style={{ marginTop: 8 }}>此區間內策略未產生任何交易訊號</div>
      ) : (
        <div className="table-wrap">
          <table className="trades">
            <thead>
              <tr>
                <th>方向</th>
                <th>進場日</th>
                <th>進場價</th>
                <th>出場日</th>
                <th>出場價</th>
                <th>損益</th>
                <th>報酬率</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((t, i) => (
                <tr key={i}>
                  <td style={{ textAlign: 'left' }}>
                    <span className={`side-tag ${t.side}`}>{t.side === 'long' ? '做多' : '做空'}</span>
                  </td>
                  <td>{t.entry_date}</td>
                  <td>{t.entry_price?.toFixed(2)}</td>
                  <td>{t.exit_date}</td>
                  <td>{t.exit_price?.toFixed(2)}</td>
                  <td className={t.pnl >= 0 ? 'up' : 'down'}>{money(t.pnl)}</td>
                  <td className={t.ret >= 0 ? 'up' : 'down'}>{pct(t.ret)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
