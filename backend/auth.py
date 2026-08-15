# -*- coding: utf-8 -*-
"""帳號密碼登入（bcrypt 雜湊 + JWT）"""
import os
import re
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Header, HTTPException

import db

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "")
if not JWT_SECRET:
    # 開發環境的備援值；正式環境務必在 Zeabur 設定 JWT_SECRET_KEY，
    # 否則每次重新部署 SECRET 都會變，所有人都要重新登入
    JWT_SECRET = "dev-insecure-secret-please-set-JWT_SECRET_KEY-env-var"

JWT_ALG = "HS256"
JWT_EXPIRE_DAYS = 30

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\-]{3,20}$")


def validate_username(username: str) -> bool:
    return bool(USERNAME_RE.match(username or ""))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except Exception:
        return None


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="請先登入")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登入已過期，請重新登入")
    user = db.get_user_by_id(int(payload["sub"]))
    if not user:
        raise HTTPException(status_code=401, detail="使用者不存在")
    return user
