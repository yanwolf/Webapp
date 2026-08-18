import React, { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { useRemeasureKey } from '../useElementWidth';
import { downsampleForChart } from '../downsample';

const TICK_STYLE = { fill: 'var(--text-faint)', fontSize: 11 };

function fmtMoney(v) {
  if (v == null) return '';
  return v.toLocaleString('zh-TW', { maximumFractionDigits: 0 });
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div style={{
      background: '#191c21', border: '1px solid #262a31', borderRadius: 8,
      padding: '10px 12px', fontSize: 12, fontFamily: 'var(--font-mono)', color: '#e9e7e1',
    }}>
      <div style={{ marginBottom: 6, color: '#8b8f98', fontFamily: 'var(--font-ui)' }}>{label}</div>
      <div>權益 {fmtMoney(payload[0].value)}</div>
    </div>
  );
}

export default function EquityChart({ equitySeries }) {
  const chartData = useMemo(() => downsampleForChart(equitySeries, 600), [equitySeries]);
  const everyNth = Math.max(1, Math.floor(chartData.length / 8));
  const remeasureKey = useRemeasureKey();

  return (
    <div className="chart-panel">
      <div className="chart-panel-title">權益曲線</div>
      <div className="legend-row">
        <span className="legend-item"><span className="legend-dot" style={{ background: '#d4b06a' }} />帳戶淨值</span>
      </div>
      <ResponsiveContainer key={remeasureKey} width="100%" height={220}>
        <AreaChart data={chartData} margin={{ top: 4, right: 12, left: -8, bottom: 4 }}>
          <defs>
            <linearGradient id="equityFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#d4b06a" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#d4b06a" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#1d2026" vertical={false} />
          <XAxis dataKey="date" tick={TICK_STYLE} axisLine={{ stroke: '#262a31' }} tickLine={false} interval={everyNth} minTickGap={40} />
          <YAxis tick={TICK_STYLE} axisLine={{ stroke: '#262a31' }} tickLine={false} domain={['auto', 'auto']} width={64}
                 tickFormatter={fmtMoney} />
          <Tooltip content={<CustomTooltip />} />
          <Area type="monotone" dataKey="equity" stroke="#d4b06a" strokeWidth={1.4} fill="url(#equityFill)" isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
