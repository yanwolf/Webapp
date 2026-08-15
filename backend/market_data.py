# -*- coding: utf-8 -*-
"""共用的資料抓取 / 代碼解析邏輯（回測 API 與背景排程共用）"""
import math
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

INTERVAL_META = {
    "1d": {"yf_interval": "1d", "max_lookback_days": None, "resample": None, "bars_per_day": 1},
    "4h": {"yf_interval": "1h", "max_lookback_days": 729, "resample": "4h", "bars_per_day": 1.625},
    "1h": {"yf_interval": "1h", "max_lookback_days": 729, "resample": None, "bars_per_day": 6.5},
    "15m": {"yf_interval": "15m", "max_lookback_days": 59, "resample": None, "bars_per_day": 26},
    "5m": {"yf_interval": "5m", "max_lookback_days": 59, "resample": None, "bars_per_day": 78},
    "1m": {"yf_interval": "1m", "max_lookback_days": 7, "resample": None, "bars_per_day": 390},
}

# 各週期的K棒時長（分鐘），用來判斷「最新一根K棒是否已經走完」
INTERVAL_MINUTES = {"1h": 60, "4h": 240, "15m": 15, "5m": 5, "1m": 1}


def resolve_ticker(market: str, ticker: str) -> str:
    t = ticker.strip().upper()
    if market == "tw":
        if t.startswith("^"):
            return t
        if not (t.endswith(".TW") or t.endswith(".TWO")):
            t = f"{t}.TW"
    elif market == "crypto":
        if "-USD" not in t and "-USDT" not in t:
            t = f"{t}-USD"
    return t


def sanitize(value):
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (pd.Timestamp, date, datetime)):
        return value.strftime("%Y-%m-%d")
    return value


def clamp_start_date(requested_start: str, end_str: str, interval_key: str) -> Tuple[str, Optional[str]]:
    meta = INTERVAL_META[interval_key]
    max_days = meta["max_lookback_days"]
    if max_days is None:
        return requested_start, None

    end_dt = datetime.strptime(end_str, "%Y-%m-%d") if end_str else datetime.today()
    earliest_allowed = end_dt - timedelta(days=max_days)
    requested_dt = datetime.strptime(requested_start, "%Y-%m-%d")

    if requested_dt < earliest_allowed:
        note = (
            f"「{interval_key}」週期的資料，Yahoo Finance 最多只提供回溯約 {max_days} 天，"
            f"已自動把起始日期調整為 {earliest_allowed.strftime('%Y-%m-%d')}。"
        )
        return earliest_allowed.strftime("%Y-%m-%d"), note
    return requested_start, None


def fetch_ohlcv(market: str, ticker: str, interval: str, start: str, end: Optional[str] = None):
    """
    回傳 (df, resolved_ticker, notes, error_detail)
    df 為 None 代表抓取失敗，error_detail 會有原因說明
    """
    resolved = resolve_ticker(market, ticker)
    end = end or datetime.today().strftime("%Y-%m-%d")
    meta = INTERVAL_META[interval]
    yf_interval = meta["yf_interval"]

    effective_start, range_note = clamp_start_date(start, end, interval)

    try:
        raw = yf.download(resolved, start=effective_start, end=end,
                           interval=yf_interval, auto_adjust=True, progress=False)
    except Exception:
        raw = None

    if raw is None or raw.empty:
        try:
            raw = yf.Ticker(resolved).history(start=effective_start, end=end,
                                               interval=yf_interval, auto_adjust=True)
        except Exception as e:
            return None, resolved, [], f"抓取資料時發生錯誤: {e}"

    if raw is None or raw.empty:
        return None, resolved, [], (
            f"抓不到「{resolved}」在「{interval}」週期下的資料。可能是 Yahoo Finance 暫時封鎖了伺服器連線，"
            f"也可能是這個代碼沒有提供分鐘/小時線資料。"
        )

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw[["Open", "High", "Low", "Close", "Volume"]].dropna()

    if meta["resample"]:
        df = df.resample(meta["resample"]).agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum",
        }).dropna()

    notes = [n for n in [range_note] if n]
    return df, resolved, notes, None


def drop_forming_bar(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    """若最後一根K棒尚未走完（例如即時抓取intraday資料時抓到當下正在形成的K棒），先丟棄避免誤判訊號"""
    if interval not in INTERVAL_MINUTES or df is None or len(df) == 0:
        return df
    try:
        from datetime import timezone
        last_ts = df.index[-1]
        bar_minutes = INTERVAL_MINUTES[interval]
        bar_end = last_ts + timedelta(minutes=bar_minutes)
        now = datetime.now(timezone.utc)
        if last_ts.tzinfo is not None:
            bar_end = bar_end.astimezone(timezone.utc) if bar_end.tzinfo else bar_end.tz_localize("UTC")
        else:
            now = now.replace(tzinfo=None)
        if bar_end > now:
            return df.iloc[:-1]
    except Exception:
        pass
    return df
