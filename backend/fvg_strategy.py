# -*- coding: utf-8 -*-
"""
FVG（Fair Value Gap，公允價值缺口）策略
========================================
多頭缺口：第1根K棒高點 < 第3根K棒低點（中間留下沒有成交重疊的缺口）
空頭缺口：第1根K棒低點 > 第3根K棒高點

邏輯：缺口形成後，等價格回測缺口區間並出現反轉確認K棒才進場。
本身沒有指標型的出場條件，出場靠 ATR 停損/停利（在 generic_backtest 裡設定）。
"""
import numpy as np
import pandas as pd
from atr_utils import compute_atr


def detect_fvg_signals(df: pd.DataFrame, atr_period: int = 14, max_wait_bars: int = 20) -> pd.DataFrame:
    df = df.copy()
    df["atr"] = compute_atr(df, atr_period)

    n = len(df)
    high = df["High"].values
    low = df["Low"].values
    close = df["Close"].values
    open_ = df["Open"].values

    entry_long = np.zeros(n, dtype=bool)
    entry_short = np.zeros(n, dtype=bool)
    fvg_upper = np.full(n, np.nan)
    fvg_lower = np.full(n, np.nan)

    for i in range(2, n):
        # 多頭缺口：第1根高點 < 第3根低點
        if low[i] > high[i - 2]:
            gap_low, gap_high = high[i - 2], low[i]
            end = min(i + max_wait_bars, n - 1)
            for j in range(i + 1, end + 1):
                if low[j] <= gap_high and close[j] >= gap_low and close[j] > open_[j]:
                    entry_long[j] = True
                    fvg_lower[j] = gap_low
                    fvg_upper[j] = gap_high
                    break

        # 空頭缺口：第1根低點 > 第3根高點
        if high[i] < low[i - 2]:
            gap_low, gap_high = high[i], low[i - 2]
            end = min(i + max_wait_bars, n - 1)
            for j in range(i + 1, end + 1):
                if high[j] >= gap_low and close[j] <= gap_high and close[j] < open_[j]:
                    entry_short[j] = True
                    fvg_lower[j] = gap_low
                    fvg_upper[j] = gap_high
                    break

    df["entry_long"] = entry_long
    df["entry_short"] = entry_short
    # FVG 沒有指標型出場訊號，出場完全交給 ATR 停損/停利處理
    df["exit_long"] = False
    df["exit_short"] = False
    df["fvg_upper"] = fvg_upper
    df["fvg_lower"] = fvg_lower
    return df
