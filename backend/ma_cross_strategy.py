# -*- coding: utf-8 -*-
"""均線黃金交叉 / 死亡交叉策略（雙均線，經典趨勢跟隨）"""
import pandas as pd


def compute_ma_cross_signals(df: pd.DataFrame, fast: int = 20, slow: int = 60,
                              ma_type: str = "sma") -> pd.DataFrame:
    df = df.copy()
    if ma_type == "ema":
        df["ma_fast"] = df["Close"].ewm(span=fast, adjust=False).mean()
        df["ma_slow"] = df["Close"].ewm(span=slow, adjust=False).mean()
    else:
        df["ma_fast"] = df["Close"].rolling(fast).mean()
        df["ma_slow"] = df["Close"].rolling(slow).mean()

    golden = (df["ma_fast"].shift(1) <= df["ma_slow"].shift(1)) & (df["ma_fast"] > df["ma_slow"])
    death = (df["ma_fast"].shift(1) >= df["ma_slow"].shift(1)) & (df["ma_fast"] < df["ma_slow"])

    df["golden_cross"] = golden
    df["death_cross"] = death
    df["entry_long"] = golden
    df["entry_short"] = death
    df["exit_long"] = death
    df["exit_short"] = golden
    return df
