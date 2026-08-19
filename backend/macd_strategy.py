# -*- coding: utf-8 -*-
"""
MACD 動量策略（經典趨勢動能指標）
====================================
原版：金叉做多、死叉做空，雙向都能交易
加濾網版：只做多。金叉且收盤站上200日均線（確認大方向偏多）才進場，死叉就出場，
          用長期均線過濾逆勢單
"""
import pandas as pd
from atr_utils import compute_atr


def compute_macd_signals(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9,
                          atr_period: int = 14, use_filter: bool = False, filter_ma_period: int = 200) -> pd.DataFrame:
    df = df.copy()
    df["atr"] = compute_atr(df, atr_period)
    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()
    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df["macd"].ewm(span=signal, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    golden = (df["macd"].shift(1) <= df["macd_signal"].shift(1)) & (df["macd"] > df["macd_signal"])
    death = (df["macd"].shift(1) >= df["macd_signal"].shift(1)) & (df["macd"] < df["macd_signal"])

    if use_filter:
        df["filter_ma"] = df["Close"].rolling(filter_ma_period).mean()
        above_filter = df["Close"] > df["filter_ma"]
        df["entry_long"] = golden & above_filter
        df["entry_short"] = False
        df["exit_long"] = death
        df["exit_short"] = False
    else:
        df["entry_long"] = golden
        df["entry_short"] = death
        df["exit_long"] = death
        df["exit_short"] = golden

    return df
