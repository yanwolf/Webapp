# -*- coding: utf-8 -*-
"""RSI 超買超賣策略（經典均值回歸）"""
import numpy as np
import pandas as pd
from atr_utils import compute_atr


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def compute_rsi_signals(df: pd.DataFrame, period: int = 14,
                         oversold: float = 30, overbought: float = 70,
                         atr_period: int = 14) -> pd.DataFrame:
    df = df.copy()
    df["atr"] = compute_atr(df, atr_period)
    df["rsi"] = compute_rsi(df["Close"], period)

    cross_up_from_oversold = (df["rsi"].shift(1) <= oversold) & (df["rsi"] > oversold)
    cross_down_from_overbought = (df["rsi"].shift(1) >= overbought) & (df["rsi"] < overbought)

    df["entry_long"] = cross_up_from_oversold
    df["entry_short"] = cross_down_from_overbought
    # 回到中性值(50)視為均值回歸完成，出場
    df["exit_long"] = (df["rsi"].shift(1) < 50) & (df["rsi"] >= 50)
    df["exit_short"] = (df["rsi"].shift(1) > 50) & (df["rsi"] <= 50)
    return df
