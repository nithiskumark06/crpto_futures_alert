import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime
import ta

# ================== CONFIG ==================
BINANCE_API = "https://api.binance.com/api/v3/klines"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

COINS = os.environ.get("COINS", "BTCUSDT,ETHUSDT").split(",")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise RuntimeError("❌ TELEGRAM_TOKEN or TELEGRAM_CHAT_ID not set")

print(f"✅ Loaded {len(COINS)} coins: {', '.join(COINS)}")

# ================== TELEGRAM ==================
def send_telegram_message(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        r = requests.post(url, json=payload, timeout=10)
        print(f"📨 Telegram response: {r.status_code}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

# ================== DATA ==================
def get_ohlcv(symbol, interval="5m", limit=500):
    try:
        url = f"{BINANCE_API}?symbol={symbol}&interval={interval}&limit={limit}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()
        if not data:
            return None

        df = pd.DataFrame(data, columns=[
            "timestamp","open","high","low","close","volume",
            "close_time","quote_volume","trades",
            "taker_buy_base","taker_buy_quote","ignore"
        ])

        df[["open","high","low","close","volume"]] = df[
            ["open","high","low","close","volume"]
        ].astype(float)

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df

    except Exception as e:
        print(f"❌ Binance error {symbol}: {e}")
        return None

# ================== INDICATORS ==================
def calculate_indicators(df):
    if df is None or len(df) < 210:
        return None

    df["ema9"] = ta.trend.EMAIndicator(df["close"], 9).ema_indicator()
    df["ema20"] = ta.trend.EMAIndicator(df["close"], 20).ema_indicator()
    df["ema50"] = ta.trend.EMAIndicator(df["close"], 50).ema_indicator()
    df["ema200"] = ta.trend.EMAIndicator(df["close"], 200).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], 14).rsi()
    df["atr"] = ta.volatility.AverageTrueRange(
        df["high"], df["low"], df["close"], 14
    ).average_true_range()

    return df

# ================== ANALYSIS ==================
def analyze_symbol(symbol):
    df5 = calculate_indicators(get_ohlcv(symbol, "5m", 500))
    df15 = calculate_indicators(get_ohlcv(symbol, "15m", 300))
    df1h = calculate_indicators(get_ohlcv(symbol, "1h", 200))

    if df5 is None or df15 is None or df1h is None:
        return None

    l5, l15, l1h = df5.iloc[-1], df15.iloc[-1], df1h.iloc[-1]

    bull = 0
    bear = 0

    if l5["ema20"] > l5["ema50"]: bull += 1
    if l5["close"] > l5["ema50"]: bull += 1
    if l5["rsi"] > 55: bull += 1
    if l15["ema9"] > l15["ema20"] > l15["ema50"]: bull += 1

    if l5["ema200"] > l5["ema50"]: bear += 1
    if l5["close"] < l5["ema50"]: bear += 1
    if l5["rsi"] < 45: bear += 1
    if l15["ema200"] > l15["ema50"]: bear += 1

    adx_proxy = (l1h["atr"] / l1h["close"]) * 100 * 2
    regime = "TREND" if adx_proxy > 30 else "RANGE" if adx_proxy > 15 else "CHOP"

    strong_bull = bull >= 3 and regime != "CHOP"
    strong_bear = bear >= 3 and regime != "CHOP"

    return {
        "symbol": symbol,
        "price": round(l5["close"], 4),
        "bull": bull,
        "bear": bear,
        "regime": regime,
        "strong_bull": strong_bull,
        "strong_bear": strong_bear
    }

# ================== FORMAT ==================
def format_message(a):
    emoji = "🟢" if a["strong_bull"] else "🔴"
    signal = "🚀 STRONG BULL" if a["strong_bull"] else "🔻 STRONG BEAR"

    return f"""
{emoji} <b>{a['symbol']}</b> | ${a['price']}

📊 Regime: <b>{a['regime']}</b>
🐂 Bull Score: <b>{a['bull']}/6</b>
🐻 Bear Score: <b>{a['bear']}/6</b>

🎯 <b>{signal}</b>

⏰ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
""".strip()

# ================== MAIN ==================
if __name__ == "__main__":
    print("🚀 GitHub Scalping Scan Started")

    sent = 0

    for coin in COINS:
        print(f"🔍 Scanning {coin}")
        analysis = analyze_symbol(coin)

        if not analysis:
            print(f"⚠ Data issue for {coin}")
            continue

        if analysis["strong_bull"] or analysis["strong_bear"]:
            msg = format_message(analysis)
            send_telegram_message(msg)
            sent += 1
        else:
            print(f"⏳ No signal for {coin}")

    print(f"✅ Scan complete | Signals sent: {sent}")
