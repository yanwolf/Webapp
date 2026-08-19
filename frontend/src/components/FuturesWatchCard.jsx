import React from 'react';

const BLADE_META = {
  fast: { title: '張飛 20MA', icon: '⚔️' },
  mid: { title: '關羽 60MA', icon: '⚔️' },
  slow: { title: '劉備 240MA', icon: '⚔️' },
};

function num(v) {
  if (v == null) return '—';
  return v.toLocaleString('zh-TW', { maximumFractionDigits: 2 });
}

export default function FuturesWatchCard({ label, snapshot }) {
  if (!snapshot || snapshot.error) {
    return (
      <div className="chart-panel">
        <div className="chart-panel-title">⚔️ {label}</div>
        <div className="info-box" style={{ marginTop: 10 }}>
          ℹ️ {snapshot?.error || '暫時無法取得資料'}
        </div>
      </div>
    );
  }

  const blades = [
    { key: 'fast', ma: snapshot.fast_ma, status: snapshot.fast_status },
    { key: 'mid', ma: snapshot.mid_ma, status: snapshot.mid_status },
    { key: 'slow', ma: snapshot.slow_ma, status: snapshot.slow_status },
  ];

  const alignmentCls = snapshot.alignment === '多方排列' ? 'up' : snapshot.alignment === '空方排列' ? 'down' : undefined;

  return (
    <div className="chart-panel">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
        <div className="chart-panel-title" style={{ marginBottom: 0 }}>⚔️ {label}</div>
        <div className="mono" style={{ fontSize: 22, fontWeight: 700 }}>{num(snapshot.price)}</div>
      </div>
      <div style={{ fontSize: 11.5, color: 'var(--text-faint)', marginBottom: 14 }}>{snapshot.price_time}（1H・{snapshot.data_source}）</div>

      <div className="stat-row">
        {blades.map((b) => (
          <div className="stat-box" key={b.key} style={{ textAlign: 'center' }}>
            <div className="stat-box-label">{BLADE_META[b.key].title}</div>
            <div className={`stat-box-value ${b.status === '站上' ? 'up' : b.status === '跌破' ? 'down' : ''}`} style={{ fontSize: 15 }}>
              {b.status}
            </div>
            <div className="mono" style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 4 }}>{num(b.ma)}</div>
          </div>
        ))}
      </div>

      <div className="stat-inline-row">
        <span className="stat-inline-label">多空分水嶺（關羽60MA）</span>
        <span className="stat-inline-value">
          {num(snapshot.mid_ma)}　
          <span className={snapshot.watershed_diff >= 0 ? 'up' : 'down'}>
            {snapshot.watershed_diff >= 0 ? '+' : ''}{num(snapshot.watershed_diff)}點
          </span>
        </span>
      </div>
      <div className="stat-inline-row">
        <span className="stat-inline-label">整體排列</span>
        <span className={`side-tag ${alignmentCls === 'up' ? 'long' : alignmentCls === 'down' ? 'short' : ''}`}>
          {snapshot.alignment}
        </span>
      </div>
    </div>
  );
}
