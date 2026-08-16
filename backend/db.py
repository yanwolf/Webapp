# -*- coding: utf-8 -*-
"""
SQLite 儲存層（多使用者：帳號、各自的 Telegram Bot 設定、各自的追蹤清單）
========================================================================
⚠️ 注意：Zeabur 容器預設沒有持久化硬碟，重新部署後這個檔案會消失，
   請務必在 Zeabur 服務設定裡加一個 Volume 掛載到 DB_PATH 指定的目錄
   （預設 /app/data/app.db），否則帳號、追蹤清單、Telegram 設定每次部署都會重置。
"""
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Optional

DB_PATH = os.environ.get("DB_PATH", "./data/app.db")
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS telegram_config (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                bot_token TEXT,
                bot_username TEXT,
                webhook_secret TEXT UNIQUE,
                chat_id TEXT,
                created_at TEXT,
                linked_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                market TEXT NOT NULL,
                ticker TEXT NOT NULL,
                strategy TEXT NOT NULL,
                interval TEXT NOT NULL,
                params TEXT NOT NULL DEFAULT '{}',
                allow_short INTEGER DEFAULT 1,
                enabled INTEGER DEFAULT 1,
                created_at TEXT,
                last_checked_at TEXT,
                last_event_key TEXT,
                last_event_summary TEXT
            )
        """)


# ---------------------------------------------------------------- users
def create_user(username: str, password_hash: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, datetime.now(timezone.utc).isoformat())
        )
        return cur.lastrowid


def get_user_by_username(username: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def count_users() -> int:
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]


def list_all_users():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT u.id, u.username, u.created_at,
                   tc.chat_id IS NOT NULL AS telegram_linked,
                   (SELECT COUNT(*) FROM watchlist w WHERE w.user_id = u.id) AS watchlist_count
            FROM users u
            LEFT JOIN telegram_config tc ON tc.user_id = u.id
            ORDER BY u.id ASC
        """).fetchall()
        return [dict(r) for r in rows]


def delete_user(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


# ---------------------------------------------------------------- telegram (per user)
def save_bot_token(user_id: int, bot_token: str, bot_username: str) -> str:
    """儲存/更新使用者的 Bot Token，回傳這個使用者專屬的 webhook_secret"""
    with get_conn() as conn:
        row = conn.execute("SELECT webhook_secret FROM telegram_config WHERE user_id = ?", (user_id,)).fetchone()
        webhook_secret = row["webhook_secret"] if row else secrets.token_urlsafe(24)
        conn.execute("""
            INSERT INTO telegram_config (user_id, bot_token, bot_username, webhook_secret, chat_id, created_at)
            VALUES (?, ?, ?, ?, NULL, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                bot_token = excluded.bot_token,
                bot_username = excluded.bot_username,
                webhook_secret = telegram_config.webhook_secret
        """, (user_id, bot_token, bot_username, webhook_secret, datetime.now(timezone.utc).isoformat()))
        return webhook_secret


def get_telegram_config(user_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM telegram_config WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_telegram_config_by_webhook_secret(webhook_secret: str):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM telegram_config WHERE webhook_secret = ?", (webhook_secret,)).fetchone()
        return dict(row) if row else None


def set_chat_id(user_id: int, chat_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE telegram_config SET chat_id = ?, linked_at = ? WHERE user_id = ?",
                      (chat_id, datetime.now(timezone.utc).isoformat(), user_id))


def unlink_telegram(user_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM telegram_config WHERE user_id = ?", (user_id,))


# ---------------------------------------------------------------- watchlist (per user)
def add_watchlist_item(user_id: int, market, ticker, strategy, interval, params: dict, allow_short: bool) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO watchlist (user_id, market, ticker, strategy, interval, params, allow_short, enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (user_id, market, ticker, strategy, interval, json.dumps(params), int(allow_short),
              datetime.now(timezone.utc).isoformat()))
        return cur.lastrowid


def _row_to_watchlist_dict(row):
    d = dict(row)
    d["params"] = json.loads(d["params"] or "{}")
    d["allow_short"] = bool(d["allow_short"])
    d["enabled"] = bool(d["enabled"])
    return d


def list_watchlist(user_id: Optional[int] = None, enabled_only: bool = False):
    with get_conn() as conn:
        q = "SELECT * FROM watchlist"
        conds, args = [], []
        if user_id is not None:
            conds.append("user_id = ?")
            args.append(user_id)
        if enabled_only:
            conds.append("enabled = 1")
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY id DESC"
        rows = conn.execute(q, args).fetchall()
        return [_row_to_watchlist_dict(r) for r in rows]


def get_watchlist_item(item_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM watchlist WHERE id = ?", (item_id,)).fetchone()
        return _row_to_watchlist_dict(row) if row else None


def set_watchlist_enabled(item_id: int, enabled: bool):
    with get_conn() as conn:
        conn.execute("UPDATE watchlist SET enabled = ? WHERE id = ?", (int(enabled), item_id))


def delete_watchlist_item(item_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM watchlist WHERE id = ?", (item_id,))


def update_watchlist_check_result(item_id: int, checked_at: str, event_key: Optional[str] = None,
                                   event_summary: Optional[str] = None):
    with get_conn() as conn:
        if event_key is not None:
            conn.execute("""
                UPDATE watchlist SET last_checked_at = ?, last_event_key = ?, last_event_summary = ?
                WHERE id = ?
            """, (checked_at, event_key, event_summary, item_id))
        else:
            conn.execute("UPDATE watchlist SET last_checked_at = ? WHERE id = ?", (checked_at, item_id))
