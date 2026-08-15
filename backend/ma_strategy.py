# -*- coding: utf-8 -*-
"""
均線三刀流策略（EMA 快/中/慢三線）
==================================
三刀： EMA_fast（預設20）／EMA_mid（預設60）／EMA_slow（預設240）

多頭排列：EMA_fast > EMA_mid > EMA_slow（三刀向上開散）
空頭排列：EMA_fast < EMA_mid < EMA_slow（三刀向下開散）

進場訊號：
  A. 交叉進場：快線黃金/死亡交叉中線，且大結構（中線 vs 慢線、價格 vs 慢線）仍同方向
  B. 貼刀進場：已處於多頭(空頭)排列中，價格拉回碰到中刀不破（收盤仍在中刀之上/下），
     且當根收紅(黑)確認反彈，視為主升(跌)段中的加碼/回檔進場點

出場訊號：
  快線死亡(黃金)交叉中線 → 出場；另設慢線為停損防線
"""
import numpy as np
import pandas as pd


def compute_ma_indicators(df: pd.DataFrame, fast: int = 20, mid: int = 60, slow: int = 240) -> pd.DataFrame:
    df = df.copy()
    df["ema_fast"] = df["Close"].ewm(span=fast, adjust=False).mean()
    df["ema_mid"] = df["Close"].ewm(span=mid, adjust=False).mean()
    df["ema_slow"] = df["Close"].ewm(span=slow, adjust=False).mean()
    return df


def detect_ma_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    bullish_struct = (df["ema_fast"] > df["ema_mid"]) & (df["ema_mid"] > df["ema_slow"])
    bearish_struct = (df["ema_fast"] < df["ema_mid"]) & (df["ema_mid"] < df["ema_slow"])
    df["bullish_alignment"] = bullish_struct
    df["bearish_alignment"] = bearish_struct

    golden_cross = (df["ema_fast"].shift(1) <= df["ema_mid"].shift(1)) & (df["ema_fast"] > df["ema_mid"])
    death_cross = (df["ema_fast"].shift(1) >= df["ema_mid"].shift(1)) & (df["ema_fast"] < df["ema_mid"])
    df["golden_cross"] = golden_cross
    df["death_cross"] = death_cross

    # A. 交叉進場：大結構仍同方向
    df["entry_long_cross"] = golden_cross & (df["ema_mid"] > df["ema_slow"]) & (df["Close"] > df["ema_slow"])
    df["entry_short_cross"] = death_cross & (df["ema_mid"] < df["ema_slow"]) & (df["Close"] < df["ema_slow"])

    # B. 貼刀進場：多頭(空頭)排列中拉回中刀不破，收紅(黑)確認反彈
    was_bullish = bullish_struct.shift(1).fillna(False)
    touched_mid_support = (df["Low"] <= df["ema_mid"]) & (df["Close"] > df["ema_mid"])
    bounce_up = df["Close"] > df["Close"].shift(1)
    df["entry_long_pullback"] = was_bullish & touched_mid_support & bounce_up & (df["Close"] > df["ema_fast"])

    was_bearish = bearish_struct.shift(1).fillna(False)
    touched_mid_resist = (df["High"] >= df["ema_mid"]) & (df["Close"] < df["ema_mid"])
    bounce_down = df["Close"] < df["Close"].shift(1)
    df["entry_short_pullback"] = was_bearish & touched_mid_resist & bounce_down & (df["Close"] < df["ema_fast"])

    return df


def build_ma_signals(df: pd.DataFrame, fast: int = 20, mid: int = 60, slow: int = 240) -> pd.DataFrame:
    df = compute_ma_indicators(df, fast=fast, mid=mid, slow=slow)
    df = detect_ma_signals(df)
    return df


def run_backtest_ma(df: pd.DataFrame, allow_short: bool = True,
                     fee_bps: float = 5, init_capital: float = 1_000_000.0) -> dict:
    """
    規則:
      進場: 交叉進場 或 貼刀進場（單一部位，long/short 二選一）
      出場: 快線死亡(黃金)交叉中線；停損則設在慢線
    """
    position = 0
    entry_price = None
    entry_date = None
    stop_price = None

    cash = init_capital
    shares = 0.0
    equity_curve = []
    trades = []

    idx = df.index
    for i in range(1, len(df)):
        row = df.iloc[i]
        date = idx[i]
        price = row["Close"]

        if position == 0:
            if row.get("entry_long_cross", False) or row.get("entry_long_pullback", False):
                position = 1
                entry_price = price
                entry_date = date
                stop_price = row["ema_slow"]
                shares = (cash * (1 - fee_bps / 10000)) / price
                cash = 0.0
            elif allow_short and (row.get("entry_short_cross", False) or row.get("entry_short_pullback", False)):
                position = -1
                entry_price = price
                entry_date = date
                stop_price = row["ema_slow"]
                shares = (cash * (1 - fee_bps / 10000)) / price
                cash = 0.0

        elif position == 1:
            exit_now = False
            exit_price = price
            if row["Low"] <= stop_price:
                exit_now = True
                exit_price = stop_price
            elif row.get("death_cross", False):
                exit_now = True
                exit_price = price

            if exit_now:
                proceeds = shares * exit_price * (1 - fee_bps / 10000)
                pnl = proceeds - (shares * entry_price)
                trades.append(dict(entry_date=entry_date, exit_date=date, side="long",
                                    entry_price=entry_price, exit_price=exit_price,
                                    pnl=pnl, ret=exit_price / entry_price - 1))
                cash = proceeds
                shares = 0.0
                position = 0
                stop_price = None

        elif position == -1:
            exit_now = False
            exit_price = price
            if row["High"] >= stop_price:
                exit_now = True
                exit_price = stop_price
            elif row.get("golden_cross", False):
                exit_now = True
                exit_price = price

            if exit_now:
                proceeds = shares * (2 * entry_price - exit_price) * (1 - fee_bps / 10000)
                pnl = proceeds - (shares * entry_price)
                trades.append(dict(entry_date=entry_date, exit_date=date, side="short",
                                    entry_price=entry_price, exit_price=exit_price,
                                    pnl=pnl, ret=entry_price / exit_price - 1))
                cash = proceeds
                shares = 0.0
                position = 0
                stop_price = None

        if position == 1:
            mtm = shares * price
        elif position == -1:
            mtm = shares * (2 * entry_price - price)
        else:
            mtm = cash
        equity_curve.append(mtm if position != 0 else cash)

    equity = pd.Series(equity_curve, index=idx[1:], name="equity")
    return dict(equity=equity, trades=pd.DataFrame(trades),
                final_capital=equity.iloc[-1] if len(equity) else init_capital)
