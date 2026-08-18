# -*- coding: utf-8 -*-
"""
台股個股分析：整合8種策略的「目前狀態」+ 基本面資訊
======================================================
不做「買/不買」的斷言式結論，只把各項指標現況攤開，讓使用者自己判斷。

技術面：把每個策略跑到「今天」，看策略邏輯目前會持有多單/空單/空手
基本面：本益比/股價淨值比/殖利率 + 三大法人近5日買賣超（需要 FinMind Token）
"""
import time
from datetime import datetime, timedelta
from typing import Optional

import requests

from market_data import FINMIND_TOKEN, FINMIND_URL
from strategy_runner import run_strategy, DEFAULT_PARAMS, STRATEGY_LABELS, ALL_SIGNAL_STRATEGIES

_fundamentals_cache = {}
CACHE_TTL_SECONDS = 3600  # 基本面資料變動不快，快取1小時


def _describe_state(strategy: str, row) -> str:
    """依最新一根K棒的指標數值，產生一句話描述目前狀態（純敘述，不下結論）"""
    try:
        if strategy == "bollinger":
            if row["Close"] > row["upper"]:
                return f"收盤價已站上布林上軌（上軌 {row['upper']:.1f}）"
            if row["Close"] < row["lower"]:
                return f"收盤價已跌破布林下軌（下軌 {row['lower']:.1f}）"
            pos = "偏上緣" if row["Close"] > row["mid"] else "偏下緣"
            return f"收盤價在通道中軌{pos}（中軌 {row['mid']:.1f}）"
        if strategy == "ma3":
            if row["ema_fast"] > row["ema_mid"] > row["ema_slow"]:
                return "快中慢刀呈多頭排列"
            if row["ema_fast"] < row["ema_mid"] < row["ema_slow"]:
                return "快中慢刀呈空頭排列"
            return "三線糾結，方向不明"
        if strategy == "ma_cross":
            rel = "之上" if row["ma_fast"] > row["ma_slow"] else "之下"
            return f"快線目前在慢線{rel}"
        if strategy == "donchian":
            return f"目前收盤 {row['Close']:.1f}，通道上緣 {row['donch_upper_entry']:.1f}／下緣 {row['donch_lower_entry']:.1f}"
        if strategy == "rsi":
            return f"RSI 目前 {row['rsi']:.1f}"
        if strategy == "macd":
            rel = "上方（動能偏多）" if row["macd"] > row["macd_signal"] else "下方（動能偏空）"
            return f"MACD 在訊號線{rel}"
        if strategy == "atr_channel":
            pos = "偏上緣" if row["Close"] > row["atr_mid"] else "偏下緣"
            return f"收盤價在ATR通道中軌{pos}（中軌 {row['atr_mid']:.1f}）"
        if strategy == "fvg":
            return "近期缺口偵測邏輯以進出場訊號為準，暫無額外描述"
    except Exception:
        pass
    return ""


def analyze_signals(df, capital: float = 1_000_000.0):
    """對全部8種策略跑到最新一根K棒，回傳每個策略目前的持倉狀態"""
    signals = []
    tally = dict(bullish=0, bearish=0, neutral=0)
    cur_price = float(df["Close"].iloc[-1])

    for strat in ALL_SIGNAL_STRATEGIES:
        params = DEFAULT_PARAMS.get(strat, {})
        try:
            out = run_strategy(df, strat, params, allow_short=True, capital=capital, bars_per_day=1)
        except Exception:
            continue

        op = out["res"].get("open_position")
        last_row = out["sig_df"].iloc[-1]

        if op:
            side = op["side"]
            entry_price = float(op["entry_price"])
            entry_date = op["entry_date"].strftime("%Y-%m-%d")
            if side == "long":
                unrealized = cur_price / entry_price - 1
                tally["bullish"] += 1
            else:
                unrealized = entry_price / cur_price - 1
                tally["bearish"] += 1
        else:
            side, entry_price, entry_date, unrealized = "flat", None, None, None
            tally["neutral"] += 1

        signals.append(dict(
            strategy=strat,
            strategy_label=STRATEGY_LABELS.get(strat, strat),
            position=side,
            entry_date=entry_date,
            entry_price=entry_price,
            unrealized_return=unrealized,
            detail=_describe_state(strat, last_row),
        ))

    return signals, tally


# ---------------------------------------------------------------- 基本面 (FinMind)
def _fm_get(dataset: str, data_id: str, start_date: str):
    if not FINMIND_TOKEN:
        return None
    try:
        r = requests.get(
            FINMIND_URL,
            headers={"Authorization": f"Bearer {FINMIND_TOKEN}"},
            params={"dataset": dataset, "data_id": data_id, "start_date": start_date},
            timeout=15,
        )
        j = r.json()
        if j.get("status") != 200:
            return None
        return j.get("data", [])
    except Exception:
        return None


def fetch_tw_fundamentals(ticker: str) -> Optional[dict]:
    if not FINMIND_TOKEN:
        return None

    data_id = ticker.strip().upper().replace(".TWO", "").replace(".TW", "")
    cache_key = data_id
    now = time.time()
    cached = _fundamentals_cache.get(cache_key)
    if cached and now - cached["ts"] < CACHE_TTL_SECONDS:
        return cached["data"]

    start_30 = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    start_10 = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    result = dict(per=None, pbr=None, dividend_yield=None, per_date=None,
                  institutional_net_5d=None, institutional_days=0)

    per_data = _fm_get("TaiwanStockPER", data_id, start_30)
    if per_data:
        latest = per_data[-1]
        result["per"] = latest.get("PER")
        result["pbr"] = latest.get("PBR")
        result["dividend_yield"] = latest.get("dividend_yield")
        result["per_date"] = latest.get("date")

    inst_data = _fm_get("InstitutionalInvestorsBuySell", data_id, start_10)
    if inst_data:
        try:
            recent_dates = sorted({row["date"] for row in inst_data})[-5:]
            net_total = 0
            for row in inst_data:
                if row["date"] in recent_dates:
                    net_total += (row.get("buy", 0) or 0) - (row.get("sell", 0) or 0)
            result["institutional_net_5d"] = net_total
            result["institutional_days"] = len(recent_dates)
        except Exception:
            pass

    if result["per"] is None and result["institutional_net_5d"] is None:
        return None

    _fundamentals_cache[cache_key] = dict(data=result, ts=now)
    return result
