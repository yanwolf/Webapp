# -*- coding: utf-8 -*-
"""ATR 通道突破策略：中軌(EMA) ± 倍數×ATR 畫出通道，突破進場、跌破中軌出場"""
import pandas as pd
from atr_utils import compute_atr


def compute_atr_channel_signals(df: pd.DataFrame, atr_period: int = 14,
                                 ma_window: int = 20, mult: float = 2.0) -> pd.DataFrame:
    df = df.copy()
    df["atr"] = compute_atr(df, atr_period)
    df["atr_mid"] = df["Close"].ewm(span=ma_window, adjust=False).mean()
    df["atr_upper"] = df["atr_mid"] + mult * df["atr"]
    df["atr_lower"] = df["atr_mid"] - mult * df["atr"]

    df["entry_long"] = df["Close"] > df["atr_upper"]
    df["entry_short"] = df["Close"] < df["atr_lower"]
    df["exit_long"] = df["Close"] < df["atr_mid"]
    df["exit_short"] = df["Close"] > df["atr_mid"]
    return df
