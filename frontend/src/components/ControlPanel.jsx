import React from 'react';
import TickerInput from './TickerInput';

const MARKET_META = {
  us: { label: '美股', placeholder: '例如 SPY / AAPL / QQQ' },
  tw: { label: '台股', placeholder: '例如 2330 / 0050 / ^TWII' },
  crypto: { label: '加密貨幣', placeholder: '例如 BTC / ETH' },
};

const INTERVAL_META = {
  '1d': { label: '日K', hint: null },
  '4h': { label: '4小時K', hint: 'Yahoo 最多回溯約2年' },
  '1h': { label: '1小時K', hint: 'Yahoo 最多回溯約2年' },
  '15m': { label: '15分K', hint: 'Yahoo 最多回溯60天' },
  '5m': { label: '5分K', hint: 'Yahoo 最多回溯60天' },
  '1m': { label: '1分K', hint: 'Yahoo 最多回溯7天' },
};

const STRATEGY_META = {
  bollinger: { label: '布林通道策略' },
  ma3: { label: '均線三刀流' },
  ma_cross: { label: '均線黃金/死亡交叉' },
  donchian: { label: '唐奇安通道突破' },
  rsi: { label: 'RSI 超買超賣' },
  macd: { label: 'MACD 動量策略' },
  atr_channel: { label: 'ATR 通道突破' },
  fvg: { label: 'FVG 缺口回補' },
  buy_hold: { label: '買進持有（基準）' },
};

const STRATEGIES_WITH_STOP_CHOICE = ['ma_cross', 'rsi', 'macd'];

export default function ControlPanel({ form, setForm, onSubmit, loading }) {
  const update = (key) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [key]: val }));
  };

  const intervalHint = INTERVAL_META[form.interval]?.hint;

  return (
    <div className="panel control-panel">
      <div className="field">
        <label>策略</label>
        <select value={form.strategy} onChange={update('strategy')}>
          {Object.entries(STRATEGY_META).map(([val, { label }]) => (
            <option key={val} value={val}>{label}</option>
          ))}
        </select>
      </div>

      <div className="field">
        <label>市場</label>
        <select value={form.market} onChange={update('market')}>
          <option value="us">美股</option>
          <option value="tw">台股</option>
          <option value="crypto">加密貨幣</option>
        </select>
      </div>

      <div className="field">
        <label>代碼</label>
        <TickerInput
          market={form.market}
          value={form.ticker}
          onChange={(v) => setForm((prev) => ({ ...prev, ticker: v }))}
          placeholder={MARKET_META[form.market].placeholder}
        />
      </div>

      <div className="field">
        <label>K線週期{intervalHint ? ` · ${intervalHint}` : ''}</label>
        <select value={form.interval} onChange={update('interval')}>
          {Object.entries(INTERVAL_META).map(([val, { label }]) => (
            <option key={val} value={val}>{label}</option>
          ))}
        </select>
      </div>

      <div className="field">
        <label>開始日期</label>
        <input type="date" value={form.start} onChange={update('start')} />
      </div>

      <div className="field">
        <label>結束日期</label>
        <input type="date" value={form.end} onChange={update('end')} placeholder="預設今天" />
      </div>

      <div className="field">
        <label>初始資金</label>
        <input type="number" value={form.capital} onChange={update('capital')} min={1} step={10000} />
      </div>

      {form.strategy !== 'buy_hold' && (
        <div className="field">
          <label>交易方式</label>
          <select
            value={form.allow_short ? 'short' : 'cash'}
            onChange={(e) => setForm((prev) => ({ ...prev, allow_short: e.target.value === 'short' }))}
          >
            <option value="cash">現股買賣（只做多）</option>
            <option value="short">現股 + 做空</option>
          </select>
        </div>
      )}

      {form.strategy === 'ma3' && (
        <>
          <div className="field">
            <label>快刀 EMA</label>
            <input type="number" value={form.ma_fast} onChange={update('ma_fast')} min={2} max={200} />
          </div>
          <div className="field">
            <label>中刀 EMA</label>
            <input type="number" value={form.ma_mid} onChange={update('ma_mid')} min={5} max={400} />
          </div>
          <div className="field">
            <label>慢刀 EMA</label>
            <input type="number" value={form.ma_slow} onChange={update('ma_slow')} min={10} max={800} />
          </div>
        </>
      )}

      {form.strategy === 'ma_cross' && (
        <>
          <div className="field">
            <label>均線類型</label>
            <select value={form.cross_ma_type} onChange={update('cross_ma_type')}>
              <option value="sma">SMA 簡單均線</option>
              <option value="ema">EMA 指數均線</option>
            </select>
          </div>
          <div className="field">
            <label>快線週期</label>
            <input type="number" value={form.cross_fast} onChange={update('cross_fast')} min={2} max={200} />
          </div>
          <div className="field">
            <label>慢線週期</label>
            <input type="number" value={form.cross_slow} onChange={update('cross_slow')} min={5} max={400} />
          </div>
        </>
      )}

      {form.strategy === 'donchian' && (
        <>
          <div className="field">
            <label>突破窗口(天)</label>
            <input type="number" value={form.donch_entry_window} onChange={update('donch_entry_window')} min={5} max={200} />
          </div>
          <div className="field">
            <label>出場窗口(天)</label>
            <input type="number" value={form.donch_exit_window} onChange={update('donch_exit_window')} min={3} max={200} />
          </div>
        </>
      )}

      {form.strategy === 'rsi' && (
        <>
          <div className="field">
            <label>RSI 週期</label>
            <input type="number" value={form.rsi_period} onChange={update('rsi_period')} min={2} max={100} />
          </div>
          <div className="field">
            <label>超賣門檻</label>
            <input type="number" value={form.rsi_oversold} onChange={update('rsi_oversold')} min={1} max={49} />
          </div>
          <div className="field">
            <label>超買門檻</label>
            <input type="number" value={form.rsi_overbought} onChange={update('rsi_overbought')} min={51} max={99} />
          </div>
        </>
      )}

      {form.strategy === 'macd' && (
        <>
          <div className="field">
            <label>快線 EMA</label>
            <input type="number" value={form.macd_fast} onChange={update('macd_fast')} min={2} max={100} />
          </div>
          <div className="field">
            <label>慢線 EMA</label>
            <input type="number" value={form.macd_slow} onChange={update('macd_slow')} min={3} max={200} />
          </div>
          <div className="field">
            <label>訊號線 EMA</label>
            <input type="number" value={form.macd_signal} onChange={update('macd_signal')} min={2} max={100} />
          </div>
        </>
      )}

      {/* 均線交叉 / RSI / MACD 共用的停損設定 */}
      {STRATEGIES_WITH_STOP_CHOICE.includes(form.strategy) && (
        <>
          <div className="field">
            <label>停損方式</label>
            <select value={form.stop_type} onChange={update('stop_type')}>
              <option value="pct">固定百分比</option>
              <option value="atr">ATR 動態停損</option>
              <option value="none">不設停損</option>
            </select>
          </div>
          {form.stop_type === 'pct' && (
            <div className="field">
              <label>停損百分比</label>
              <input type="number" value={form.stop_pct} onChange={update('stop_pct')} min={0.01} max={0.5} step={0.01} />
            </div>
          )}
          {form.stop_type === 'atr' && (
            <>
              <div className="field">
                <label>ATR 週期</label>
                <input type="number" value={form.atr_period} onChange={update('atr_period')} min={2} max={100} />
              </div>
              <div className="field">
                <label>ATR 倍數</label>
                <input type="number" value={form.atr_mult} onChange={update('atr_mult')} min={0.5} max={10} step={0.1} />
              </div>
            </>
          )}
        </>
      )}

      {form.strategy === 'atr_channel' && (
        <>
          <div className="field">
            <label>ATR 週期</label>
            <input type="number" value={form.atr_ch_period} onChange={update('atr_ch_period')} min={2} max={100} />
          </div>
          <div className="field">
            <label>中軌 EMA 週期</label>
            <input type="number" value={form.atr_ch_ma_window} onChange={update('atr_ch_ma_window')} min={5} max={200} />
          </div>
          <div className="field">
            <label>通道寬度（ATR倍數）</label>
            <input type="number" value={form.atr_ch_mult} onChange={update('atr_ch_mult')} min={0.5} max={10} step={0.1} />
          </div>
        </>
      )}

      {form.strategy === 'fvg' && (
        <>
          <div className="field">
            <label>缺口回補等待K棒數</label>
            <input type="number" value={form.fvg_max_wait} onChange={update('fvg_max_wait')} min={3} max={100} />
          </div>
          <div className="field">
            <label>ATR 週期</label>
            <input type="number" value={form.fvg_atr_period} onChange={update('fvg_atr_period')} min={2} max={100} />
          </div>
          <div className="field">
            <label>停損（ATR倍數）</label>
            <input type="number" value={form.fvg_atr_stop_mult} onChange={update('fvg_atr_stop_mult')} min={0.5} max={10} step={0.1} />
          </div>
          <div className="field">
            <label>停利（ATR倍數）</label>
            <input type="number" value={form.fvg_atr_target_mult} onChange={update('fvg_atr_target_mult')} min={0.5} max={20} step={0.1} />
          </div>
        </>
      )}

      <button className="run-btn" onClick={onSubmit} disabled={loading || !form.ticker.trim()}>
        {loading ? '回測中…' : '執行回測'}
      </button>
    </div>
  );
}
