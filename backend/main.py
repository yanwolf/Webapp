# -*- coding: utf-8 -*-
"""
布林通道 / 均線三刀流 策略回測 API
==================================
POST /api/backtest  執行回測，回傳指標、走勢+指標序列、權益曲線、逐筆交易
GET  /api/health     健康檢查
"""
import math
import traceback
from datetime import date, datetime, timedelta
from typing import Optional, Literal, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from bollinger_strategy import (
    compute_indicators, detect_breakout_signals, detect_divergence_signals,
    run_backtest, compute_metrics,
)
from ma_strategy import build_ma_signals, run_backtest_ma

app = FastAPI(title="Bollinger / MA3 Backtest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MIN_BARS = 60

INTERVAL_META = {
    "1d": {"yf_interval": "1d", "max_lookback_days": None, "resample": None, "bars_per_day": 1},
    "4h": {"yf_interval": "1h", "max_lookback_days": 729, "resample": "4h", "bars_per_day": 1.625},
    "1h": {"yf_interval": "1h", "max_lookback_days": 729, "resample": None, "bars_per_day": 6.5},
    "15m": {"yf_interval": "15m", "max_lookback_days": 59, "resample": None, "bars_per_day": 26},
    "5m": {"yf_interval": "5m", "max_lookback_days": 59, "resample": None, "bars_per_day": 78},
    "1m": {"yf_interval": "1m", "max_lookback_days": 7, "resample": None, "bars_per_day": 390},
}

SQUEEZE_MONTHS_IN_DAYS = 126


class BacktestRequest(BaseModel):
    market: Literal["us", "tw", "crypto"] = Field(..., description="市場別")
    ticker: str = Field(..., description="代碼，例如 AAPL / 2330 / BTC / ^TWII")
    strategy: Literal["bollinger", "ma3"] = Field("bollinger", description="策略類型")
    interval: Literal["1d", "4h", "1h", "15m", "5m", "1m"] = Field("1d", description="K線週期")
    start: str = Field("2015-01-01", description="回測起始日 YYYY-MM-DD")
    end: Optional[str] = Field(None, description="回測結束日，預設今天")
    capital: float = Field(1_000_000, gt=0)
    allow_short: bool = Field(True)
    # 布林通道參數
    bb_window: int = Field(20, ge=5, le=100)
    bb_std: float = Field(2.0, ge=0.5, le=4.0)
    vol_mult: float = Field(1.5, ge=1.0, le=5.0)
    # 均線三刀流參數
    ma_fast: int = Field(20, ge=2, le=200)
    ma_mid: int = Field(60, ge=5, le=400)
    ma_slow: int = Field(240, ge=10, le=800)


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


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/backtest")
def backtest(req: BacktestRequest):
    resolved = resolve_ticker(req.market, req.ticker)
    end = req.end or datetime.today().strftime("%Y-%m-%d")

    interval_key = req.interval
    meta = INTERVAL_META[interval_key]
    yf_interval = meta["yf_interval"]

    effective_start, range_note = clamp_start_date(req.start, end, interval_key)

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
            raise HTTPException(status_code=502, detail=f"抓取資料時發生錯誤: {e}")

    if raw is None or raw.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"抓不到「{resolved}」在「{interval_key}」週期下的資料。可能是 Yahoo Finance 暫時封鎖了伺服器連線"
                f"（過幾分鐘再試一次），也可能是這個代碼沒有提供分鐘/小時線資料（常見於部分台股/加密貨幣），"
                f"建議先切回日K確認代碼本身沒問題。"
            )
        )

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw[["Open", "High", "Low", "Close", "Volume"]].dropna()

    if meta["resample"]:
        df = df.resample(meta["resample"]).agg({
            "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum",
        }).dropna()

    min_bars_needed = MIN_BARS
    if req.strategy == "ma3":
        # 三刀流需要慢線的資料窗口才有意義，至少要有 1.2 倍慢線週期的K棒數
        min_bars_needed = max(MIN_BARS, int(req.ma_slow * 1.2))

    if len(df) < min_bars_needed:
        raise HTTPException(
            status_code=422,
            detail=(
                f"「{resolved}」在「{interval_key}」週期下只抓到 {len(df)} 根K棒，過少無法計算指標"
                f"（此設定至少需要約 {min_bars_needed} 根）。分鐘/小時線的歷史資料本來就比日K短很多，"
                f"請試著縮短回測區間、改用較長的K線週期，或（三刀流）調小慢線週期。"
            )
        )

    strategy_note = None
    try:
        if req.strategy == "ma3":
            sig_df = build_ma_signals(df, fast=req.ma_fast, mid=req.ma_mid, slow=req.ma_slow)
            res = run_backtest_ma(sig_df, allow_short=req.allow_short, init_capital=req.capital)
            overlay_keys = ["ema_fast", "ema_mid", "ema_slow"]
        else:
            auto_squeeze_lookback = max(20, int(SQUEEZE_MONTHS_IN_DAYS * meta["bars_per_day"]))
            squeeze_lookback = min(auto_squeeze_lookback, max(20, int(len(df) * 0.4)))
            strategy_note = f"squeeze_lookback={squeeze_lookback}"

            sig_df = compute_indicators(df, bb_window=req.bb_window, bb_std=req.bb_std,
                                         squeeze_lookback=squeeze_lookback)
            sig_df = detect_breakout_signals(sig_df, vol_mult=req.vol_mult)
            sig_df = detect_divergence_signals(sig_df)
            res = run_backtest(sig_df, allow_short=req.allow_short, init_capital=req.capital)
            overlay_keys = ["mid", "upper", "lower"]

        metrics = compute_metrics(
            res["equity"], res["trades"], init_capital=req.capital,
            freq_per_year=int(252 * meta["bars_per_day"]),
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"回測執行失敗: {e}")

    def fmt_ts(ts):
        if interval_key == "1d":
            return ts.strftime("%Y-%m-%d")
        return ts.strftime("%Y-%m-%d %H:%M")

    price_series = []
    for ts, row in sig_df.iterrows():
        item = {"date": fmt_ts(ts), "close": sanitize(row["Close"])}
        for k in overlay_keys:
            item[k] = sanitize(row[k])
        price_series.append(item)

    equity_series = [
        {"date": fmt_ts(ts), "equity": sanitize(v)}
        for ts, v in res["equity"].items()
    ]

    trades = []
    if len(res["trades"]):
        for _, r in res["trades"].iterrows():
            trades.append({
                "entry_date": fmt_ts(r["entry_date"]),
                "exit_date": fmt_ts(r["exit_date"]),
                "side": r["side"],
                "entry_price": sanitize(r["entry_price"]),
                "exit_price": sanitize(r["exit_price"]),
                "pnl": sanitize(r["pnl"]),
                "ret": sanitize(r["ret"]),
            })

    notes = [n for n in [range_note] if n]

    return {
        "ticker_resolved": resolved,
        "strategy": req.strategy,
        "interval": interval_key,
        "overlay_keys": overlay_keys,
        "data_points": len(df),
        "date_range": [fmt_ts(df.index[0]), fmt_ts(df.index[-1])],
        "notes": notes,
        "metrics": metrics,
        "price_series": price_series,
        "equity_series": equity_series,
        "trades": trades,
    }
