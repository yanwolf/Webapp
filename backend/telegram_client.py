# -*- coding: utf-8 -*-
"""
Telegram Bot 用戶端（多使用者：每個人用自己的 Bot Token）
==========================================================
"""
import requests


def get_me(bot_token: str):
    """驗證 Bot Token 是否有效，回傳 bot 資訊（含 username），失敗回傳 None"""
    try:
        r = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe", timeout=10)
        data = r.json()
        if data.get("ok"):
            return data["result"]
    except Exception:
        pass
    return None


def set_webhook(bot_token: str, webhook_url: str, secret_token: str) -> bool:
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json={"url": webhook_url, "secret_token": secret_token},
            timeout=10,
        )
        return bool(r.json().get("ok"))
    except Exception:
        return False


def delete_webhook(bot_token: str) -> bool:
    try:
        r = requests.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook", timeout=10)
        return bool(r.json().get("ok"))
    except Exception:
        return False


def send_message(bot_token: str, chat_id: str, text: str) -> bool:
    if not bot_token or not chat_id:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        return r.status_code == 200
    except Exception:
        return False


def extract_chat_id_and_text(update: dict):
    """從 Telegram webhook 收到的 update 物件解析 chat_id 跟訊息文字"""
    message = update.get("message") or update.get("edited_message")
    if not message:
        return None, None
    chat_id = str(message.get("chat", {}).get("id", ""))
    text = (message.get("text") or "").strip()
    if not chat_id:
        return None, None
    return chat_id, text
