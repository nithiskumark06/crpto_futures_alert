# 🚀 **Pro Scalping Bot** [![Telegram](https://img.shields.io/badge/Telegram-Join-blue?logo=telegram)](https://t.me/crypto_futures_06)


### 📊 Multi-Timeframe (MTF) Crypto Analysis & Telegram Alerts

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python"/>
  <img src="https://img.shields.io/badge/Exchange-Binance-yellow?logo=binance"/>
  <img src="https://img.shields.io/badge/Strategy-MTF%20Scalping-green"/>
  <img src="https://img.shields.io/badge/Alerts-Telegram-blue?logo=telegram"/>
</p>

> **A crypto scalping engine** using Python, combining multi-timeframe EMA structure, volume expansion, and risk-controlled trade planning — fully automated via **GitHub Actions**.

---

## ✨ **Key Features**

| 🎯 Core Intelligence     | 📊 Multi-Timeframe Logic | 🚨 Smart Alerts     |
| ------------------------ | ------------------------ | ------------------- |
| Confluence scoring (0–6) | 5m / 15m / 1h EMA stack  | Telegram alerts     |
| ATR-based stop & target  | Volume strength filter   | Strong signals only |
| Market regime detection  | Dynamic S/R zones        | Risk-reward ≥ 2:1   |
| Pine Script parity       | ADX proxy strength       | Auto-skip bad data  |

---

## 📈 **Strategy Flow**

```text
1️⃣ Fetch live OHLCV data (Binance)
2️⃣ Compute EMA, RSI, ATR, Volume
3️⃣ Evaluate 6-factor confluence
4️⃣ Detect TREND / RANGE / CHOP
5️⃣ Calculate Stop, Target & R:R
6️⃣ Push alerts to Telegram
```

---

## 🟢 **Sample Telegram Alert**

```text
🟢 BTCUSDT | $95,420.50

📊 Dashboard
• Regime: TREND
• Bull: 5/6 | Bear: 1/6
• Volume: 78.2%

🎯 STRONG BULL
• Stop: 94,850.25
• Target: 97,250.00
• R:R: 2.3 : 1
```

---

## 🧮 **Confluence Scoring (0–6)**

| Factor           | Bullish ✅ | Bearish ✅ |
| ---------------- | --------- | --------- |
| EMA20 > EMA50    | ✅         |           |
| Price vs EMA50   | ✅         |           |
| ADX Proxy > 22   | ✅         | ✅         |
| RSI Filter       | RSI > 55  | RSI < 45  |
| Volume Expansion | ✅         | ✅         |
| 15m Trend Bias   | ✅         | ✅         |

🎯 **Signal Rule:**
`Confluence ≥ 3 AND Market ≠ CHOP`

---

## 📦 **Dependencies**

```txt
pandas==2.2.2
numpy==2.1.1
requests==2.31.0
urllib3==2.1.0
python-telegram-bot==21.5
ta==0.11.0
python-dotenv==1.0.1
```

---

## 🛡️ **Reliability & Safety**

✔ Handles empty / NaN data
✔ Skips invalid symbols
✔ API timeout protection
✔ Never crashes on bad candles
✔ Telegram flood-safe
✔ GitHub Actions hardened


<p align="center">
<strong>Built with ❤️ for Traders, Quant Enthusiasts & Data Analysts</strong>
</p>

---

⚠️ **Disclaimer:**
This project is for educational purposes only.
Not financial advice. Trade at your own risk.
