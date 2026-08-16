# -*- coding: utf-8 -*-
"""
多策略回測 + 多使用者追蹤清單 + 各自的 Telegram Bot 通知
==========================================================
POST /api/auth/register          註冊帳號（需邀請碼）
POST /api/auth/login             登入，取得 JWT
GET  /api/auth/me                取得目前登入使用者資訊

POST /api/backtest                執行回測
GET  /api/health                  健康檢查

POST /api/telegram/config         儲存/更新自己的 Bot Token（會自動註冊 webhook）
GET  /api/telegram/status         查詢自己的 Telegram 設定狀態
DELETE /api/telegram/config       解除自己的 Telegram 設定
POST /api/telegram/webhook/{secret}  Telegram 伺服器回呼（依 secret 對應到使用者）

GET    /api/watchlist             取得自己的追蹤清單
POST   /api/watchlist             新增追蹤項目
PATCH  /api/watchlist/{id}        啟用/停用
DELETE /api/watchlist/{id}        刪除
"""
import logging
import os
import traceback
from typing import Optional, Literal, Dict, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import db
import auth
import telegram_client
from market_data import fetch_ohlcv, sanitize, INTERVAL_META
from strategy_runner import (
    run_strategy, STRATEGY_LABELS, DEFAULT_PARAMS, min_bars_for_strategy,
    ALL_SIGNAL_STRATEGIES, STYLE_PRESETS,
)
from ticker_search import search_tw, search_us, search_crypto
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(title="Multi-Strategy Backtest + Multi-User Watchlist API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MIN_BARS = 60
SIGNUP_INVITE_CODE = os.environ.get("SIGNUP_INVITE_CODE", "")
PUBLIC_BACKEND_URL = os.environ.get("PUBLIC_BACKEND_URL", "").rstrip("/")
MAX_USERS = int(os.environ.get("MAX_USERS", "10"))


@app.on_event("startup")
def on_startup():
    db.init_db()
    start_scheduler()
    logger.info("啟動完成：資料庫已初始化、背景排程已啟動")
    if not PUBLIC_BACKEND_URL:
        logger.warning("尚未設定 PUBLIC_BACKEND_URL，Telegram webhook 將無法自動註冊")
    if not os.environ.get("JWT_SECRET_KEY"):
        logger.warning("尚未設定 JWT_SECRET_KEY，將使用不安全的預設值（正式環境請務必設定）")


# ======================================================================
# 帳號註冊 / 登入
# ======================================================================
class RegisterRequest(BaseModel):
    username: str
    password: str = Field(..., min_length=6)
    invite_code: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/register")
def register(req: RegisterRequest):
    if db.count_users() >= MAX_USERS:
        raise HTTPException(status_code=403, detail=f"目前已達開放註冊上限（{MAX_USERS}人），請聯絡管理員")
    if SIGNUP_INVITE_CODE and req.invite_code != SIGNUP_INVITE_CODE:
        raise HTTPException(status_code=403, detail="邀請碼錯誤")
    if not auth.validate_username(req.username):
        raise HTTPException(status_code=422, detail="帳號需為 3-20 字元的英數字、底線或連字號")
    if db.get_user_by_username(req.username):
        raise HTTPException(status_code=409, detail="這個帳號已經被註冊了")

    password_hash = auth.hash_password(req.password)
    user_id = db.create_user(req.username, password_hash)
    token = auth.create_token(user_id, req.username)
    return {"token": token, "username": req.username}


@app.post("/api/auth/login")
def login(req: LoginRequest):
    user = db.get_user_by_username(req.username)
    if not user or not auth.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    token = auth.create_token(user["id"], user["username"])
    return {"token": token, "username": user["username"]}


@app.get("/api/auth/me")
def me(user=Depends(auth.get_current_user)):
    return {"id": user["id"], "username": user["username"], "is_admin": auth.is_admin(user)}


# ======================================================================
# 管理員：使用者管理
# ======================================================================
@app.get("/api/admin/users")
def admin_list_users(admin=Depends(auth.require_admin)):
    users = db.list_all_users()
    return {"users": users, "max_users": MAX_USERS, "current_count": len(users)}


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: int, admin=Depends(auth.require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="不能刪除自己目前登入的帳號")
    target = db.get_user_by_id(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="找不到這個使用者")
    db.delete_user(user_id)
    return {"ok": True}


# ======================================================================
# 回測 API
# ======================================================================
class BacktestRequest(BaseModel):
    market: Literal["us", "tw", "crypto"] = Field(..., description="市場別")
    ticker: str
    strategy: Literal["bollinger", "ma3", "ma_cross", "donchian", "rsi", "macd",
                       "atr_channel", "fvg", "buy_hold"] = Field("bollinger")
    interval: Literal["1d", "4h", "1h", "15m", "5m", "1m"] = Field("1d")
    start: str = Field("2015-01-01")
    end: Optional[str] = Field(None)
    capital: float = Field(1_000_000, gt=0)
    allow_short: bool = Field(True)

    bb_window: int = Field(20, ge=5, le=100)
    bb_std: float = Field(2.0, ge=0.5, le=4.0)
    vol_mult: float = Field(1.5, ge=1.0, le=5.0)
    ma_fast: int = Field(20, ge=2, le=200)
    ma_mid: int = Field(60, ge=5, le=400)
    ma_slow: int = Field(240, ge=10, le=800)
    cross_fast: int = Field(20, ge=2, le=200)
    cross_slow: int = Field(60, ge=5, le=400)
    cross_ma_type: Literal["sma", "ema"] = Field("sma")
    donch_entry_window: int = Field(20, ge=5, le=200)
    donch_exit_window: int = Field(10, ge=3, le=200)
    rsi_period: int = Field(14, ge=2, le=100)
    rsi_oversold: float = Field(30, ge=1, le=49)
    rsi_overbought: float = Field(70, ge=51, le=99)
    macd_fast: int = Field(12, ge=2, le=100)
    macd_slow: int = Field(26, ge=3, le=200)
    macd_signal: int = Field(9, ge=2, le=100)

    # 均線交叉 / RSI / MACD 共用的停損設定（同一次請求只會用其中一組策略，欄位共用不衝突）
    stop_type: Literal["pct", "atr", "none"] = Field("pct", description="停損類型")
    stop_pct: float = Field(0.08, ge=0.0, le=0.5)
    atr_period: int = Field(14, ge=2, le=100)
    atr_mult: float = Field(2.0, ge=0.5, le=10.0)

    # ATR 通道突破策略
    atr_ch_period: int = Field(14, ge=2, le=100)
    atr_ch_ma_window: int = Field(20, ge=5, le=200)
    atr_ch_mult: float = Field(2.0, ge=0.5, le=10.0)

    # FVG 缺口回補策略
    fvg_atr_period: int = Field(14, ge=2, le=100)
    fvg_max_wait: int = Field(20, ge=3, le=100)
    fvg_atr_stop_mult: float = Field(1.5, ge=0.5, le=10.0)
    fvg_atr_target_mult: float = Field(3.0, ge=0.5, le=20.0)


def _req_to_params(req: BacktestRequest) -> Dict[str, Any]:
    return dict(
        bb_window=req.bb_window, bb_std=req.bb_std, vol_mult=req.vol_mult,
        ma_fast=req.ma_fast, ma_mid=req.ma_mid, ma_slow=req.ma_slow,
        cross_fast=req.cross_fast, cross_slow=req.cross_slow, cross_ma_type=req.cross_ma_type,
        donch_entry_window=req.donch_entry_window, donch_exit_window=req.donch_exit_window,
        rsi_period=req.rsi_period, rsi_oversold=req.rsi_oversold, rsi_overbought=req.rsi_overbought,
        macd_fast=req.macd_fast, macd_slow=req.macd_slow, macd_signal=req.macd_signal,
        stop_type=req.stop_type, stop_pct=req.stop_pct, atr_period=req.atr_period, atr_mult=req.atr_mult,
        atr_ch_period=req.atr_ch_period, atr_ch_ma_window=req.atr_ch_ma_window, atr_ch_mult=req.atr_ch_mult,
        fvg_atr_period=req.fvg_atr_period, fvg_max_wait=req.fvg_max_wait,
        fvg_atr_stop_mult=req.fvg_atr_stop_mult, fvg_atr_target_mult=req.fvg_atr_target_mult,
    )


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/search-ticker")
def search_ticker(market: Literal["us", "tw", "crypto"], query: str, user=Depends(auth.get_current_user)):
    query = query.strip()
    if not query:
        return {"results": [], "available": True}

    if market == "tw":
        results = search_tw(query)
        if results is None:
            return {"results": [], "available": False, "message": "尚未設定 FINMIND_API_TOKEN，無法查詢台股代號/名稱"}
        return {"results": results, "available": True}

    if market == "us":
        results = search_us(query)
        if results is None:
            return {"results": [], "available": False, "message": "尚未設定 TWELVE_DATA_API_KEY，無法查詢美股代號/名稱"}
        return {"results": results, "available": True}

    if market == "crypto":
        results = search_crypto(query)
        if results is None:
            return {"results": [], "available": False, "message": "查詢加密貨幣清單失敗，請稍後再試"}
        return {"results": results, "available": True}

    return {"results": [], "available": True}


@app.post("/api/backtest")
def backtest(req: BacktestRequest, user=Depends(auth.get_current_user)):
    df, resolved, notes, err, source = fetch_ohlcv(req.market, req.ticker, req.interval, req.start, req.end)
    if err:
        status = 404 if "抓不到" in err else 502
        raise HTTPException(status_code=status, detail=err)

    meta = INTERVAL_META[req.interval]
    params = _req_to_params(req)
    min_bars_needed = min_bars_for_strategy(req.strategy, params, base_min=MIN_BARS)

    if len(df) < min_bars_needed:
        raise HTTPException(
            status_code=422,
            detail=(
                f"「{resolved}」在「{req.interval}」週期下只抓到 {len(df)} 根K棒，過少無法計算指標"
                f"（此設定至少需要約 {min_bars_needed} 根）。請縮短回測區間、改用較長的K線週期，或調小策略週期參數。"
            )
        )

    try:
        out = run_strategy(df, req.strategy, params, allow_short=req.allow_short,
                            capital=req.capital, bars_per_day=meta["bars_per_day"])
        sig_df, res = out["sig_df"], out["res"]
        from bollinger_strategy import compute_metrics
        metrics = compute_metrics(res["equity"], res["trades"], init_capital=req.capital,
                                   freq_per_year=int(252 * meta["bars_per_day"]))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"回測執行失敗: {e}")

    def fmt_ts(ts):
        if req.interval == "1d":
            return ts.strftime("%Y-%m-%d")
        return ts.strftime("%Y-%m-%d %H:%M")

    price_series = []
    for ts, row in sig_df.iterrows():
        item = {"date": fmt_ts(ts), "close": sanitize(row["Close"])}
        for k in out["overlay_keys"] + out["oscillator_keys"]:
            item[k] = sanitize(row[k])
        price_series.append(item)

    equity_series = [{"date": fmt_ts(ts), "equity": sanitize(v)} for ts, v in res["equity"].items()]

    trades = []
    if len(res["trades"]):
        for _, r in res["trades"].iterrows():
            trades.append({
                "entry_date": fmt_ts(r["entry_date"]), "exit_date": fmt_ts(r["exit_date"]), "side": r["side"],
                "entry_price": sanitize(r["entry_price"]), "exit_price": sanitize(r["exit_price"]),
                "pnl": sanitize(r["pnl"]), "ret": sanitize(r["ret"]),
            })

    return {
        "ticker_resolved": resolved,
        "data_source": source,
        "strategy": req.strategy,
        "strategy_label": STRATEGY_LABELS.get(req.strategy, req.strategy),
        "chart_type": out["chart_type"],
        "interval": req.interval,
        "overlay_keys": out["overlay_keys"],
        "oscillator_keys": out["oscillator_keys"],
        "data_points": len(df),
        "date_range": [fmt_ts(df.index[0]), fmt_ts(df.index[-1])],
        "notes": notes,
        "metrics": metrics,
        "price_series": price_series,
        "equity_series": equity_series,
        "trades": trades,
    }


# ======================================================================
# 策略比較：同一標的、同一區間，一次跑完所有策略排出優劣
# ======================================================================
class CompareRequest(BaseModel):
    market: Literal["us", "tw", "crypto"]
    ticker: str
    style: Literal["short", "swing"] = Field("swing", description="short=短沖, swing=長線波段")
    interval: Optional[Literal["1d", "4h", "1h", "15m", "5m", "1m"]] = Field(
        None, description="留空則依 style 自動決定"
    )
    start: str = Field("2015-01-01")
    end: Optional[str] = Field(None)
    capital: float = Field(1_000_000, gt=0)
    allow_short: bool = Field(True)


@app.post("/api/compare-strategies")
def compare_strategies(req: CompareRequest, user=Depends(auth.get_current_user)):
    preset = STYLE_PRESETS[req.style]
    interval = req.interval or preset["interval"]

    df, resolved, notes, err, source = fetch_ohlcv(req.market, req.ticker, interval, req.start, req.end)
    if err:
        status = 404 if "抓不到" in err else 502
        raise HTTPException(status_code=status, detail=err)

    meta = INTERVAL_META[interval]
    from bollinger_strategy import compute_raw_metrics

    results = []
    buy_hold_cagr = None

    strategies_to_run = ["buy_hold"] + ALL_SIGNAL_STRATEGIES
    for strat in strategies_to_run:
        params = DEFAULT_PARAMS.get(strat, {})
        min_needed = min_bars_for_strategy(strat, params, base_min=MIN_BARS)
        if len(df) < min_needed:
            results.append(dict(
                strategy=strat, strategy_label=STRATEGY_LABELS.get(strat, strat),
                error=f"資料筆數不足（需要約{min_needed}根，只有{len(df)}根）", metrics=None,
            ))
            continue
        try:
            out = run_strategy(df, strat, params, allow_short=req.allow_short,
                                capital=req.capital, bars_per_day=meta["bars_per_day"])
            m = compute_raw_metrics(out["res"]["equity"], out["res"]["trades"],
                                     init_capital=req.capital, freq_per_year=int(252 * meta["bars_per_day"]))
            if strat == "buy_hold":
                buy_hold_cagr = m["cagr"]
            results.append(dict(
                strategy=strat, strategy_label=STRATEGY_LABELS.get(strat, strat),
                metrics=m, error=None,
            ))
        except Exception as e:
            traceback.print_exc()
            results.append(dict(
                strategy=strat, strategy_label=STRATEGY_LABELS.get(strat, strat),
                error=f"執行失敗: {e}", metrics=None,
            ))

    for r in results:
        if r["metrics"] is not None and buy_hold_cagr is not None and r["metrics"]["cagr"] is not None:
            r["beats_buy_hold"] = r["metrics"]["cagr"] > buy_hold_cagr
        else:
            r["beats_buy_hold"] = None

    # 依 CAGR 由高到低排序（無法計算的排最後）
    def sort_key(r):
        c = r["metrics"]["cagr"] if r["metrics"] and r["metrics"]["cagr"] is not None else -999
        return -c
    results.sort(key=sort_key)

    return {
        "ticker_resolved": resolved,
        "data_source": source,
        "style": req.style,
        "style_label": preset["label"],
        "interval": interval,
        "data_points": len(df),
        "date_range": [df.index[0].strftime("%Y-%m-%d"), df.index[-1].strftime("%Y-%m-%d")],
        "notes": notes,
        "buy_hold_cagr": buy_hold_cagr,
        "results": results,
    }


# ======================================================================
# 每個使用者自己的 Telegram Bot 設定
# ======================================================================
class TelegramConfigRequest(BaseModel):
    bot_token: str


@app.post("/api/telegram/config")
def save_telegram_config(req: TelegramConfigRequest, user=Depends(auth.get_current_user)):
    bot_token = req.bot_token.strip()
    if not bot_token:
        raise HTTPException(status_code=422, detail="請輸入 Bot Token")

    bot_info = telegram_client.get_me(bot_token)
    if not bot_info:
        raise HTTPException(status_code=422, detail="這組 Bot Token 無效，請確認是否直接從 BotFather 複製完整")

    bot_username = bot_info.get("username", "")
    webhook_secret = db.save_bot_token(user["id"], bot_token, bot_username)

    webhook_registered = False
    webhook_error = None
    if PUBLIC_BACKEND_URL:
        webhook_url = f"{PUBLIC_BACKEND_URL}/api/telegram/webhook/{webhook_secret}"
        webhook_registered = telegram_client.set_webhook(bot_token, webhook_url, webhook_secret)
        if not webhook_registered:
            webhook_error = "自動註冊 webhook 失敗，請稍後再試一次儲存"
    else:
        webhook_error = "伺服器尚未設定 PUBLIC_BACKEND_URL，無法自動註冊 webhook，請聯絡管理員"

    return {
        "ok": True,
        "bot_username": bot_username,
        "webhook_registered": webhook_registered,
        "webhook_error": webhook_error,
    }


@app.get("/api/telegram/status")
def telegram_status(user=Depends(auth.get_current_user)):
    cfg = db.get_telegram_config(user["id"])
    if not cfg:
        return {"configured": False, "linked": False, "bot_username": None}
    return {
        "configured": bool(cfg.get("bot_token")),
        "linked": bool(cfg.get("chat_id")),
        "bot_username": cfg.get("bot_username"),
    }


@app.delete("/api/telegram/config")
def remove_telegram_config(user=Depends(auth.get_current_user)):
    cfg = db.get_telegram_config(user["id"])
    if cfg and cfg.get("bot_token"):
        telegram_client.delete_webhook(cfg["bot_token"])
    db.unlink_telegram(user["id"])
    return {"ok": True}


@app.post("/api/telegram/webhook/{webhook_secret}")
async def telegram_webhook(webhook_secret: str, request: Request):
    cfg = db.get_telegram_config_by_webhook_secret(webhook_secret)
    if not cfg:
        raise HTTPException(status_code=404, detail="unknown webhook")

    header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if header_secret != webhook_secret:
        raise HTTPException(status_code=403, detail="invalid secret")

    update = await request.json()
    chat_id, text = telegram_client.extract_chat_id_and_text(update)
    if not chat_id:
        return {"ok": True}

    bot_token = cfg["bot_token"]
    if not cfg.get("chat_id"):
        db.set_chat_id(cfg["user_id"], chat_id)
        telegram_client.send_message(bot_token, chat_id, "✅ 連結成功！之後你在追蹤清單設定的訊號會通知到這裡。")
    else:
        telegram_client.send_message(bot_token, chat_id, "已經連結囉，訊號出現時我會主動通知你 🙂")

    return {"ok": True}


# ======================================================================
# 追蹤清單（各自的）
# ======================================================================
class WatchlistCreate(BaseModel):
    market: Literal["us", "tw", "crypto"]
    ticker: str
    strategy: Literal["bollinger", "ma3", "ma_cross", "donchian", "rsi", "macd", "atr_channel", "fvg"]
    interval: Literal["1d", "4h", "1h", "15m", "5m", "1m"] = "1d"
    allow_short: bool = True
    params: Dict[str, Any] = Field(default_factory=dict)


@app.get("/api/watchlist")
def get_watchlist(user=Depends(auth.get_current_user)):
    items = db.list_watchlist(user_id=user["id"])
    for it in items:
        it["strategy_label"] = STRATEGY_LABELS.get(it["strategy"], it["strategy"])
    return {"items": items}


@app.post("/api/watchlist")
def create_watchlist_item(req: WatchlistCreate, user=Depends(auth.get_current_user)):
    if not req.ticker.strip():
        raise HTTPException(status_code=422, detail="代碼不可為空")
    params = {**DEFAULT_PARAMS.get(req.strategy, {}), **req.params}
    item_id = db.add_watchlist_item(user["id"], req.market, req.ticker.strip(), req.strategy, req.interval,
                                     params, req.allow_short)
    return {"id": item_id}


def _get_owned_item_or_404(item_id: int, user_id: int):
    item = db.get_watchlist_item(item_id)
    if not item or item["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="找不到這個追蹤項目")
    return item


@app.patch("/api/watchlist/{item_id}")
def toggle_watchlist_item(item_id: int, enabled: bool, user=Depends(auth.get_current_user)):
    _get_owned_item_or_404(item_id, user["id"])
    db.set_watchlist_enabled(item_id, enabled)
    return {"ok": True}


@app.delete("/api/watchlist/{item_id}")
def remove_watchlist_item(item_id: int, user=Depends(auth.get_current_user)):
    _get_owned_item_or_404(item_id, user["id"])
    db.delete_watchlist_item(item_id)
    return {"ok": True}
