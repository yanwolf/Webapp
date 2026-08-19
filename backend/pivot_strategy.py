# -*- coding: utf-8 -*-
"""
轉折突破策略（Pivot Breakout）
================================
先找出「經確認的轉折高/低點」：某根K棒的高點要比前2根、後5根都高，才算轉折高點
（低點反之）。之後盤中最高價突破轉折高點就翻多、最低價跌破轉折低點就翻空。
沒有濾網、沒有停損，靠反向訊號直接翻單，所以理論上永遠有部位（除非還沒出現第一次突破）。
"""
import numpy as np
import pandas as pd


def detect_pivots(df: pd.DataFrame, left: int = 2, right: int = 5):
    """回傳兩個 Series：pivot_high / pivot_low，值是「當下有效的最近一個經確認轉折點」"""
    n = len(df)
    high = df["High"].values
    low = df["Low"].values

    confirmed_high = np.full(n, np.nan)
    confirmed_low = np.full(n, np.nan)

    for i in range(left, n - right):
        window_h = high[i - left:i + right + 1]
        if high[i] == window_h.max() and high[i] > high[i - left:i].max() and high[i] > high[i + 1:i + right + 1].max():
            confirmed_high[i + right] = high[i]  # 要等right根之後才算「確認」，避免用到未來資料
        window_l = low[i - left:i + right + 1]
        if low[i] == window_l.min() and low[i] < low[i - left:i].min() and low[i] < low[i + 1:i + right + 1].min():
            confirmed_low[i + right] = low[i]

    pivot_high = pd.Series(confirmed_high, index=df.index).ffill()
    pivot_low = pd.Series(confirmed_low, index=df.index).ffill()
    return pivot_high, pivot_low


def compute_pivot_signals(df: pd.DataFrame, left: int = 2, right: int = 5) -> pd.DataFrame:
    df = df.copy()
    pivot_high, pivot_low = detect_pivots(df, left=left, right=right)
    df["pivot_high"] = pivot_high
    df["pivot_low"] = pivot_low

    entry_long = df["High"] > df["pivot_high"]
    entry_short = df["Low"] < df["pivot_low"]

    df["entry_long"] = entry_long
    df["entry_short"] = entry_short
    # 沒有濾網也沒有停損，靠反向訊號直接翻單出場
    df["exit_long"] = entry_short
    df["exit_short"] = entry_long
    return df
