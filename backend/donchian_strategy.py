# -*- coding: utf-8 -*-
"""唐奇安通道突破策略（Donchian Channel Breakout，經典海龜交易法則簡化版）"""
import pandas as pd


def compute_donchian_signals(df: pd.DataFrame, entry_window: int = 20, exit_window: int = 10) -> pd.DataFrame:
    df = df.copy()
    df["donch_upper_entry"] = df["High"].rolling(entry_window).max()
    df["donch_lower_entry"] = df["Low"].rolling(entry_window).min()
    df["donch_upper_exit"] = df["High"].rolling(exit_window).max()
    df["donch_lower_exit"] = df["Low"].rolling(exit_window).min()

    df["entry_long"] = df["Close"] > df["donch_upper_entry"].shift(1)
    df["entry_short"] = df["Close"] < df["donch_lower_entry"].shift(1)
    df["exit_long"] = df["Close"] < df["donch_lower_exit"].shift(1)
    df["exit_short"] = df["Close"] > df["donch_upper_exit"].shift(1)
    return df
