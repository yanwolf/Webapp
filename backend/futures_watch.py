# -*- coding: utf-8 -*-
"""
美股期貨三刀流監控（1H，含盤前盤後）
======================================
仿照參考網站的呈現方式：張飛20MA／關羽60MA／劉備240MA 個別站上/跌破，
以及跟關羽60MA（多空分水嶺）的距離、整體排列判定。

跟「台股個股分析」不同，這裡不限市場（期貨近24小時交易），
且不含基本面/籌碼面資料（期貨沒有本益比、法人買賣超這些概念）。
"""
from datetime import datetime, timedelta
from typing import Optional

from market_data import fetch_ohlcv
from ma_strategy import build_ma_signals

FUTURES_PRESETS = [
    {"label": "ES · 小型標普500", "market": "us", "ticker": "ES=F"},
    {"label": "NQ · 小型那斯達克100", "market": "us", "ticker": "NQ=F"},
]


def _break_status(price: float, ma_val: float) -> str:
    if price > ma_val:
        return "站上"
    if price < ma_val:
        return "跌破"
    return "持平"


def get_ma3_snapshot(market: str, ticker: str, ma_fast: int = 20, ma_mid: int = 60,
                      ma_slow: int = 240, ma_type: str = "sma") -> Optional[dict]:
    """抓1小時K，算三刀流目前狀態，回傳詳細的逐線判斷資訊"""
    start = (datetime.now() - timedelta(days=700)).strftime("%Y-%m-%d")
    df, resolved, notes, err, source = fetch_ohlcv(market, ticker, "1h", start)

    min_needed = int(ma_slow * 1.2)
    if err or df is None or len(df) < min_needed:
        return dict(error=err or f"資料量不足（只有{len(df) if df is not None else 0}根，需要約{min_needed}根）")

    sig = build_ma_signals(df, fast=ma_fast, mid=ma_mid, slow=ma_slow, ma_type=ma_type)
    last = sig.iloc[-1]
    price = float(last["Close"])
    fast_ma, mid_ma, slow_ma = float(last["ema_fast"]), float(last["ema_mid"]), float(last["ema_slow"])

    if last["bullish_alignment"]:
        alignment = "多方排列"
    elif last["bearish_alignment"]:
        alignment = "空方排列"
    else:
        alignment = "排列糾結"

    return dict(
        error=None,
        ticker_resolved=resolved,
        data_source=source,
        price=price,
        price_time=sig.index[-1].strftime("%Y-%m-%d %H:%M"),
        fast_ma=fast_ma, fast_status=_break_status(price, fast_ma),
        mid_ma=mid_ma, mid_status=_break_status(price, mid_ma),
        slow_ma=slow_ma, slow_status=_break_status(price, slow_ma),
        watershed_diff=price - mid_ma,
        alignment=alignment,
    )
