# -*- coding: utf-8 -*-
"""策略執行的共用邏輯，供 /api/backtest 與背景排程共同呼叫，避免重複程式碼"""
import itertools

from bollinger_strategy import (
    compute_indicators, detect_breakout_signals, detect_divergence_signals, run_backtest,
)
from ma_strategy import build_ma_signals
from generic_backtest import run_generic_backtest, run_buy_and_hold
from ma_cross_strategy import compute_ma_cross_signals
from donchian_strategy import compute_donchian_signals
from rsi_strategy import compute_rsi_signals
from macd_strategy import compute_macd_signals
from atr_strategy import compute_atr_channel_signals
from fvg_strategy import detect_fvg_signals
from pivot_strategy import compute_pivot_signals
from ma60_filter_strategy import compute_ma60_filter_signals

STRATEGY_LABELS = {
    "bollinger": "布林通道策略",
    "ma3": "均線三刀流",
    "ma_cross": "均線黃金/死亡交叉",
    "donchian": "唐奇安通道突破",
    "rsi": "RSI 超買超賣",
    "macd": "MACD 動量策略",
    "atr_channel": "ATR 通道突破",
    "fvg": "FVG 缺口回補",
    "pivot": "轉折突破",
    "ma60_filter": "MA60季線濾網",
    "buy_hold": "買進持有（基準）",
}

# stop_type / stop_pct / atr_period / atr_mult 是共用欄位，給 ma_cross / rsi / macd 選擇
# 用固定百分比停損還是 ATR 動態停損（同一個請求只會用到其中一組策略參數，共用欄位不會互相干擾）
DEFAULT_PARAMS = {
    "bollinger": dict(bb_window=20, bb_std=2.0, vol_mult=1.5),
    "ma3": dict(ma_fast=20, ma_mid=60, ma_slow=240, ma_type="sma"),
    "ma_cross": dict(cross_fast=20, cross_slow=60, cross_ma_type="sma",
                      stop_type="pct", stop_pct=0.08, atr_period=14, atr_mult=2.0),
    "donchian": dict(donch_entry_window=20, donch_exit_window=10),
    "rsi": dict(rsi_period=14, rsi_oversold=30, rsi_overbought=70,
                stop_type="pct", stop_pct=0.06, atr_period=14, atr_mult=2.0),
    "macd": dict(macd_fast=12, macd_slow=26, macd_signal=9,
                 stop_type="pct", stop_pct=0.08, atr_period=14, atr_mult=2.0),
    "atr_channel": dict(atr_ch_period=14, atr_ch_ma_window=20, atr_ch_mult=2.0),
    "fvg": dict(fvg_atr_period=14, fvg_max_wait=20, fvg_atr_stop_mult=1.5, fvg_atr_target_mult=3.0),
    "pivot": dict(pivot_left=2, pivot_right=5),
    "ma60_filter": dict(ma60_period=60, ma60_filter_period=200),
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
    if strategy == "ma60_filter":
        return max(base_min, int(p.get("ma60_filter_period", 200) * 1.2))
    if strategy == "pivot":
        return max(base_min, p.get("pivot_left", 2) + p.get("pivot_right", 5) + 20)
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
        sig_df = build_ma_signals(df, fast=p["ma_fast"], mid=p["ma_mid"], slow=p["ma_slow"],
                                   ma_type=p.get("ma_type", "sma"))
        res = run_generic_backtest(sig_df, allow_short=allow_short, init_capital=capital)
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

    elif strategy == "pivot":
        sig_df = compute_pivot_signals(df, left=p["pivot_left"], right=p["pivot_right"])
        res = run_generic_backtest(sig_df, allow_short=allow_short, init_capital=capital)
        overlay_keys = ["pivot_high", "pivot_low"]
        chart_type = "lines"

    elif strategy == "ma60_filter":
        sig_df = compute_ma60_filter_signals(df, ma_period=p["ma60_period"], filter_period=p["ma60_filter_period"])
        res = run_generic_backtest(sig_df, allow_short=False, init_capital=capital)
        overlay_keys = ["ma60", "ma200"]
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


ALL_SIGNAL_STRATEGIES = ["bollinger", "ma3", "ma_cross", "donchian", "rsi", "macd",
                          "atr_channel", "fvg", "pivot", "ma60_filter"]

STYLE_PRESETS = {
    "short": dict(label="短沖", interval="1h", strategies=ALL_SIGNAL_STRATEGIES),
    "swing": dict(label="長線波段", interval="1d", strategies=ALL_SIGNAL_STRATEGIES),
}


# ----------------------------------------------------------------------
# 參數最佳化：每個策略預先設計一組合理的搜尋網格（值太多會跑太久，這裡控制在數十到百組內）
# ----------------------------------------------------------------------
def _grid_bollinger():
    for bb_window, bb_std, vol_mult in itertools.product([15, 20, 25], [1.75, 2.0, 2.25, 2.5], [1.2, 1.5, 1.8]):
        yield dict(bb_window=bb_window, bb_std=bb_std, vol_mult=vol_mult)


def _grid_ma3():
    for fast, mid, slow in itertools.product([10, 15, 20], [40, 60, 80], [150, 200, 240, 300]):
        if fast < mid < slow:
            yield dict(ma_fast=fast, ma_mid=mid, ma_slow=slow)


def _grid_ma_cross():
    for fast, slow, stop_pct in itertools.product([5, 10, 15, 20], [30, 50, 70, 100], [0.05, 0.08, 0.12]):
        if fast < slow:
            yield dict(cross_fast=fast, cross_slow=slow, stop_type="pct", stop_pct=stop_pct)


def _grid_donchian():
    for entry, exit_ in itertools.product([10, 15, 20, 30, 40], [5, 10, 15, 20]):
        if exit_ < entry:
            yield dict(donch_entry_window=entry, donch_exit_window=exit_)


def _grid_rsi():
    for period, os_, ob_ in itertools.product([7, 10, 14, 21], [20, 25, 30, 35], [65, 70, 75, 80]):
        yield dict(rsi_period=period, rsi_oversold=os_, rsi_overbought=ob_)


def _grid_macd():
    for fast, slow, signal in itertools.product([8, 12, 16], [20, 26, 32], [5, 9, 12]):
        if fast < slow:
            yield dict(macd_fast=fast, macd_slow=slow, macd_signal=signal)


def _grid_atr_channel():
    for period, ma_window, mult in itertools.product([7, 14, 21], [10, 20, 30], [1.5, 2.0, 2.5, 3.0]):
        yield dict(atr_ch_period=period, atr_ch_ma_window=ma_window, atr_ch_mult=mult)


def _grid_fvg():
    for wait, stop_mult, target_mult in itertools.product([10, 20, 30], [1.0, 1.5, 2.0], [2.0, 3.0, 4.0]):
        if target_mult > stop_mult:
            yield dict(fvg_max_wait=wait, fvg_atr_stop_mult=stop_mult, fvg_atr_target_mult=target_mult)


def _grid_pivot():
    for left, right in itertools.product([1, 2, 3], [3, 5, 8]):
        yield dict(pivot_left=left, pivot_right=right)


def _grid_ma60_filter():
    for ma_period, filter_period in itertools.product([40, 60, 80], [150, 200, 250]):
        if ma_period < filter_period:
            yield dict(ma60_period=ma_period, ma60_filter_period=filter_period)


OPTIMIZE_GRIDS = {
    "bollinger": _grid_bollinger,
    "ma3": _grid_ma3,
    "ma_cross": _grid_ma_cross,
    "donchian": _grid_donchian,
    "rsi": _grid_rsi,
    "macd": _grid_macd,
    "atr_channel": _grid_atr_channel,
    "fvg": _grid_fvg,
    "pivot": _grid_pivot,
    "ma60_filter": _grid_ma60_filter,
}

# 每個參數的中文標籤，給前端表格用
PARAM_LABELS = {
    "bb_window": "布林週期", "bb_std": "標準差倍數", "vol_mult": "爆量倍數",
    "ma_fast": "快刀", "ma_mid": "中刀", "ma_slow": "慢刀",
    "cross_fast": "快線", "cross_slow": "慢線", "stop_pct": "停損%",
    "donch_entry_window": "突破窗口", "donch_exit_window": "出場窗口",
    "rsi_period": "RSI週期", "rsi_oversold": "超賣門檻", "rsi_overbought": "超買門檻",
    "macd_fast": "快線EMA", "macd_slow": "慢線EMA", "macd_signal": "訊號線EMA",
    "atr_ch_period": "ATR週期", "atr_ch_ma_window": "中軌週期", "atr_ch_mult": "通道倍數",
    "fvg_max_wait": "等待K棒數", "fvg_atr_stop_mult": "停損倍數", "fvg_atr_target_mult": "停利倍數",
    "pivot_left": "轉折左窗", "pivot_right": "轉折右窗",
    "ma60_period": "季線週期", "ma60_filter_period": "濾網均線週期",
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
