# -*- coding: utf-8 -*-
"""
均線三刀流策略（張飛20MA／關羽60MA／劉備240MA）
==================================================
排列判斷（複合規則，兩條路徑用「或」串起來）：
  多方 = (20MA>60MA>240MA 且收盤站上60MA分水嶺) 或 收盤同時站上三條均線
  空方 = (20MA<60MA<240MA 且收盤跌破60MA分水嶺) 或 收盤同時跌破三條均線
  都不符合 → 排列糾結，退場觀望

進出場：
  進場點 = 排列「剛翻多／剛翻空」的那一根K棒
  出場點 = 排列轉為糾結，或直接反轉到對側
"""
import pandas as pd


def compute_ma_indicators(df: pd.DataFrame, fast: int = 20, mid: int = 60, slow: int = 240,
                           ma_type: str = "sma") -> pd.DataFrame:
    df = df.copy()
    if ma_type == "sma":
        df["ema_fast"] = df["Close"].rolling(fast).mean()
        df["ema_mid"] = df["Close"].rolling(mid).mean()
        df["ema_slow"] = df["Close"].rolling(slow).mean()
    else:
        df["ema_fast"] = df["Close"].ewm(span=fast, adjust=False).mean()
        df["ema_mid"] = df["Close"].ewm(span=mid, adjust=False).mean()
        df["ema_slow"] = df["Close"].ewm(span=slow, adjust=False).mean()
    return df


def detect_ma_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    order_bullish = (df["ema_fast"] > df["ema_mid"]) & (df["ema_mid"] > df["ema_slow"])
    order_bearish = (df["ema_fast"] < df["ema_mid"]) & (df["ema_mid"] < df["ema_slow"])

    price_above_mid = df["Close"] > df["ema_mid"]
    price_below_mid = df["Close"] < df["ema_mid"]

    price_above_all = (df["Close"] > df["ema_fast"]) & (df["Close"] > df["ema_mid"]) & (df["Close"] > df["ema_slow"])
    price_below_all = (df["Close"] < df["ema_fast"]) & (df["Close"] < df["ema_mid"]) & (df["Close"] < df["ema_slow"])

    # 多方 = (排列多頭 且 站上分水嶺60MA) 或 收盤同時站上三條線（價格跌破/站上可蓋過排列本身）
    bullish = (order_bullish & price_above_mid) | price_above_all
    bearish = (order_bearish & price_below_mid) | price_below_all

    df["bullish_alignment"] = bullish
    df["bearish_alignment"] = bearish

    # 剛翻多／剛翻空：狀態從非多(空)轉成多(空)的那一根K棒
    turned_bullish = bullish & ~bullish.shift(1).fillna(False)
    turned_bearish = bearish & ~bearish.shift(1).fillna(False)

    # 出場：原本多頭排列，這根變成糾結（既非多也非空）或直接反轉成空頭
    exit_from_long = bullish.shift(1).fillna(False) & ~bullish
    exit_from_short = bearish.shift(1).fillna(False) & ~bearish

    df["entry_long"] = turned_bullish
    df["entry_short"] = turned_bearish
    df["exit_long"] = exit_from_long
    df["exit_short"] = exit_from_short

    return df


def build_ma_signals(df: pd.DataFrame, fast: int = 20, mid: int = 60, slow: int = 240,
                      ma_type: str = "sma") -> pd.DataFrame:
    df = compute_ma_indicators(df, fast=fast, mid=mid, slow=slow, ma_type=ma_type)
    df = detect_ma_signals(df)
    return df
