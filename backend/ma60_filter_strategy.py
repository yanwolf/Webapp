# -*- coding: utf-8 -*-
"""
MA60季線 + 200MA濾網（只做多）
================================
收盤由下往上穿越60日均線，且當時收盤在200日均線之上（確認大方向偏多）才進場；
收盤跌破60日均線就出場。規則最單純，交易次數少，且只做多不做空。
"""
import pandas as pd


def compute_ma60_filter_signals(df: pd.DataFrame, ma_period: int = 60, filter_period: int = 200) -> pd.DataFrame:
    df = df.copy()
    df["ma60"] = df["Close"].rolling(ma_period).mean()
    df["ma200"] = df["Close"].rolling(filter_period).mean()

    cross_up = (df["Close"] > df["ma60"]) & (df["Close"].shift(1) <= df["ma60"].shift(1))
    above_filter = df["Close"] > df["ma200"]

    df["entry_long"] = cross_up & above_filter
    df["entry_short"] = False
    df["exit_long"] = df["Close"] < df["ma60"]
    df["exit_short"] = False
    return df
