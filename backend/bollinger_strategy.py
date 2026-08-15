# -*- coding: utf-8 -*-
"""
布林通道完整策略（依據 mio来了 教學影片重點整理實作）
======================================================
訊號來源：
  A. 擠壓 (Squeeze) -> 擴張突破 (Expansion Breakout)   [趨勢啟動]
  B. 貼軌趨勢跟隨 + 中軌確認離場                          [持倉/出場邏輯]
  C. W底 / M頭 背離 + 頸線突破確認                         [精準抄底/逃頂]

本檔案只包含「策略邏輯」，不含資料下載，方便你替換成任何資料來源
（yfinance / 永豐 Shioaji / 你自己的 crypto screener 等）。
"""

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema


# ----------------------------------------------------------------------
# 1. 指標計算
# ----------------------------------------------------------------------
def compute_indicators(df: pd.DataFrame, bb_window: int = 20, bb_std: float = 2.0,
                        vol_window: int = 20, squeeze_lookback: int = 126) -> pd.DataFrame:
    """輸入需含 Open/High/Low/Close/Volume 欄位（首字大寫）"""
    df = df.copy()
    df["mid"] = df["Close"].rolling(bb_window).mean()
    df["std"] = df["Close"].rolling(bb_window).std()
    df["upper"] = df["mid"] + bb_std * df["std"]
    df["lower"] = df["mid"] - bb_std * df["std"]
    df["bandwidth"] = (df["upper"] - df["lower"]) / df["mid"]

    df["vol_avg"] = df["Volume"].rolling(vol_window).mean()

    # 擠壓判斷：帶寬是否接近過去 N 天（約半年）的最低值
    df["bw_min_lb"] = df["bandwidth"].rolling(squeeze_lookback).min()
    df["is_squeeze"] = df["bandwidth"] <= df["bw_min_lb"] * 1.05
    # 「近期曾經擠壓」：過去 10 天內有出現過擠壓狀態
    df["recent_squeeze"] = df["is_squeeze"].rolling(10).max().fillna(0).astype(bool)

    df["upper_slope"] = df["upper"].diff()
    df["lower_slope"] = df["lower"].diff()

    return df


# ----------------------------------------------------------------------
# 2A. 擠壓 -> 擴張突破訊號
# ----------------------------------------------------------------------
def detect_breakout_signals(df: pd.DataFrame, vol_mult: float = 1.5) -> pd.DataFrame:
    df = df.copy()
    vol_spike = df["Volume"] > df["vol_avg"] * vol_mult

    # 真突破：上下軌同時「向外」張開，代表大行情啟動（而非假突破）
    bands_expanding = (df["upper_slope"] > 0) & (df["lower_slope"] < 0)

    had_squeeze = df["recent_squeeze"].shift(1).fillna(False)

    df["entry_long_breakout"] = (
        had_squeeze & (df["Close"] > df["upper"]) & vol_spike & bands_expanding
    )
    df["entry_short_breakout"] = (
        had_squeeze & (df["Close"] < df["lower"]) & vol_spike & bands_expanding
    )

    # 減速訊號（僅供圖表標註參考）：上升趨勢中下軌由降轉升 -> 動能轉弱
    df["decel_long"] = (df["lower_slope"].shift(1) < 0) & (df["lower_slope"] >= 0) & (df["Close"] > df["mid"])
    df["decel_short"] = (df["upper_slope"].shift(1) > 0) & (df["upper_slope"] <= 0) & (df["Close"] < df["mid"])

    return df


# ----------------------------------------------------------------------
# 2B. W底 / M頭 背離 + 頸線突破確認
# ----------------------------------------------------------------------
def detect_divergence_signals(df: pd.DataFrame, order: int = 5, max_gap: int = 40,
                               confirm_window: int = 20, vol_mult: float = 1.2) -> pd.DataFrame:
    """
    W 底（多頭背離）:
      第一跌: Low 跌破下軌 (恐慌拋售)
      第二跌: 價格創新低，但收盤已收回下軌之內 (賣壓減弱)
      確認: 之後收盤放量突破兩次低點間的反彈高點 (頸線)
    M 頭（空頭背離）為鏡像邏輯。
    """
    df = df.copy()
    df["entry_long_wbottom"] = False
    df["entry_short_mtop"] = False
    df["neckline_long"] = np.nan
    df["neckline_short"] = np.nan

    close = df["Close"].values
    low = df["Low"].values
    high = df["High"].values

    lows_idx = sorted(set(argrelextrema(close, np.less_equal, order=order)[0]))
    highs_idx = sorted(set(argrelextrema(close, np.greater_equal, order=order)[0]))

    n = len(df)

    # --- W 底 ---
    for i in range(1, len(lows_idx)):
        t1, t2 = lows_idx[i - 1], lows_idx[i]
        if not (3 <= t2 - t1 <= max_gap):
            continue
        lower1, lower2 = df["lower"].iloc[t1], df["lower"].iloc[t2]
        if pd.isna(lower1) or pd.isna(lower2):
            continue
        first_break = low[t1] < lower1
        bullish_div = (low[t2] < low[t1]) and (close[t2] >= lower2)
        if first_break and bullish_div:
            neckline = df["Close"].iloc[t1:t2 + 1].max()
            end = min(t2 + confirm_window, n - 1)
            for t3 in range(t2 + 1, end + 1):
                vol_ok = df["Volume"].iloc[t3] > df["vol_avg"].iloc[t3] * vol_mult
                if close[t3] > neckline and vol_ok:
                    df.iloc[t3, df.columns.get_loc("entry_long_wbottom")] = True
                    df.iloc[t3, df.columns.get_loc("neckline_long")] = neckline
                    break

    # --- M 頭 (鏡像) ---
    for i in range(1, len(highs_idx)):
        t1, t2 = highs_idx[i - 1], highs_idx[i]
        if not (3 <= t2 - t1 <= max_gap):
            continue
        upper1, upper2 = df["upper"].iloc[t1], df["upper"].iloc[t2]
        if pd.isna(upper1) or pd.isna(upper2):
            continue
        first_break = high[t1] > upper1
        bearish_div = (high[t2] > high[t1]) and (close[t2] <= upper2)
        if first_break and bearish_div:
            neckline = df["Close"].iloc[t1:t2 + 1].min()
            end = min(t2 + confirm_window, n - 1)
            for t3 in range(t2 + 1, end + 1):
                vol_ok = df["Volume"].iloc[t3] > df["vol_avg"].iloc[t3] * vol_mult
                if close[t3] < neckline and vol_ok:
                    df.iloc[t3, df.columns.get_loc("entry_short_mtop")] = True
                    df.iloc[t3, df.columns.get_loc("neckline_short")] = neckline
                    break

    return df


def build_signals(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    df = compute_indicators(df)
    df = detect_breakout_signals(df)
    df = detect_divergence_signals(df)
    return df


# ----------------------------------------------------------------------
# 3. 事件驅動回測引擎
# ----------------------------------------------------------------------
def run_backtest(df: pd.DataFrame, allow_short: bool = True,
                  fee_bps: float = 5, init_capital: float = 1_000_000.0) -> dict:
    """
    規則:
      進場: 擠壓突破 或 W底/M頭確認 (單一部位，long/short 二選一，不同時持有)
      出場:
        1) 停損 (跌破入場當時的下軌/上軌，或第二低點/高點)
        2) 中軌確認離場：收盤跌破(站上)中軌後，下一根K棒未能收復，才確認離場
      交易成本: 進出各扣 fee_bps (basis points)
    """
    position = 0          # 0=空手, 1=多單, -1=空單
    entry_price = None
    entry_date = None
    stop_price = None
    warn_flag = False     # 是否已出現一次「收盤跌破/站上中軌」的警告

    cash = init_capital
    shares = 0.0
    equity_curve = []
    trades = []

    idx = df.index
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        date = idx[i]

        price = row["Close"]

        # ---------- 空手：找進場機會 ----------
        if position == 0:
            if row.get("entry_long_breakout", False) or row.get("entry_long_wbottom", False):
                position = 1
                entry_price = price
                entry_date = date
                warn_flag = False
                if row.get("entry_long_wbottom", False) and not pd.isna(row.get("neckline_long", np.nan)):
                    stop_price = min(row["lower"], df["Low"].iloc[max(0, i - 15):i].min())
                else:
                    stop_price = row["lower"]
                shares = (cash * (1 - fee_bps / 10000)) / price
                cash = 0.0

            elif allow_short and (row.get("entry_short_breakout", False) or row.get("entry_short_mtop", False)):
                position = -1
                entry_price = price
                entry_date = date
                warn_flag = False
                stop_price = row["upper"]
                shares = (cash * (1 - fee_bps / 10000)) / price
                cash = 0.0

        # ---------- 持有多單 ----------
        elif position == 1:
            exit_now = False
            exit_price = price

            if row["Low"] <= stop_price:
                exit_now = True
                exit_price = stop_price
            else:
                below_mid = row["Close"] < row["mid"]
                if below_mid:
                    if warn_flag:
                        exit_now = True
                        exit_price = row["Close"]
                    else:
                        warn_flag = True
                else:
                    warn_flag = False

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
                warn_flag = False

        # ---------- 持有空單 ----------
        elif position == -1:
            exit_now = False
            exit_price = price

            if row["High"] >= stop_price:
                exit_now = True
                exit_price = stop_price
            else:
                above_mid = row["Close"] > row["mid"]
                if above_mid:
                    if warn_flag:
                        exit_now = True
                        exit_price = row["Close"]
                    else:
                        warn_flag = True
                else:
                    warn_flag = False

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
                warn_flag = False

        # ---------- 記錄權益 ----------
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


# ----------------------------------------------------------------------
# 4. 績效指標
# ----------------------------------------------------------------------
def compute_metrics(equity: pd.Series, trades: pd.DataFrame, init_capital: float, freq_per_year: int = 252) -> dict:
    if len(equity) == 0:
        return {}

    total_return = equity.iloc[-1] / init_capital - 1
    n_years = len(equity) / freq_per_year
    cagr = (equity.iloc[-1] / init_capital) ** (1 / n_years) - 1 if n_years > 0 else np.nan

    daily_ret = equity.pct_change().fillna(0)
    sharpe = (daily_ret.mean() / daily_ret.std()) * np.sqrt(freq_per_year) if daily_ret.std() > 0 else np.nan

    running_max = equity.cummax()
    drawdown = equity / running_max - 1
    max_dd = drawdown.min()

    n_trades = len(trades)
    if n_trades > 0:
        win_trades = trades[trades["pnl"] > 0]
        lose_trades = trades[trades["pnl"] <= 0]
        win_rate = len(win_trades) / n_trades
        gross_profit = win_trades["pnl"].sum()
        gross_loss = -lose_trades["pnl"].sum()
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
        avg_ret = trades["ret"].mean()
    else:
        win_rate = profit_factor = avg_ret = np.nan

    return dict(
        總報酬率=f"{total_return:.2%}",
        年化報酬率_CAGR=f"{cagr:.2%}" if not np.isnan(cagr) else "N/A",
        年化夏普比率=f"{sharpe:.2f}" if not np.isnan(sharpe) else "N/A",
        最大回撤=f"{max_dd:.2%}",
        交易次數=n_trades,
        勝率=f"{win_rate:.1%}" if n_trades else "N/A",
        獲利因子_ProfitFactor=f"{profit_factor:.2f}" if n_trades else "N/A",
        平均單筆報酬=f"{avg_ret:.2%}" if n_trades else "N/A",
    )
