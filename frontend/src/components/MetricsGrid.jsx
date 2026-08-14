import React from 'react';

function colorFor(label, value) {
  if (typeof value !== 'string') return 'var(--text)';
  if (label.includes('報酬') || label.includes('夏普') || label.includes('獲利因子')) {
    if (value.startsWith('-')) return 'var(--down)';
    if (value !== 'N/A') return 'var(--up)';
  }
  if (label.includes('回撤')) return 'var(--down)';
  return 'var(--text)';
}

export default function MetricsGrid({ metrics }) {
  if (!metrics) return null;
  const entries = Object.entries(metrics);

  return (
    <div className="metrics-grid">
      {entries.map(([label, value]) => (
        <div className="metric-card" key={label}>
          <div className="metric-label">{label.replace(/_/g, ' ')}</div>
          <div className="metric-value" style={{ color: colorFor(label, value) }}>
            {String(value)}
          </div>
        </div>
      ))}
    </div>
  );
}
