# -*- coding: utf-8 -*-
"""策略執行的共用邏輯，供 /api/backtest 與背景排程共同呼叫，避免重複程式碼"""
from bollinger_strategy import (
    compute_indicators, detect_breakout_signals, detect_divergence_signals, run_backtest,
)
from ma_strategy import build_ma_signals, run_backtest_ma
from generic_backtest import run_generic_backtest, run_buy_and_hold
from ma_cross_strategy import compute_ma_cross_signals
from donchian_strategy import compute_donchian_signals
from rsi_strategy import compute_rsi_signals
from macd_strategy import compute_macd_signals
from atr_strategy import compute_atr_channel_signals
from fvg_strategy import detect_fvg_signals

STRATEGY_LABELS = {
    "bollinger": "布林通道策略",
    "ma3": "均線三刀流",
    "ma_cross": "均線黃金/死亡交叉",
    "donchian": "唐奇安通道突破",
    "rsi": "RSI 超買超賣",
    "macd": "MACD 動量策略",
    "atr_channel": "ATR 通道突破",
    "fvg": "FVG 缺口回補",
    "buy_hold": "買進持有（基準）",
}

# stop_type / stop_pct / atr_period / atr_mult 是共用欄位，給 ma_cross / rsi / macd 選擇
# 用固定百分比停損還是 ATR 動態停損（同一個請求只會用到其中一組策略參數，共用欄位不會互相干擾）
DEFAULT_PARAMS = {
    "bollinger": dict(bb_window=20, bb_std=2.0, vol_mult=1.5),
    "ma3": dict(ma_fast=20, ma_mid=60, ma_slow=240),
    "ma_cross": dict(cross_fast=20, cross_slow=60, cross_ma_type="sma",
                      stop_type="pct", stop_pct=0.08, atr_period=14, atr_mult=2.0),
    "donchian": dict(donch_entry_window=20, donch_exit_window=10),
    "rsi": dict(rsi_period=14, rsi_oversold=30, rsi_overbought=70,
                stop_type="pct", stop_pct=0.06, atr_period=14, atr_mult=2.0),
    "macd": dict(macd_fast=12, macd_slow=26, macd_signal=9,
                 stop_type="pct", stop_pct=0.08, atr_period=14, atr_mult=2.0),
    "atr_channel": dict(atr_ch_period=14, atr_ch_ma_window=20, atr_ch_mult=2.0),
    "fvg": dict(fvg_atr_period=14, fvg_max_wait=20, fvg_atr_stop_mult=1.5, fvg_atr_target_mult=3.0),
    "buy_hold": dict(),
}


def min_bars_for_strategy(strategy: str, params: dict, base_min: int = 60) -> int:
    p = {**DEFAULT_PARAMS.get(strategy, {}), **(params or {})}
    if strategy == "ma3":
        return max(base_min, int(p.get("ma_slow", 240) * 1.2))
    if strategy == "ma_cross":
        return max(base_min, int(p.get("cross_slow", 60) * 1.2))
    if strategy == "macd":
        return max(base_min, int(p.get("macd_slow", 26) * 1.5))
    if strategy == "atr_channel":
        return max(base_min, int(p.get("atr_ch_ma_window", 20) * 1.5))
    return base_min


def _stop_kwargs(p: dict) -> dict:
    """把統一的 stop_type/stop_pct/atr_mult 轉成 run_generic_backtest 要的參數"""
    stop_type = p.get("stop_type", "pct")
    if stop_type == "atr":
        return dict(atr_stop_mult=p.get("atr_mult", 2.0))
    if stop_type == "pct":
        pct = p.get("stop_pct", 0)
        return dict(stop_pct=pct if pct and pct > 0 else None)
    return dict()  # "none"


def run_strategy(df, strategy: str, params: dict, allow_short: bool = True,
                  capital: float = 1_000_000.0, bars_per_day: float = 1.0):
    """
    執行指定策略的訊號計算 + 回測
    回傳 dict(sig_df, res, overlay_keys, oscillator_keys, chart_type)
    """
    p = {**DEFAULT_PARAMS.get(strategy, {}), **(params or {})}
    overlay_keys, oscillator_keys, chart_type = [], [], "lines"

    if strategy == "buy_hold":
        res = run_buy_and_hold(df, init_capital=capital)
        sig_df = df
        chart_type = "none"

    elif strategy == "ma3":
        sig_df = build_ma_signals(df, fast=p["ma_fast"], mid=p["ma_mid"], slow=p["ma_slow"])
        res = run_backtest_ma(sig_df, allow_short=allow_short, init_capital=capital)
        overlay_keys = ["ema_fast", "ema_mid", "ema_slow"]
        chart_type = "lines"

    elif strategy == "ma_cross":
        sig_df = compute_ma_cross_signals(df, fast=p["cross_fast"], slow=p["cross_slow"],
                                           ma_type=p["cross_ma_type"], atr_period=p.get("atr_period", 14))
        res = run_generic_backtest(sig_df, allow_short=allow_short, init_capital=capital, **_stop_kwargs(p))
        overlay_keys = ["ma_fast", "ma_slow"]
        chart_type = "lines"

    elif strategy == "donchian":
        sig_df = compute_donchian_signals(df, entry_window=p["donch_entry_window"], exit_window=p["donch_exit_window"])
        res = run_generic_backtest(sig_df, allow_short=allow_short, init_capital=capital)
        overlay_keys = ["donch_upper_entry", "donch_lower_entry"]
        chart_type = "band"

    elif strategy == "rsi":
        sig_df = compute_rsi_signals(df, period=p["rsi_period"], oversold=p["rsi_oversold"],
                                      overbought=p["rsi_overbought"], atr_period=p.get("atr_period", 14))
        res = run_generic_backtest(sig_df, allow_short=allow_short, init_capital=capital, **_stop_kwargs(p))
        oscillator_keys = ["rsi"]
        chart_type = "oscillator_rsi"

    elif strategy == "macd":
        sig_df = compute_macd_signals(df, fast=p["macd_fast"], slow=p["macd_slow"], signal=p["macd_signal"],
                                       atr_period=p.get("atr_period", 14))
        res = run_generic_backtest(sig_df, allow_short=allow_short, init_capital=capital, **_stop_kwargs(p))
        oscillator_keys = ["macd", "macd_signal", "macd_hist"]
        chart_type = "oscillator_macd"

    elif strategy == "atr_channel":
        sig_df = compute_atr_channel_signals(df, atr_period=p["atr_ch_period"],
                                              ma_window=p["atr_ch_ma_window"], mult=p["atr_ch_mult"])
        res = run_generic_backtest(sig_df, allow_short=allow_short, init_capital=capital)
        overlay_keys = ["atr_mid", "atr_upper", "atr_lower"]
        chart_type = "band"

    elif strategy == "fvg":
        sig_df = detect_fvg_signals(df, atr_period=p["fvg_atr_period"], max_wait_bars=p["fvg_max_wait"])
        res = run_generic_backtest(sig_df, allow_short=allow_short, init_capital=capital,
                                    atr_stop_mult=p["fvg_atr_stop_mult"], atr_target_mult=p["fvg_atr_target_mult"])
        overlay_keys = []
        chart_type = "lines"

    else:  # bollinger
        squeeze_lookback = max(20, int(126 * bars_per_day))
        sig_df = compute_indicators(df, bb_window=p["bb_window"], bb_std=p["bb_std"], squeeze_lookback=squeeze_lookback)
        sig_df = detect_breakout_signals(sig_df, vol_mult=p["vol_mult"])
        sig_df = detect_divergence_signals(sig_df)
        res = run_backtest(sig_df, allow_short=allow_short, init_capital=capital)
        overlay_keys = ["mid", "upper", "lower"]
        chart_type = "band"

    return dict(sig_df=sig_df, res=res, overlay_keys=overlay_keys,
                oscillator_keys=oscillator_keys, chart_type=chart_type)


ALL_SIGNAL_STRATEGIES = ["bollinger", "ma3", "ma_cross", "donchian", "rsi", "macd", "atr_channel", "fvg"]

STYLE_PRESETS = {
    "short": dict(label="短沖", interval="1h", strategies=ALL_SIGNAL_STRATEGIES),
    "swing": dict(label="長線波段", interval="1d", strategies=ALL_SIGNAL_STRATEGIES),
}


def determine_latest_event(sig_df, res):
    """
    判斷最新一根K棒是否剛好出現「新的」進場或出場事件
    回傳 None 或 dict(type, date, price)  type 例如 'entry_long' / 'exit_short'
    """
    if sig_df is None or len(sig_df) == 0:
        return None
    last_bar_date = sig_df.index[-1]

    trades = res.get("trades")
    if trades is not None and len(trades):
        last_trade = trades.iloc[-1]
        if last_trade["exit_date"] == last_bar_date:
            return dict(type=f"exit_{last_trade['side']}", date=last_bar_date, price=last_trade["exit_price"])

    op = res.get("open_position")
    if op and op.get("entry_date") == last_bar_date:
        return dict(type=f"entry_{op['side']}", date=last_bar_date, price=op["entry_price"])

    return None
