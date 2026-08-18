import React, { useMemo } from 'react';
import {
  ComposedChart, Area, Line, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';
import { useRemeasureKey } from '../useElementWidth';
import { downsampleForChart } from '../downsample';

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

  const data = useMemo(() => {
    const rows = priceSeries.map((d) => (
      isBand && lowerKey && upperKey
        ? { ...d, band: [d[lowerKey], d[upperKey]], entry_long: null, entry_short: null, exit_long: null, exit_short: null }
        : { ...d, entry_long: null, entry_short: null, exit_long: null, exit_short: null }
    ));
    // 用 Map 一次建立日期→列索引對照，避免每筆交易都線性掃描整個陣列
    const indexByDate = new Map(rows.map((r, i) => [r.date, i]));
    (trades || []).forEach((t) => {
      const entryIdx = indexByDate.get(t.entry_date);
      const exitIdx = indexByDate.get(t.exit_date);
      if (t.side === 'long') {
        if (entryIdx != null) rows[entryIdx].entry_long = t.entry_price;
        if (exitIdx != null) rows[exitIdx].exit_long = t.exit_price;
      } else {
        if (entryIdx != null) rows[entryIdx].entry_short = t.entry_price;
        if (exitIdx != null) rows[exitIdx].exit_short = t.exit_price;
      }
    });
    return rows;
  }, [priceSeries, isBand, lowerKey, upperKey, trades]);

  // 資料點太多時（常見於小時K/分K）先抽稀再畫，避免手機瀏覽器畫太密的SVG卡住；
  // 進出場K棒一定保留，不會因為抽稀被跳過
  const chartData = useMemo(() => {
    const keepIndices = [];
    data.forEach((r, i) => {
      if (r.entry_long != null || r.entry_short != null || r.exit_long != null || r.exit_short != null) {
        keepIndices.push(i);
      }
    });
    return downsampleForChart(data, 600, keepIndices);
  }, [data]);

  const everyNth = Math.max(1, Math.floor(chartData.length / 8));
  const remeasureKey = useRemeasureKey();
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
      <ResponsiveContainer key={remeasureKey} width="100%" height={380}>
        <ComposedChart data={chartData} margin={{ top: 4, right: 12, left: -8, bottom: 4 }}>
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

          <Scatter data={chartData} dataKey="entry_long" shape={(p) => <Triangle {...p} up color="#ec5f5f" />} isAnimationActive={false} />
          <Scatter data={chartData} dataKey="entry_short" shape={(p) => <Triangle {...p} up={false} color="#29b389" />} isAnimationActive={false} />
          <Scatter data={chartData} dataKey="exit_long" shape={(p) => <Triangle {...p} up={false} color="#8b8f98" />} isAnimationActive={false} />
          <Scatter data={chartData} dataKey="exit_short" shape={(p) => <Triangle {...p} up color="#8b8f98" />} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
