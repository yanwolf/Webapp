import React, { useMemo } from 'react';
import {
  ComposedChart, Area, Line, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';

const TICK_STYLE = { fill: 'var(--text-faint)', fontSize: 11 };

const OVERLAY_COLORS = {
  mid: '#d4b06a', upper: '#6ee7df', lower: '#6ee7df',
  ema_fast: '#ec5f5f', ema_mid: '#d4b06a', ema_slow: '#6ee7df',
  ma_fast: '#ec5f5f', ma_slow: '#6ee7df',
  donch_upper_entry: '#6ee7df', donch_lower_entry: '#6ee7df',
  atr_mid: '#d4b06a', atr_upper: '#6ee7df', atr_lower: '#6ee7df',
};
const OVERLAY_LABELS = {
  mid: '中軌', upper: '上軌', lower: '下軌',
  ema_fast: '快刀', ema_mid: '中刀', ema_slow: '慢刀',
  ma_fast: '快線', ma_slow: '慢線',
  donch_upper_entry: '通道上緣', donch_lower_entry: '通道下緣',
  atr_mid: '中軌', atr_upper: '通道上緣', atr_lower: '通道下緣',
};

function Triangle({ cx, cy, up, color }) {
  if (cx == null || cy == null) return null;
  const size = 5.5;
  const points = up
    ? `${cx},${cy - size} ${cx - size},${cy + size} ${cx + size},${cy + size}`
    : `${cx},${cy + size} ${cx - size},${cy - size} ${cx + size},${cy - size}`;
  return <polygon points={points} fill={color} stroke="#08090b" strokeWidth={0.6} />;
}

function makeTooltip(overlayKeys) {
  return function CustomTooltip({ active, payload, label }) {
    if (!active || !payload || !payload.length) return null;
    const row = payload[0].payload;
    return (
      <div style={{
        background: '#191c21', border: '1px solid #262a31', borderRadius: 8,
        padding: '10px 12px', fontSize: 12, fontFamily: 'var(--font-mono)', color: '#e9e7e1',
      }}>
        <div style={{ marginBottom: 6, color: '#8b8f98', fontFamily: 'var(--font-ui)' }}>{label}</div>
        <div>收盤 {row.close?.toFixed(2)}</div>
        {overlayKeys.map((k) => (
          <div key={k} style={{ color: OVERLAY_COLORS[k] || '#e9e7e1' }}>
            {OVERLAY_LABELS[k] || k} {row[k] != null ? row[k].toFixed(2) : '—'}
          </div>
        ))}
      </div>
    );
  };
}

export default function PriceChart({ priceSeries, trades, chartType = 'lines', overlayKeys = [], strategyLabel }) {
  const isBand = chartType === 'band';

  const bandKeys = isBand ? overlayKeys.filter((k) => k.toLowerCase().includes('lower') || k.toLowerCase().includes('upper')) : [];
  const lowerKey = bandKeys.find((k) => k.toLowerCase().includes('lower'));
  const upperKey = bandKeys.find((k) => k.toLowerCase().includes('upper'));
  const midKey = overlayKeys.find((k) => !bandKeys.includes(k));

  const data = useMemo(
    () => priceSeries.map((d) => (
      isBand && lowerKey && upperKey ? { ...d, band: [d[lowerKey], d[upperKey]] } : { ...d }
    )),
    [priceSeries, isBand, lowerKey, upperKey]
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
  const Tooltip_ = makeTooltip(overlayKeys);

  return (
    <div className="chart-panel">
      <div className="chart-panel-title">
        價格走勢 {strategyLabel && <span className="badge">{strategyLabel}</span>}
      </div>
      <div className="legend-row">
        <span className="legend-item"><span className="legend-dot" style={{ background: '#e9e7e1' }} />收盤價</span>
        {overlayKeys.map((k) => (
          <span className="legend-item" key={k}>
            <span className="legend-dot" style={{ background: OVERLAY_COLORS[k] || '#8b8f98' }} />
            {OVERLAY_LABELS[k] || k}
          </span>
        ))}
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
          <Tooltip content={<Tooltip_ />} />

          {isBand && lowerKey && upperKey && (
            <>
              <Area dataKey="band" stroke="none" fill="#6ee7df" fillOpacity={0.06} isAnimationActive={false} />
              <Line dataKey={upperKey} stroke="#6ee7df" strokeWidth={0.9} dot={false} strokeOpacity={0.55} isAnimationActive={false} />
              <Line dataKey={lowerKey} stroke="#6ee7df" strokeWidth={0.9} dot={false} strokeOpacity={0.55} isAnimationActive={false} />
            </>
          )}
          {!isBand && overlayKeys.map((k) => (
            <Line key={k} dataKey={k} stroke={OVERLAY_COLORS[k] || '#8b8f98'} strokeWidth={1.1} dot={false} isAnimationActive={false} />
          ))}
          {isBand && midKey && (
            <Line dataKey={midKey} stroke={OVERLAY_COLORS[midKey] || '#d4b06a'} strokeWidth={1.1} dot={false} isAnimationActive={false} />
          )}

          <Line dataKey="close" stroke="#e9e7e1" strokeWidth={1.2} dot={false} isAnimationActive={false} />

          <Scatter data={longEntries} dataKey="val" shape={(p) => <Triangle {...p} up color="#ec5f5f" />} isAnimationActive={false} />
          <Scatter data={shortEntries} dataKey="val" shape={(p) => <Triangle {...p} up={false} color="#29b389" />} isAnimationActive={false} />
          <Scatter data={longExits} dataKey="val" shape={(p) => <Triangle {...p} up={false} color="#8b8f98" />} isAnimationActive={false} />
          <Scatter data={shortExits} dataKey="val" shape={(p) => <Triangle {...p} up color="#8b8f98" />} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
