import React, { useMemo } from 'react';
import {
  ComposedChart, Area, Line, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';

const TICK_STYLE = { fill: 'var(--text-faint)', fontSize: 11 };

function Triangle({ cx, cy, up, color }) {
  if (cx == null || cy == null) return null;
  const size = 5.5;
  const points = up
    ? `${cx},${cy - size} ${cx - size},${cy + size} ${cx + size},${cy + size}`
    : `${cx},${cy + size} ${cx - size},${cy - size} ${cx + size},${cy - size}`;
  return <polygon points={points} fill={color} stroke="#08090b" strokeWidth={0.6} />;
}

function BollingerTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const row = payload[0].payload;
  return (
    <div style={{
      background: '#191c21', border: '1px solid #262a31', borderRadius: 8,
      padding: '10px 12px', fontSize: 12, fontFamily: 'var(--font-mono)', color: '#e9e7e1',
    }}>
      <div style={{ marginBottom: 6, color: '#8b8f98', fontFamily: 'var(--font-ui)' }}>{label}</div>
      <div>收盤 {row.close?.toFixed(2)}</div>
      <div style={{ color: '#d4b06a' }}>中軌 {row.mid?.toFixed(2)}</div>
      <div style={{ color: '#6ee7df' }}>上軌 {row.upper?.toFixed(2)}</div>
      <div style={{ color: '#6ee7df' }}>下軌 {row.lower?.toFixed(2)}</div>
    </div>
  );
}

function MaTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  const row = payload[0].payload;
  return (
    <div style={{
      background: '#191c21', border: '1px solid #262a31', borderRadius: 8,
      padding: '10px 12px', fontSize: 12, fontFamily: 'var(--font-mono)', color: '#e9e7e1',
    }}>
      <div style={{ marginBottom: 6, color: '#8b8f98', fontFamily: 'var(--font-ui)' }}>{label}</div>
      <div>收盤 {row.close?.toFixed(2)}</div>
      <div style={{ color: '#ec5f5f' }}>快刀 {row.ema_fast?.toFixed(2)}</div>
      <div style={{ color: '#d4b06a' }}>中刀 {row.ema_mid?.toFixed(2)}</div>
      <div style={{ color: '#6ee7df' }}>慢刀 {row.ema_slow?.toFixed(2)}</div>
    </div>
  );
}

export default function PriceChart({ priceSeries, trades, strategy = 'bollinger' }) {
  const isMa = strategy === 'ma3';

  const data = useMemo(
    () => priceSeries.map((d) => (isMa ? { ...d } : { ...d, band: [d.lower, d.upper] })),
    [priceSeries, isMa]
  );

  const { longEntries, longExits, shortEntries, shortExits } = useMemo(() => {
    const byDate = new Map(data.map((d) => [d.date, d]));
    const longEntries = [], longExits = [], shortEntries = [], shortExits = [];
    (trades || []).forEach((t) => {
      const push = (arr, dateStr, price) => {
        if (byDate.has(dateStr)) arr.push({ date: dateStr, val: price });
      };
      if (t.side === 'long') {
        push(longEntries, t.entry_date, t.entry_price);
        push(longExits, t.exit_date, t.exit_price);
      } else {
        push(shortEntries, t.entry_date, t.entry_price);
        push(shortExits, t.exit_date, t.exit_price);
      }
    });
    return { longEntries, longExits, shortEntries, shortExits };
  }, [data, trades]);

  const everyNth = Math.max(1, Math.floor(data.length / 8));

  return (
    <div className="chart-panel">
      <div className="chart-panel-title">
        {isMa ? '價格與均線三刀流' : '價格與布林通道'}
        <span className="badge">{isMa ? 'EMA 快/中/慢三線' : 'SMA20 · ±2σ'}</span>
      </div>
      <div className="legend-row">
        <span className="legend-item"><span className="legend-dot" style={{ background: '#e9e7e1' }} />收盤價</span>
        {isMa ? (
          <>
            <span className="legend-item"><span className="legend-dot" style={{ background: '#ec5f5f' }} />快刀</span>
            <span className="legend-item"><span className="legend-dot" style={{ background: '#d4b06a' }} />中刀</span>
            <span className="legend-item"><span className="legend-dot" style={{ background: '#6ee7df' }} />慢刀</span>
          </>
        ) : (
          <>
            <span className="legend-item"><span className="legend-dot" style={{ background: '#d4b06a' }} />中軌</span>
            <span className="legend-item"><span className="legend-dot" style={{ background: '#6ee7df' }} />上下軌</span>
          </>
        )}
        <span className="legend-item"><span className="legend-tri" style={{ borderBottom: '8px solid #ec5f5f' }} />做多進場</span>
        <span className="legend-item"><span className="legend-tri" style={{ borderTop: '8px solid #29b389' }} />做空進場</span>
        <span className="legend-item"><span className="legend-tri" style={{ borderTop: '8px solid #8b8f98' }} />出場</span>
      </div>
      <ResponsiveContainer width="100%" height={380}>
        <ComposedChart data={data} margin={{ top: 4, right: 12, left: -8, bottom: 4 }}>
          <CartesianGrid stroke="#1d2026" vertical={false} />
          <XAxis
            dataKey="date"
            tick={TICK_STYLE}
            axisLine={{ stroke: '#262a31' }}
            tickLine={false}
            interval={everyNth}
            minTickGap={40}
          />
          <YAxis
            tick={TICK_STYLE}
            axisLine={{ stroke: '#262a31' }}
            tickLine={false}
            domain={['auto', 'auto']}
            width={54}
          />
          <Tooltip content={isMa ? <MaTooltip /> : <BollingerTooltip />} />

          {isMa ? (
            <>
              <Line dataKey="ema_slow" stroke="#6ee7df" strokeWidth={1.1} dot={false} strokeOpacity={0.75} isAnimationActive={false} />
              <Line dataKey="ema_mid" stroke="#d4b06a" strokeWidth={1.1} dot={false} isAnimationActive={false} />
              <Line dataKey="ema_fast" stroke="#ec5f5f" strokeWidth={1.1} dot={false} isAnimationActive={false} />
              <Line dataKey="close" stroke="#e9e7e1" strokeWidth={1.2} dot={false} isAnimationActive={false} />
            </>
          ) : (
            <>
              <Area dataKey="band" stroke="none" fill="#6ee7df" fillOpacity={0.06} isAnimationActive={false} />
              <Line dataKey="upper" stroke="#6ee7df" strokeWidth={0.9} dot={false} strokeOpacity={0.55} isAnimationActive={false} />
              <Line dataKey="lower" stroke="#6ee7df" strokeWidth={0.9} dot={false} strokeOpacity={0.55} isAnimationActive={false} />
              <Line dataKey="mid" stroke="#d4b06a" strokeWidth={1.1} dot={false} isAnimationActive={false} />
              <Line dataKey="close" stroke="#e9e7e1" strokeWidth={1.2} dot={false} isAnimationActive={false} />
            </>
          )}

          <Scatter data={longEntries} dataKey="val" shape={(p) => <Triangle {...p} up color="#ec5f5f" />} isAnimationActive={false} />
          <Scatter data={shortEntries} dataKey="val" shape={(p) => <Triangle {...p} up={false} color="#29b389" />} isAnimationActive={false} />
          <Scatter data={longExits} dataKey="val" shape={(p) => <Triangle {...p} up={false} color="#8b8f98" />} isAnimationActive={false} />
          <Scatter data={shortExits} dataKey="val" shape={(p) => <Triangle {...p} up color="#8b8f98" />} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
