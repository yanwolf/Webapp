# -*- coding: utf-8 -*-
"""
背景排程：依每個追蹤項目的K線週期，自動決定多久檢查一次新訊號
==================================================================
多使用者版本：每個追蹤項目都屬於某個 user_id，通知時查該使用者自己的 Bot Token + chat_id 發送。

主排程每 5 分鐘 tick 一次；每個追蹤項目依自己的週期換算出「應該多久檢查一次」，
只有超過這個間隔才會真的重新抓資料、跑策略。
"""
import logging
import traceback
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

import db
import telegram_client
from market_data import fetch_ohlcv, drop_forming_bar, INTERVAL_META
from strategy_runner import run_strategy, determine_latest_event, min_bars_for_strategy, STRATEGY_LABELS

logger = logging.getLogger("scheduler")

CHECK_INTERVAL_MINUTES = {
    "1d": 24 * 60, "4h": 4 * 60, "1h": 60, "15m": 15, "5m": 5, "1m": 5,
}

EVENT_LABELS = {
    "entry_long": "🔴 做多進場", "entry_short": "🟢 做空進場",
    "exit_long": "⚪ 多單出場", "exit_short": "⚪ 空單出場",
}

LOOKBACK_START = {"1d": "2018-01-01"}


def _is_due(item, now: datetime) -> bool:
    if not item["last_checked_at"]:
        return True
    last = datetime.fromisoformat(item["last_checked_at"])
    threshold = CHECK_INTERVAL_MINUTES.get(item["interval"], 60)
    return (now - last) >= timedelta(minutes=threshold)


def _start_date_for(interval: str) -> str:
    preset = LOOKBACK_START.get(interval)
    if preset:
        return preset
    max_days = INTERVAL_META[interval]["max_lookback_days"] or 365
    return (datetime.now(timezone.utc) - timedelta(days=max_days)).strftime("%Y-%m-%d")


def check_one_item(item: dict, now: datetime):
    market, ticker, strategy, interval = item["market"], item["ticker"], item["strategy"], item["interval"]
    params = item["params"]

    start = _start_date_for(interval)
    df, resolved, notes, err = fetch_ohlcv(market, ticker, interval, start)
    if err or df is None:
        logger.warning(f"[watchlist#{item['id']}] 抓資料失敗: {err}")
        db.update_watchlist_check_result(item["id"], now.isoformat())
        return

    df = drop_forming_bar(df, interval)
    if len(df) < min_bars_for_strategy(strategy, params):
        db.update_watchlist_check_result(item["id"], now.isoformat())
        return

    bars_per_day = INTERVAL_META[interval]["bars_per_day"]
    out = run_strategy(df, strategy, params, allow_short=item["allow_short"],
                        capital=1_000_000.0, bars_per_day=bars_per_day)

    event = determine_latest_event(out["sig_df"], out["res"])
    if event is None:
        db.update_watchlist_check_result(item["id"], now.isoformat())
        return

    event_key = f"{event['type']}_{event['date']}"
    if event_key == item.get("last_event_key"):
        db.update_watchlist_check_result(item["id"], now.isoformat())
        return

    label = EVENT_LABELS.get(event["type"], event["type"])
    strategy_label = STRATEGY_LABELS.get(strategy, strategy)
    date_str = event["date"].strftime("%Y-%m-%d %H:%M") if hasattr(event["date"], "strftime") else str(event["date"])
    price = event["price"]
    price_str = f"{price:.2f}" if price is not None else "—"

    text = (
        f"<b>{label}</b>\n"
        f"標的：{resolved}（{market}）\n"
        f"策略：{strategy_label}｜週期：{interval}\n"
        f"時間：{date_str}\n"
        f"價格：{price_str}"
    )

    tg = db.get_telegram_config(item["user_id"])
    if tg and tg.get("bot_token") and tg.get("chat_id"):
        telegram_client.send_message(tg["bot_token"], tg["chat_id"], text)
    else:
        logger.info(f"[watchlist#{item['id']}] user#{item['user_id']} 尚未完成 Telegram 連結，略過通知")

    summary = f"{label} @ {price_str} ({date_str})"
    db.update_watchlist_check_result(item["id"], now.isoformat(), event_key, summary)
    logger.info(f"[watchlist#{item['id']}] 新事件: {summary}")


def tick():
    now = datetime.now(timezone.utc)
    items = db.list_watchlist(enabled_only=True)
    for item in items:
        if not _is_due(item, now):
            continue
        try:
            check_one_item(item, now)
        except Exception:
            logger.error(f"[watchlist#{item['id']}] 檢查失敗:\n{traceback.format_exc()}")


_scheduler = None


def start_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(tick, "interval", minutes=5, id="watchlist_tick", max_instances=1)
    _scheduler.start()
    logger.info("背景排程已啟動（每5分鐘tick一次）")
    return _scheduler
