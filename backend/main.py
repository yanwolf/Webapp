# -*- coding: utf-8 -*-
"""
布林通道策略回測 API
====================
POST /api/backtest  執行回測，回傳指標、K線+通道序列、權益曲線、逐筆交易
GET  /api/health     健康檢查
"""
import math
import traceback
from datetime import date, datetime
from typing import Optional, Literal

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

app = FastAPI(title="Bollinger Band Backtest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 個人工具用途；如需限制請改成你的前端網域
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# 請求 / 回應模型
# ----------------------------------------------------------------------
class BacktestRequest(BaseModel):
    market: Literal["us", "tw", "crypto"] = Field(..., description="市場別")
    ticker: str = Field(..., description="代碼，例如 AAPL / 2330 / BTC")
    start: str = Field("2015-01-01", description="回測起始日 YYYY-MM-DD")
    end: Optional[str] = Field(None, description="回測結束日，預設今天")
    capital: float = Field(1_000_000, gt=0)
    allow_short: bool = Field(True)
    bb_window: int = Field(20, ge=5, le=100)
    bb_std: float = Field(2.0, ge=0.5, le=4.0)
    vol_mult: float = Field(1.5, ge=1.0, le=5.0)


# ----------------------------------------------------------------------
# 代碼解析
# ----------------------------------------------------------------------
def resolve_ticker(market: str, ticker: str) -> str:
    t = ticker.strip().upper()
    if market == "tw":
        if not (t.endswith(".TW") or t.endswith(".TWO")):
            t = f"{t}.TW"
    elif market == "crypto":
        if "-USD" not in t and "-USDT" not in t:
            t = f"{t}-USD"
    return t


def sanitize(value):
    """把 NaN / Inf / numpy 型別轉成 JSON 安全值"""
    if isinstance(value, (np.floating, float)):
        v = float(value)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (pd.Timestamp, date, datetime)):
        return value.strftime("%Y-%m-%d")
    return value


# ----------------------------------------------------------------------
# API
# ----------------------------------------------------------------------
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/backtest")
def backtest(req: BacktestRequest):
    resolved = resolve_ticker(req.market, req.ticker)
    end = req.end or datetime.today().strftime("%Y-%m-%d")

    try:
        raw = yf.download(resolved, start=req.start, end=end,
                           auto_adjust=True, progress=False)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"抓取資料時發生錯誤: {e}")

    if raw is None or raw.empty:
        raise HTTPException(
            status_code=404,
            detail=f"抓不到「{resolved}」的資料，請確認代碼是否正確、市場別是否選對，或該區間是否有交易資料。"
        )

    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw[["Open", "High", "Low", "Close", "Volume"]].dropna()

    if len(df) < 130:
        raise HTTPException(
            status_code=422,
            detail=f"「{resolved}」資料筆數只有 {len(df)} 筆，過少無法計算擠壓等指標（至少需要約130個交易日）。"
        )

    try:
        sig_df = compute_indicators(df, bb_window=req.bb_window, bb_std=req.bb_std)
        sig_df = detect_breakout_signals(sig_df, vol_mult=req.vol_mult)
        sig_df = detect_divergence_signals(sig_df)

        res = run_backtest(sig_df, allow_short=req.allow_short, init_capital=req.capital)
        metrics = compute_metrics(res["equity"], res["trades"], init_capital=req.capital)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"回測執行失敗: {e}")

    price_series = []
    for ts, row in sig_df.iterrows():
        price_series.append({
            "date": ts.strftime("%Y-%m-%d"),
            "close": sanitize(row["Close"]),
            "mid": sanitize(row["mid"]),
            "upper": sanitize(row["upper"]),
            "lower": sanitize(row["lower"]),
        })

    equity_series = [
        {"date": ts.strftime("%Y-%m-%d"), "equity": sanitize(v)}
        for ts, v in res["equity"].items()
    ]

    trades = []
    if len(res["trades"]):
        for _, r in res["trades"].iterrows():
            trades.append({
                "entry_date": sanitize(r["entry_date"]),
                "exit_date": sanitize(r["exit_date"]),
                "side": r["side"],
                "entry_price": sanitize(r["entry_price"]),
                "exit_price": sanitize(r["exit_price"]),
                "pnl": sanitize(r["pnl"]),
                "ret": sanitize(r["ret"]),
            })

    return {
        "ticker_resolved": resolved,
        "data_points": len(df),
        "date_range": [df.index[0].strftime("%Y-%m-%d"), df.index[-1].strftime("%Y-%m-%d")],
        "metrics": metrics,
        "price_series": price_series,
        "equity_series": equity_series,
        "trades": trades,
    }
