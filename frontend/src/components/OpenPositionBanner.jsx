import React from 'react';

function pct(v) {
  if (v == null) return '—';
  const s = (v * 100).toFixed(2);
  return `${v >= 0 ? '+' : ''}${s}%`;
}

export default function OpenPositionBanner({ position }) {
  if (!position) return null;
  const isLong = position.side === 'long';
  const cls = position.unrealized_return >= 0 ? 'up' : 'down';

  return (
    <div
      className="panel"
      style={{
        marginBottom: 24,
        border: `1px solid ${isLong ? 'rgba(236,95,95,0.35)' : 'rgba(41,179,137,0.35)'}`,
        background: isLong ? 'rgba(236,95,95,0.05)' : 'rgba(41,179,137,0.05)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className={`side-tag ${isLong ? 'long' : 'short'}`}>
            {isLong ? '目前持有多單' : '目前持有空單'}
          </span>
          <span style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
            {position.entry_date} 進場 @ {position.entry_price?.toFixed(2)}
          </span>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: 11.5, color: 'var(--text-faint)' }}>目前價 {position.current_price?.toFixed(2)}</div>
          <div className={cls} style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 700 }}>
            {pct(position.unrealized_return)}
          </div>
        </div>
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 8 }}>
        這筆部位還沒出場，不會出現在下面的交易明細表裡（交易明細只列已經完結的交易）
      </div>
    </div>
  );
}
