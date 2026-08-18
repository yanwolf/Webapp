import React, { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { useRemeasureKey } from '../useElementWidth';
import { downsampleForChart } from '../downsample';
import { toTs, formatTick } from '../chartTime';

const TICK_STYLE = { fill: 'var(--text-faint)', fontSize: 11 };

function fmtMoney(v) {
  if (v == null) return '';
  return v.toLocaleString('zh-TW', { maximumFractionDigits: 0 });
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;
  const row = payload[0].payload;
  return (
    <div style={{
      background: '#191c21', border: '1px solid #262a31', borderRadius: 8,
      padding: '10px 12px', fontSize: 12, fontFamily: 'var(--font-mono)', color: '#e9e7e1',
    }}>
      <div style={{ marginBottom: 6, color: '#8b8f98', fontFamily: 'var(--font-ui)' }}>{row.date}</div>
      <div>權益 {fmtMoney(row.equity)}</div>
    </div>
  );
}

export default function EquityChart({ equitySeries }) {
  const hasTime = useMemo(() => (equitySeries[0]?.date || '').includes(' '), [equitySeries]);
  const withTs = useMemo(() => equitySeries.map((d) => ({ ...d, ts: toTs(d.date) })), [equitySeries]);
  const chartData = useMemo(() => downsampleForChart(withTs, 600), [withTs]);
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
          <XAxis
            dataKey="ts"
            type="number"
            domain={['dataMin', 'dataMax']}
            tick={TICK_STYLE}
            axisLine={{ stroke: '#262a31' }}
            tickLine={false}
            tickFormatter={(ts) => formatTick(ts, hasTime)}
            minTickGap={40}
          />
          <YAxis tick={TICK_STYLE} axisLine={{ stroke: '#262a31' }} tickLine={false} domain={['auto', 'auto']} width={64}
                 tickFormatter={fmtMoney} />
          <Tooltip content={<CustomTooltip />} />
          <Area type="monotone" dataKey="equity" stroke="#d4b06a" strokeWidth={1.4} fill="url(#equityFill)" isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
