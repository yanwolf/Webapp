# -*- coding: utf-8 -*-
"""
唐奇安通道突破策略（Donchian Channel Breakout，經典海龜交易法則簡化版）
========================================================================
原版：收盤突破前N根最高價翻多、跌破最低價翻空，無濾網無停損，訊號較多
加濾網版：收盤突破一樣要翻多/翻空，但要同時通過三關：
  1. ADX 大於門檻（確認有趨勢，盤整不出手）
  2. 成交量大於N期均量的倍數（要有量能配合）
  3. 進場後掛 ATR 停損/停利（濾網最多，訊號最少，但有風控）
"""
import pandas as pd
from adx_utils import compute_adx
from atr_utils import compute_atr


def compute_donchian_signals(df: pd.DataFrame, entry_window: int = 20, exit_window: int = 10,
                              use_filter: bool = False, adx_period: int = 14, adx_threshold: float = 20,
                              vol_period: int = 20, vol_mult: float = 1.1, atr_period: int = 14) -> pd.DataFrame:
    df = df.copy()
    df["donch_upper_entry"] = df["High"].rolling(entry_window).max()
    df["donch_lower_entry"] = df["Low"].rolling(entry_window).min()
    df["donch_upper_exit"] = df["High"].rolling(exit_window).max()
    df["donch_lower_exit"] = df["Low"].rolling(exit_window).min()

    breakout_long = df["Close"] > df["donch_upper_entry"].shift(1)
    breakout_short = df["Close"] < df["donch_lower_entry"].shift(1)

    if use_filter:
        df["atr"] = compute_atr(df, atr_period)
        df["adx"] = compute_adx(df, adx_period)
        vol_avg = df["Volume"].rolling(vol_period).mean()
        pass_filters = (df["adx"] > adx_threshold) & (df["Volume"] > vol_avg * vol_mult)

        df["entry_long"] = breakout_long & pass_filters
        df["entry_short"] = breakout_short & pass_filters
        # 有濾網版本靠 ATR 停損停利出場（在 generic_backtest 設定），這裡不用通道出場訊號
        df["exit_long"] = False
        df["exit_short"] = False
    else:
        df["entry_long"] = breakout_long
        df["entry_short"] = breakout_short
        df["exit_long"] = df["Close"] < df["donch_lower_exit"].shift(1)
        df["exit_short"] = df["Close"] > df["donch_upper_exit"].shift(1)

    return df
