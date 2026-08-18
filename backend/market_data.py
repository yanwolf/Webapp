# -*- coding: utf-8 -*-
"""
市場資料抓取（多資料源 + 自動退回機制）
==========================================
優先順序：
  台股 (日K)   → FinMind          失敗/未設定Token → yfinance
  美股         → Twelve Data      失敗/未設定Key   → yfinance
  加密貨幣     → Binance 公開API  失敗              → yfinance
  台股 (分K/小時K)、指數(^開頭)   → 直接用 yfinance（FinMind 分K資料可靠度未驗證，暫不啟用）

環境變數：
  FINMIND_API_TOKEN    FinMind 的 API Token（免費註冊 https://finmindtrade.com）
  TWELVE_DATA_API_KEY  Twelve Data 的 API Key（免費註冊 https://twelvedata.com）
  Binance 不需要 API Key，公開行情資料直接可用
"""
import math
import os
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import requests
import yfinance as yf

FINMIND_TOKEN = os.environ.get("FINMIND_API_TOKEN", "")
FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"

TWELVE_DATA_KEY = os.environ.get("TWELVE_DATA_API_KEY", "")
TWELVE_DATA_URL = "https://api.twelvedata.com/time_series"
TWELVE_DATA_INTERVAL = {"1d": "1day", "4h": "4h", "1h": "1h", "15m": "15min", "5m": "5min", "1m": "1min"}

BINANCE_URL = "https://api.binance.com/api/v3/klines"
BINANCE_INTERVAL = {"1d": "1d", "4h": "4h", "1h": "1h", "15m": "15m", "5m": "5m", "1m": "1m"}

INTERVAL_META = {
    "1d": {"yf_interval": "1d", "max_lookback_days": None, "resample": None, "bars_per_day": 1},
    "4h": {"yf_interval": "1h", "max_lookback_days": 729, "resample": "4h", "bars_per_day": 1.625},
    "1h": {"yf_interval": "1h", "max_lookback_days": 729, "resample": None, "bars_per_day": 6.5},
    "15m": {"yf_interval": "15m", "max_lookback_days": 59, "resample": None, "bars_per_day": 26},
    "5m": {"yf_interval": "5m", "max_lookback_days": 59, "resample": None, "bars_per_day": 78},
    "1m": {"yf_interval": "1m", "max_lookback_days": 7, "resample": None, "bars_per_day": 390},
}

INTERVAL_MINUTES = {"1h": 60, "4h": 240, "15m": 15, "5m": 5, "1m": 1}

REQUIRED_COLS = ["Open", "High", "Low", "Close", "Volume"]


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


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return None
    df = df[REQUIRED_COLS].dropna()
    return df if len(df) else None


# ---------------------------------------------------------------- FinMind (台股 日K)
def _fetch_finmind_daily(ticker: str, start: str, end: str) -> Optional[pd.DataFrame]:
    if not FINMIND_TOKEN:
        return None
    data_id = ticker.strip().upper().replace(".TWO", "").replace(".TW", "")
    try:
        r = requests.get(
            FINMIND_URL,
            headers={"Authorization": f"Bearer {FINMIND_TOKEN}"},
            params={"dataset": "TaiwanStockPrice", "data_id": data_id,
                    "start_date": start, "end_date": end or ""},
            timeout=15,
        )
        j = r.json()
        if j.get("status") != 200 or not j.get("data"):
            return None
        df = pd.DataFrame(j["data"])
        if df.empty:
            return None
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        df = df.rename(columns={
            "open": "Open", "max": "High", "min": "Low", "close": "Close", "Trading_Volume": "Volume",
        })
        return _clean_df(df)
    except Exception:
        return None


# ---------------------------------------------------------------- Twelve Data (美股)
def _fetch_twelve_data(ticker: str, interval: str, start: str, end: str) -> Optional[pd.DataFrame]:
    if not TWELVE_DATA_KEY:
        return None
    td_interval = TWELVE_DATA_INTERVAL.get(interval, "1day")
    try:
        r = requests.get(
            TWELVE_DATA_URL,
            params={"symbol": ticker.strip().upper(), "interval": td_interval,
                    "start_date": start, "end_date": end or "",
                    "outputsize": 5000, "order": "ASC", "apikey": TWELVE_DATA_KEY},
            timeout=15,
        )
        j = r.json()
        if j.get("status") != "ok" or not j.get("values"):
            return None
        df = pd.DataFrame(j["values"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.set_index("datetime").sort_index()
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
        return _clean_df(df)
    except Exception:
        return None


# ---------------------------------------------------------------- Binance (加密貨幣)
def _resolve_binance_symbol(ticker: str) -> str:
    t = ticker.strip().upper()
    for suf in ("-USDT", "-USD", "USDT", "USD"):
        if t.endswith(suf):
            t = t[: -len(suf)]
            break
    return f"{t}USDT"


def _fetch_binance(ticker: str, interval: str, start: str, end: str) -> Optional[pd.DataFrame]:
    symbol = _resolve_binance_symbol(ticker)
    biv = BINANCE_INTERVAL.get(interval, "1d")
    try:
        start_ms = int(datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp() * 1000)
        end_dt = datetime.strptime(end, "%Y-%m-%d") if end else datetime.now(timezone.utc)
        end_ms = int(end_dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
    except Exception:
        return None

    all_rows = []
    cur = start_ms
    for _ in range(50):  # 最多分50批抓取，避免無窮迴圈
        try:
            r = requests.get(BINANCE_URL, params={
                "symbol": symbol, "interval": biv, "startTime": cur, "endTime": end_ms, "limit": 1000,
            }, timeout=15)
            rows = r.json()
        except Exception:
            break
        if not isinstance(rows, list) or not rows:
            break
        all_rows.extend(rows)
        last_open_time = rows[-1][0]
        if len(rows) < 1000 or last_open_time >= end_ms:
            break
        cur = last_open_time + 1

    if not all_rows:
        return None

    df = pd.DataFrame(all_rows, columns=[
        "open_time", "open", "high", "low", "close", "volume", "close_time",
        "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
    ])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.set_index("open_time").sort_index()
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    return _clean_df(df)


# ---------------------------------------------------------------- yfinance（備援）
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


def _fetch_yfinance(market: str, ticker: str, interval: str, start: str, end: str):
    resolved = resolve_ticker(market, ticker)
    meta = INTERVAL_META[interval]
    yf_interval = meta["yf_interval"]

    effective_start, range_note = clamp_start_date(start, end, interval)

    # yfinance 的 end 參數是「不包含當天」的，直接傳今天的日期會系統性漏掉今天整天的資料，
    # 所以內部請求時要多加一天，確保今天的資料真的抓得到
    try:
        end_plus_one = (datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    except Exception:
        end_plus_one = end

    try:
        raw = yf.download(resolved, start=effective_start, end=end_plus_one,
                           interval=yf_interval, auto_adjust=True, progress=False)
    except Exception:
        raw = None

    if raw is None or raw.empty:
        try:
            raw = yf.Ticker(resolved).history(start=effective_start, end=end_plus_one,
                                               interval=yf_interval, auto_adjust=True)
        except Exception:
            raw = None

    if raw is None or raw.empty:
        return None, resolved, [], (
            f"抓不到「{resolved}」在「{interval}」週期下的資料。可能是 Yahoo Finance 暫時封鎖了伺服器連線，"
            f"也可能是這個代碼沒有提供分鐘/小時線資料。"
        )

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw[REQUIRED_COLS].dropna()

    if meta["resample"]:
        df = df.resample(meta["resample"]).agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum",
        }).dropna()

    notes = [n for n in [range_note] if n]
    return df, resolved, notes, None


# ---------------------------------------------------------------- 統一入口
def fetch_ohlcv(market: str, ticker: str, interval: str, start: str, end: Optional[str] = None):
    """
    回傳 (df, resolved_ticker, notes, error_detail, source)
    依優先順序嘗試新資料源，失敗則自動退回 yfinance。
    """
    resolved = resolve_ticker(market, ticker)
    end = end or datetime.today().strftime("%Y-%m-%d")
    is_index = ticker.strip().startswith("^")

    df = None
    source = None

    if market == "tw" and interval == "1d" and not is_index:
        df = _fetch_finmind_daily(ticker, start, end)
        if df is not None:
            source = "finmind"

    if df is None and market == "us":
        df = _fetch_twelve_data(ticker, interval, start, end)
        if df is not None:
            source = "twelve_data"

    if df is None and market == "crypto":
        df = _fetch_binance(ticker, interval, start, end)
        if df is not None:
            source = "binance"

    if df is not None:
        return df, resolved, [], None, source

    # 全部新資料源都沒有回傳（未設定Key、暫時性錯誤、代碼查不到等），退回 yfinance
    df, resolved, notes, err = _fetch_yfinance(market, ticker, interval, start, end)
    return df, resolved, notes, err, ("yfinance" if df is not None else None)


def drop_forming_bar(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    """若最後一根K棒尚未走完，先丟棄避免誤判訊號"""
    if interval not in INTERVAL_MINUTES or df is None or len(df) == 0:
        return df
    try:
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
