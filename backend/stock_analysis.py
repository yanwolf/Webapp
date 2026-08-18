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
            if row.get("bullish_alignment"):
                return f"目前判定多頭排列（收盤{row['Close']:.1f}／分水嶺60線{row['ema_mid']:.1f}）"
            if row.get("bearish_alignment"):
                return f"目前判定空頭排列（收盤{row['Close']:.1f}／分水嶺60線{row['ema_mid']:.1f}）"
            return f"排列糾結，方向不明（快{row['ema_fast']:.1f}／中{row['ema_mid']:.1f}／慢{row['ema_slow']:.1f}）"
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


def analyze_signals(df, capital: float = 1_000_000.0, df_ma3=None, ma3_interval_label: str = "日K"):
    """
    對全部8種策略跑到最新一根K棒，回傳每個策略目前的持倉狀態

    均線三刀流(ma3)的原始設計是用在1小時K上（20/60/240根1H K棒），跟其他策略用的日K
    是完全不同的時間跨度，所以若有提供 df_ma3（額外抓的1小時K資料），ma3 會改用它計算，
    其餘策略仍用日K的 df。
    """
    signals = []
    tally = dict(bullish=0, bearish=0, neutral=0)
    cur_price = float(df["Close"].iloc[-1])

    for strat in ALL_SIGNAL_STRATEGIES:
        params = DEFAULT_PARAMS.get(strat, {})

        use_df = df
        interval_label = "日K"
        strat_cur_price = cur_price
        if strat == "ma3" and df_ma3 is not None:
            use_df = df_ma3
            interval_label = ma3_interval_label
            strat_cur_price = float(df_ma3["Close"].iloc[-1])

        try:
            out = run_strategy(use_df, strat, params, allow_short=True, capital=capital, bars_per_day=1)
        except Exception:
            continue

        op = out["res"].get("open_position")
        last_row = out["sig_df"].iloc[-1]

        if op:
            side = op["side"]
            entry_price = float(op["entry_price"])
            entry_ts = op["entry_date"]
            if interval_label == "日K":
                entry_date = entry_ts.strftime("%Y-%m-%d")
            else:
                entry_date = entry_ts.strftime("%Y-%m-%d %H:%M")
            if side == "long":
                unrealized = strat_cur_price / entry_price - 1
                tally["bullish"] += 1
            else:
                unrealized = entry_price / strat_cur_price - 1
                tally["bearish"] += 1
        else:
            side, entry_price, entry_date, unrealized = "flat", None, None, None
            tally["neutral"] += 1

        signals.append(dict(
            strategy=strat,
            strategy_label=STRATEGY_LABELS.get(strat, strat),
            interval=interval_label,
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

    result = dict(per=None, pbr=None, dividend_yield=None, per_date=None)
    per_data = _fm_get("TaiwanStockPER", data_id, start_30)
    if per_data:
        latest = per_data[-1]
        result["per"] = latest.get("PER")
        result["pbr"] = latest.get("PBR")
        result["dividend_yield"] = latest.get("dividend_yield")
        result["per_date"] = latest.get("date")

    if result["per"] is None:
        return None

    _fundamentals_cache[cache_key] = dict(data=result, ts=now)
    return result


def _classify_institution(name: str) -> Optional[str]:
    n = (name or "").lower()
    if "foreign" in n:
        return "foreign"
    if "trust" in n:
        return "trust"
    if "dealer" in n:
        return "dealer"
    return None


def fetch_institutional_daily(ticker: str, days: int = 20) -> Optional[list]:
    """逐日三大法人買賣超明細（外資/投信/自營/合計），單位：張"""
    if not FINMIND_TOKEN:
        return None
    data_id = ticker.strip().upper().replace(".TWO", "").replace(".TW", "")
    start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")  # 抓寬一點避開假日
    raw = _fm_get("InstitutionalInvestorsBuySell", data_id, start)
    if not raw:
        return None

    by_date = {}
    for row in raw:
        d = row.get("date")
        cat = _classify_institution(row.get("name"))
        if not d or not cat:
            continue
        net = (row.get("buy", 0) or 0) - (row.get("sell", 0) or 0)
        by_date.setdefault(d, dict(date=d, foreign=0, trust=0, dealer=0))
        by_date[d][cat] += net

    if not by_date:
        return None

    result = []
    for d in sorted(by_date.keys())[-days:]:
        row = by_date[d]
        row["total"] = row["foreign"] + row["trust"] + row["dealer"]
        result.append(row)
    return result or None


def fetch_margin_daily(ticker: str, days: int = 10) -> Optional[list]:
    """逐日融資融券餘額，單位：張"""
    if not FINMIND_TOKEN:
        return None
    data_id = ticker.strip().upper().replace(".TWO", "").replace(".TW", "")
    start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
    raw = _fm_get("TaiwanStockMarginPurchaseShortSale", data_id, start)
    if not raw:
        return None

    rows = []
    for row in raw:
        try:
            rows.append(dict(
                date=row.get("date"),
                margin_balance=int(row.get("MarginPurchaseTodayBalance", 0) or 0),
                short_balance=int(row.get("ShortSaleTodayBalance", 0) or 0),
            ))
        except Exception:
            continue
    rows.sort(key=lambda r: r["date"])
    rows = rows[-days:]

    for i in range(len(rows)):
        if i == 0:
            rows[i]["margin_change"] = None
            rows[i]["short_change"] = None
        else:
            rows[i]["margin_change"] = rows[i]["margin_balance"] - rows[i - 1]["margin_balance"]
            rows[i]["short_change"] = rows[i]["short_balance"] - rows[i - 1]["short_balance"]

    return rows or None


# ---------------------------------------------------------------- 量能與波動（不需FinMind，直接用OHLCV算）
def compute_volume_volatility(df) -> dict:
    result = dict(vol_5d=None, vol_20d=None, vol_ratio=None, avg_swing_20d=None)
    try:
        if len(df) >= 5:
            result["vol_5d"] = float(df["Volume"].tail(5).mean())
        if len(df) >= 20:
            result["vol_20d"] = float(df["Volume"].tail(20).mean())
            swing = (df["High"] - df["Low"]) / df["Close"]
            result["avg_swing_20d"] = float(swing.tail(20).mean())
        if result["vol_5d"] and result["vol_20d"]:
            result["vol_ratio"] = result["vol_5d"] / result["vol_20d"]
    except Exception:
        pass
    return result


# ---------------------------------------------------------------- 規則產生的文字摘要（非AI生成）
def build_summary_text(tally: dict, institutional_daily: Optional[list],
                        volume_stats: dict, margin_daily: Optional[list]) -> str:
    parts = []

    if tally["bullish"] > tally["bearish"]:
        parts.append(f"技術面：8個策略中有{tally['bullish']}個目前偏多、{tally['bearish']}個偏空，整體技術訊號偏多方。")
    elif tally["bearish"] > tally["bullish"]:
        parts.append(f"技術面：8個策略中有{tally['bearish']}個目前偏空、{tally['bullish']}個偏多，整體技術訊號偏空方。")
    else:
        parts.append(f"技術面：8個策略中偏多偏空各{tally['bullish']}個，訊號分歧，方向不明確。")

    if institutional_daily:
        recent = institutional_daily[-5:]
        net_sum = sum(d["total"] for d in recent)

        consecutive = 0
        sign = None
        for d in reversed(institutional_daily):
            if d["total"] == 0:
                break
            cur_sign = d["total"] > 0
            if sign is None:
                sign = cur_sign
                consecutive = 1
            elif cur_sign == sign:
                consecutive += 1
            else:
                break

        if net_sum < 0:
            note = f"，且已連續{consecutive}日賣超" if sign is False and consecutive >= 2 else ""
            parts.append(f"籌碼面：三大法人近{len(recent)}日合計賣超約{abs(net_sum):,.0f}張{note}。")
        elif net_sum > 0:
            note = f"，且已連續{consecutive}日買超" if sign is True and consecutive >= 2 else ""
            parts.append(f"籌碼面：三大法人近{len(recent)}日合計買超約{net_sum:,.0f}張{note}。")
        else:
            parts.append("籌碼面：三大法人近期買賣力道大致平衡。")

    if volume_stats.get("vol_ratio") is not None:
        ratio = volume_stats["vol_ratio"]
        if ratio < 0.85:
            parts.append(f"量能：近5日均量較近20日均量萎縮（量比約{ratio:.2f}），市場參與度降低。")
        elif ratio > 1.15:
            parts.append(f"量能：近5日均量較近20日均量放大（量比約{ratio:.2f}），市場關注度提高。")
        else:
            parts.append(f"量能：近期量能與過去20日相當（量比約{ratio:.2f}）。")
        if volume_stats.get("avg_swing_20d") is not None:
            parts.append(f"近20日平均單日振幅約{volume_stats['avg_swing_20d'] * 100:.1f}%。")

    if margin_daily and len(margin_daily) >= 2:
        first, last = margin_daily[0], margin_daily[-1]
        diff = last["margin_balance"] - first["margin_balance"]
        if diff > 0:
            parts.append(f"融資餘額近期增加約{diff:,.0f}張，顯示散戶做多意願上升。")
        elif diff < 0:
            parts.append(f"融資餘額近期減少約{abs(diff):,.0f}張，顯示散戶做多意願下降。")

    parts.append("以上為規則統計整理而成，非AI生成內容，也不構成投資建議。")
    return "".join(parts)
