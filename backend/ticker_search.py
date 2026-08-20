# -*- coding: utf-8 -*-
"""
股票/加密貨幣代碼查詢（依名稱或代號反查）
==========================================
台股：FinMind 的 TaiwanStockInfo 清單（含中文名稱），記憶體快取 24 小時
美股：Twelve Data 的 symbol_search（即時查詢，該公司自己做好比對）
加密貨幣：Binance 上市幣種清單 + 常見幣種中英文對照表
"""
import time
from typing import List, Optional

import requests

from market_data import FINMIND_TOKEN, FINMIND_URL, TWELVE_DATA_KEY

CACHE_TTL_SECONDS = 24 * 3600

_tw_cache = {"data": None, "ts": 0}
_crypto_cache = {"data": None, "ts": 0}

# 常見幣種代號 -> 中英文名稱，用於加密貨幣的名稱搜尋（Binance本身沒有提供幣種全名）
CRYPTO_NAMES = {
    "BTC": "Bitcoin 比特幣", "ETH": "Ethereum 以太幣", "BNB": "BNB 幣安幣",
    "SOL": "Solana", "XRP": "Ripple 瑞波幣", "ADA": "Cardano",
    "DOGE": "Dogecoin 狗狗幣", "AVAX": "Avalanche", "DOT": "Polkadot",
    "MATIC": "Polygon", "POL": "Polygon", "LINK": "Chainlink",
    "UNI": "Uniswap", "ATOM": "Cosmos", "LTC": "Litecoin 萊特幣",
    "TRX": "Tron 波場", "SHIB": "Shiba Inu 柴犬幣", "NEAR": "Near Protocol",
    "APT": "Aptos", "ARB": "Arbitrum", "OP": "Optimism",
    "FIL": "Filecoin", "ICP": "Internet Computer", "ETC": "Ethereum Classic",
    "XLM": "Stellar 恆星幣", "HBAR": "Hedera", "VET": "VeChain",
    "ALGO": "Algorand", "SAND": "The Sandbox", "MANA": "Decentraland",
    "AXS": "Axie Infinity", "FTM": "Fantom", "S": "Sonic",
    "INJ": "Injective", "RUNE": "THORChain", "GRT": "The Graph",
    "AAVE": "Aave", "MKR": "Maker", "SNX": "Synthetix",
    "CRV": "Curve DAO", "COMP": "Compound", "SUI": "Sui",
    "PEPE": "Pepe", "WIF": "dogwifhat", "BONK": "Bonk",
    "TIA": "Celestia", "SEI": "Sei", "STX": "Stacks",
    "IMX": "Immutable", "RENDER": "Render", "RNDR": "Render",
    "THETA": "Theta Network", "FLOW": "Flow", "EGLD": "MultiversX",
    "XTZ": "Tezos", "KAVA": "Kava", "ZEC": "Zcash",
    "DASH": "Dash", "EOS": "EOS", "NEO": "Neo",
    "WAVES": "Waves", "CHZ": "Chiliz", "ENJ": "Enjin Coin",
    "GALA": "Gala", "LDO": "Lido DAO", "CAKE": "PancakeSwap",
    "1INCH": "1inch", "BAT": "Basic Attention Token", "ZRX": "0x",
    "YFI": "yearn.finance", "SUSHI": "SushiSwap", "KSM": "Kusama",
    "DYDX": "dYdX", "USDT": "Tether", "USDC": "USD Coin",
}


# ---------------------------------------------------------------- 台股
def _refresh_tw_list() -> Optional[list]:
    now = time.time()
    if _tw_cache["data"] is not None and now - _tw_cache["ts"] < CACHE_TTL_SECONDS:
        return _tw_cache["data"]
    if not FINMIND_TOKEN:
        return None
    try:
        r = requests.get(
            FINMIND_URL,
            headers={"Authorization": f"Bearer {FINMIND_TOKEN}"},
            params={"dataset": "TaiwanStockInfo"},
            timeout=15,
        )
        j = r.json()
        if j.get("status") != 200:
            return None
        data = j.get("data", [])
        if not data:
            return None
        _tw_cache["data"] = data
        _tw_cache["ts"] = now
        return data
    except Exception:
        return None


def get_tw_stock_name(ticker: str) -> Optional[str]:
    """依代號反查台股中文名稱，查不到回傳 None"""
    data = _refresh_tw_list()
    if data is None:
        return None
    stock_id = ticker.strip().upper().replace(".TWO", "").replace(".TW", "").lstrip("^")
    for row in data:
        if str(row.get("stock_id", "")).upper() == stock_id:
            return row.get("stock_name") or None
    return None


def search_tw(query: str, limit: int = 15) -> Optional[List[dict]]:
    """回傳 None 代表功能未啟用（沒設定FinMind Token或抓取失敗），回傳 [] 代表查無結果"""
    data = _refresh_tw_list()
    if data is None:
        return None
    q = query.strip().upper()
    if not q:
        return []
    results = []
    for row in data:
        stock_id = str(row.get("stock_id", ""))
        stock_name = str(row.get("stock_name", ""))
        if q in stock_id.upper() or q in stock_name.upper() or q in stock_name:
            results.append({
                "symbol": stock_id, "name": stock_name,
                "exchange": row.get("type", ""),
            })
            if len(results) >= limit:
                break
    return results


# ---------------------------------------------------------------- 美股
def search_us(query: str, limit: int = 15) -> Optional[List[dict]]:
    if not TWELVE_DATA_KEY:
        return None
    q = query.strip()
    if not q:
        return []
    try:
        r = requests.get(
            "https://api.twelvedata.com/symbol_search",
            params={"symbol": q, "apikey": TWELVE_DATA_KEY},
            timeout=10,
        )
        j = r.json()
        data = j.get("data", [])
        results = []
        for row in data[:limit]:
            results.append({
                "symbol": row.get("symbol"), "name": row.get("instrument_name"),
                "exchange": row.get("exchange"),
            })
        return results
    except Exception:
        return None


# ---------------------------------------------------------------- 加密貨幣
def _refresh_crypto_bases() -> Optional[List[str]]:
    now = time.time()
    if _crypto_cache["data"] is not None and now - _crypto_cache["ts"] < CACHE_TTL_SECONDS:
        return _crypto_cache["data"]
    try:
        r = requests.get("https://api.binance.com/api/v3/exchangeInfo", timeout=15)
        j = r.json()
        symbols = j.get("symbols", [])
        bases = sorted({
            s["baseAsset"] for s in symbols
            if s.get("quoteAsset") == "USDT" and s.get("status") == "TRADING"
        })
        if not bases:
            return None
        _crypto_cache["data"] = bases
        _crypto_cache["ts"] = now
        return bases
    except Exception:
        return None


def search_crypto(query: str, limit: int = 15) -> Optional[List[dict]]:
    bases = _refresh_crypto_bases()
    if bases is None:
        return None
    q = query.strip().upper()
    if not q:
        return []
    results, seen = [], set()

    for base in bases:
        if base.upper().startswith(q) and base not in seen:
            results.append({"symbol": base, "name": CRYPTO_NAMES.get(base.upper(), ""), "exchange": "Binance"})
            seen.add(base)
            if len(results) >= limit:
                return results

    for base in bases:
        if base in seen:
            continue
        name = CRYPTO_NAMES.get(base.upper(), "")
        if name and q.lower() in name.lower():
            results.append({"symbol": base, "name": name, "exchange": "Binance"})
            seen.add(base)
            if len(results) >= limit:
                break
    return results
