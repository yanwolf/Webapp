import React from 'react';
import {
  ComposedChart, Line, Bar, ReferenceLine, XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts';
import { useElementWidth } from '../useElementWidth';

const TICK_STYLE = { fill: 'var(--text-faint)', fontSize: 11 };

function RsiTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const row = payload[0].payload;
  return (
    <div style={{
      background: '#191c21', border: '1px solid #262a31', borderRadius: 8,
      padding: '10px 12px', fontSize: 12, fontFamily: 'var(--font-mono)', color: '#e9e7e1',
    }}>
      <div style={{ marginBottom: 6, color: '#8b8f98', fontFamily: 'var(--font-ui)' }}>{label}</div>
      <div>RSI {row.rsi?.toFixed(1)}</div>
    </div>
  );
}

function MacdTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const row = payload[0].payload;
  return (
    <div style={{
      background: '#191c21', border: '1px solid #262a31', borderRadius: 8,
      padding: '10px 12px', fontSize: 12, fontFamily: 'var(--font-mono)', color: '#e9e7e1',
    }}>
      <div style={{ marginBottom: 6, color: '#8b8f98', fontFamily: 'var(--font-ui)' }}>{label}</div>
      <div style={{ color: '#ec5f5f' }}>MACD {row.macd?.toFixed(3)}</div>
      <div style={{ color: '#d4b06a' }}>訊號線 {row.macd_signal?.toFixed(3)}</div>
      <div>柱狀 {row.macd_hist?.toFixed(3)}</div>
    </div>
  );
}

export function RsiChart({ priceSeries, oversold = 30, overbought = 70 }) {
  const everyNth = Math.max(1, Math.floor(priceSeries.length / 8));
  const [boxRef, boxWidth] = useElementWidth();
  return (
    <div className="chart-panel">
      <div className="chart-panel-title">RSI 相對強弱指標</div>
      <div className="legend-row">
        <span className="legend-item"><span className="legend-dot" style={{ background: '#6ee7df' }} />RSI</span>
        <span className="legend-item"><span className="legend-dot" style={{ background: '#ec5f5f' }} />超買/超賣線</span>
      </div>
      <div ref={boxRef} style={{ width: '100%' }}>
        {boxWidth > 0 && (
        <ComposedChart width={boxWidth} height={220} data={priceSeries} margin={{ top: 4, right: 12, left: -8, bottom: 4 }}>
          <CartesianGrid stroke="#1d2026" vertical={false} />
          <XAxis dataKey="date" tick={TICK_STYLE} axisLine={{ stroke: '#262a31' }} tickLine={false} interval={everyNth} minTickGap={40} />
          <YAxis tick={TICK_STYLE} axisLine={{ stroke: '#262a31' }} tickLine={false} domain={[0, 100]} width={40} />
          <Tooltip content={<RsiTooltip />} />
          <ReferenceLine y={overbought} stroke="#ec5f5f" strokeDasharray="4 3" strokeOpacity={0.6} />
          <ReferenceLine y={oversold} stroke="#29b389" strokeDasharray="4 3" strokeOpacity={0.6} />
          <ReferenceLine y={50} stroke="#565a63" strokeOpacity={0.4} />
          <Line dataKey="rsi" stroke="#6ee7df" strokeWidth={1.3} dot={false} isAnimationActive={false} />
        </ComposedChart>
        )}
      </div>
    </div>
  );
}

export function MacdChart({ priceSeries }) {
  const everyNth = Math.max(1, Math.floor(priceSeries.length / 8));
  const [boxRef, boxWidth] = useElementWidth();
  const data = priceSeries.map((d) => ({ ...d, hist_pos: d.macd_hist >= 0 ? d.macd_hist : 0, hist_neg: d.macd_hist < 0 ? d.macd_hist : 0 }));
  return (
    <div className="chart-panel">
      <div className="chart-panel-title">MACD 動量指標</div>
      <div className="legend-row">
        <span className="legend-item"><span className="legend-dot" style={{ background: '#ec5f5f' }} />MACD</span>
        <span className="legend-item"><span className="legend-dot" style={{ background: '#d4b06a' }} />訊號線</span>
        <span className="legend-item"><span className="legend-dot" style={{ background: '#6ee7df' }} />柱狀圖</span>
      </div>
      <div ref={boxRef} style={{ width: '100%' }}>
        {boxWidth > 0 && (
        <ComposedChart width={boxWidth} height={220} data={data} margin={{ top: 4, right: 12, left: -8, bottom: 4 }}>
          <CartesianGrid stroke="#1d2026" vertical={false} />
          <XAxis dataKey="date" tick={TICK_STYLE} axisLine={{ stroke: '#262a31' }} tickLine={false} interval={everyNth} minTickGap={40} />
          <YAxis tick={TICK_STYLE} axisLine={{ stroke: '#262a31' }} tickLine={false} domain={['auto', 'auto']} width={54} />
          <Tooltip content={<MacdTooltip />} />
          <ReferenceLine y={0} stroke="#565a63" strokeOpacity={0.5} />
          <Bar dataKey="hist_pos" fill="#ec5f5f" fillOpacity={0.5} isAnimationActive={false} />
          <Bar dataKey="hist_neg" fill="#29b389" fillOpacity={0.5} isAnimationActive={false} />
          <Line dataKey="macd" stroke="#ec5f5f" strokeWidth={1.2} dot={false} isAnimationActive={false} />
          <Line dataKey="macd_signal" stroke="#d4b06a" strokeWidth={1.2} dot={false} isAnimationActive={false} />
        </ComposedChart>
        )}
      </div>
    </div>
  );
}
