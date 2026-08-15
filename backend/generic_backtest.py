# -*- coding: utf-8 -*-
"""
通用事件驅動回測引擎
====================
給定含有以下欄位的 DataFrame，即可執行回測（單一部位，long/short 二選一）：
  entry_long / entry_short / exit_long / exit_short  (布林值欄位)
停損可用兩種方式之一：
  stop_pct     固定百分比停損（相對進場價）
  stop_col_*   逐列指定停損價格欄位（例如唐奇安通道下軌）
"""
import pandas as pd


def run_generic_backtest(df: pd.DataFrame, allow_short: bool = True,
                          fee_bps: float = 5, init_capital: float = 1_000_000.0,
                          stop_pct: float = None,
                          stop_col_long: str = None, stop_col_short: str = None) -> dict:
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
            if row.get("entry_long", False):
                position = 1
                entry_price = price
                entry_date = date
                if stop_col_long:
                    stop_price = row.get(stop_col_long)
                elif stop_pct:
                    stop_price = entry_price * (1 - stop_pct)
                else:
                    stop_price = None
                shares = (cash * (1 - fee_bps / 10000)) / price
                cash = 0.0
            elif allow_short and row.get("entry_short", False):
                position = -1
                entry_price = price
                entry_date = date
                if stop_col_short:
                    stop_price = row.get(stop_col_short)
                elif stop_pct:
                    stop_price = entry_price * (1 + stop_pct)
                else:
                    stop_price = None
                shares = (cash * (1 - fee_bps / 10000)) / price
                cash = 0.0

        elif position == 1:
            exit_now = False
            exit_price = price
            if stop_price is not None and row["Low"] <= stop_price:
                exit_now = True
                exit_price = stop_price
            elif row.get("exit_long", False):
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
            if stop_price is not None and row["High"] >= stop_price:
                exit_now = True
                exit_price = stop_price
            elif row.get("exit_short", False):
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
    open_position = None
    if position != 0:
        open_position = dict(side="long" if position == 1 else "short",
                              entry_date=entry_date, entry_price=entry_price)
    return dict(equity=equity, trades=pd.DataFrame(trades), open_position=open_position,
                final_capital=equity.iloc[-1] if len(equity) else init_capital)


def run_buy_and_hold(df: pd.DataFrame, fee_bps: float = 5, init_capital: float = 1_000_000.0) -> dict:
    """買進持有基準：第一根K棒買進，最後一根K棒視為結算，全程不出場"""
    idx = df.index
    entry_price = df["Close"].iloc[0]
    entry_date = idx[0]
    shares = (init_capital * (1 - fee_bps / 10000)) / entry_price

    equity = (df["Close"] * shares)
    equity = equity.iloc[1:]
    equity.name = "equity"

    exit_price = df["Close"].iloc[-1]
    exit_date = idx[-1]
    proceeds = shares * exit_price * (1 - fee_bps / 10000)
    pnl = proceeds - shares * entry_price
    trades = pd.DataFrame([dict(entry_date=entry_date, exit_date=exit_date, side="long",
                                 entry_price=entry_price, exit_price=exit_price,
                                 pnl=pnl, ret=exit_price / entry_price - 1)])

    return dict(equity=equity, trades=trades, final_capital=equity.iloc[-1] if len(equity) else init_capital)
