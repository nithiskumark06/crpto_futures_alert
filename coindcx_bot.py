import pandas as pd
import numpy as np
import requests
import time
import telegram
from datetime import datetime
import asyncio
import ta
from dotenv import load_dotenv
import os

load_dotenv() # Load environment variables from .env file

BINANCE_API = "https://api.binance.com/api/v3/klines"
BYBIT_API = "https://api.bybit.com/v2/public/kline/list"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
COINS = os.getenv("COINS", "BTCUSDT,ETHUSDT").split(",")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ TELEGRAM_TOKEN and TELEGRAM_CHAT_ID must be set in .env file!")

print(f"✅ Loaded {len(COINS)} coins: {', '.join(COINS)}")

bot = telegram.Bot(token=TELEGRAM_TOKEN)

def get_ohlcv(symbol, interval='5m', limit=500):
    try:
        url = f"{BINANCE_API}?symbol={symbol}&interval={interval}&limit={limit}"
        r = requests.get(url, timeout=10)

        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data, columns=[
                    'timestamp', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades',
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])

                df[['open','high','low','close','volume']] = df[
                    ['open','high','low','close','volume']
                ].astype(float)

                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                return df
    except Exception as e:
        print(f"⚠ Binance error for {symbol}: {e}")
    
    try:
        bybit_interval = interval.replace("m", "")

        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": bybit_interval,
            "limit": limit
        }

        r = requests.get(BYBIT_API, params=params, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()

        if data.get("retCode") != 0:
            return None

        candles = data['result']['list']
        if not candles:
            return None

        df = pd.DataFrame(candles, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])

        df[['open','high','low','close','volume']] = df[
            ['open','high','low','close','volume']
        ].astype(float)

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df.sort_values('timestamp')

        return df

    except Exception as e:
        print(f"❌ Bybit error for {symbol}: {e}")
        return None
    
def calculate_indicators(df):
    try:
        df['ema9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
        df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
        df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
        df['ema200'] = ta.trend.EMAIndicator(df['close'], window=200).ema_indicator()
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
        return df
    except:
        return None 

def get_mtf_trends(df_5m, symbol):
    try:
        df_15m = get_ohlcv(symbol, '15m', 300)
        df_15m = calculate_indicators(df_15m)
        
        df_1h = get_ohlcv(symbol, '1h', 200)
        df_1h = calculate_indicators(df_1h)
        
        latest_5m = df_5m.iloc[-1]
        latest_15m = df_15m.iloc[-1]
        latest_1h = df_1h.iloc[-1]
        
        # Trend detection
        trend_5m_bull = (latest_5m['ema9'] > latest_5m['ema20'] and 
                         latest_5m['ema20'] > latest_5m['ema50'] and 
                         latest_5m['ema50'] > latest_5m['ema200'])
        
        trend_5m_bear = (latest_5m['ema200'] > latest_5m['ema50'] and 
                         latest_5m['ema50'] > latest_5m['ema20'] and 
                         latest_5m['ema20'] > latest_5m['ema9'])
        
        trend_15m_bull = (latest_15m['ema9'] > latest_15m['ema20'] and 
                          latest_15m['ema20'] > latest_15m['ema50'] and 
                          latest_15m['ema50'] > latest_15m['ema200'])
        
        trend_15m_bear = (latest_15m['ema200'] > latest_15m['ema50'] and 
                          latest_15m['ema50'] > latest_15m['ema20'] and 
                          latest_15m['ema20'] > latest_15m['ema9'])
        
        trend_1h_bull = (latest_1h['ema9'] > latest_1h['ema20'] and 
                         latest_1h['ema20'] > latest_1h['ema50'] and 
                         latest_1h['ema50'] > latest_1h['ema200'])
        
        trend_1h_bear = (latest_1h['ema200'] > latest_1h['ema50'] and 
                         latest_1h['ema50'] > latest_1h['ema20'] and 
                         latest_1h['ema20'] > latest_1h['ema9'])
        
        return {
            'trend_5m_bull': trend_5m_bull,
            'trend_5m_bear': trend_5m_bear,
            'trend_15m_bull': trend_15m_bull,
            'trend_15m_bear': trend_15m_bear,
            'trend_1h_bull': trend_1h_bull,
            'trend_1h_bear': trend_1h_bear,
            'latest_5m': latest_5m,
            'latest_15m': latest_15m,
            'latest_1h': latest_1h
        }
    except:
        return None

def analyze_symbol(symbol):
    try:
        df_5m = get_ohlcv(symbol, '5m', 500)
        df_5m = calculate_indicators(df_5m)
        
        mtf = get_mtf_trends(df_5m, symbol)
        latest = mtf['latest_5m']
        
        vol_ma_5m = df_5m['volume'].rolling(20).mean().iloc[-1]
        vol_strength_5m = (df_5m['volume'].iloc[-1] / vol_ma_5m - 1) * 100 if df_5m['volume'].iloc[-1] > vol_ma_5m else 0
        vol_strength_5m = min(100, vol_strength_5m)
        
        adx_1h_proxy = mtf['latest_1h']['atr'] / mtf['latest_1h']['close'] * 100 * 2
        
        bull_score = 0
        bear_score = 0
        
        if latest['ema20'] > latest['ema50']: bull_score += 1
        if latest['close'] > latest['ema50']: bull_score += 1
        if adx_1h_proxy > 22: bull_score += 1
        if latest['rsi'] > 55: bull_score += 1
        if vol_strength_5m > 50: bull_score += 1
        if mtf['trend_15m_bull']: bull_score += 1
        
        if latest['ema200'] > latest['ema50']: bear_score += 1
        if latest['close'] < latest['ema50']: bear_score += 1
        if adx_1h_proxy > 22: bear_score += 1
        if latest['rsi'] < 45: bear_score += 1
        if vol_strength_5m > 50: bear_score += 1
        if mtf['trend_15m_bear']: bear_score += 1
        
        market_regime = "TREND" if adx_1h_proxy > 30 else "RANGE" if adx_1h_proxy > 15 else "CHOP"
        
        # S/R Levels from 15m
        df_15m = get_ohlcv(symbol, '15m', 100)
        df_15m = calculate_indicators(df_15m)
        support_15m = df_15m['low'].rolling(10).min().iloc[-1] if mtf['trend_5m_bull'] else df_15m['low'].rolling(20).min().iloc[-1]
        resistance_15m = df_15m['high'].rolling(10).max().iloc[-1] if mtf['trend_5m_bear'] else df_15m['high'].rolling(20).max().iloc[-1]
        
        # 1H S/R
        df_1h = get_ohlcv(symbol, '1h', 50)
        df_1h = calculate_indicators(df_1h)
        support_1h = df_1h['low'].rolling(10).min().iloc[-1] if mtf['trend_5m_bull'] else df_1h['low'].rolling(20).min().iloc[-1]
        resistance_1h = df_1h['high'].rolling(10).max().iloc[-1] if mtf['trend_5m_bear'] else df_1h['high'].rolling(20).max().iloc[-1]
        
        # Risk Management
        atr_mult = 1.5
        atr_value = latest['atr']
        
        stop_loss = None
        profit_target = None
        rr_ratio = 0
        
        if bull_score >= 3:
            stop_loss = max(support_15m, latest['close'] - atr_value * atr_mult)
        elif bear_score >= 3:
            stop_loss = min(resistance_15m, latest['close'] + atr_value * atr_mult)
        
        if stop_loss:
            stop_distance = abs(latest['close'] - stop_loss)
            if stop_distance > 0:
                if bull_score >= 3:
                    profit_target = min(latest['close'] + stop_distance * 2, resistance_1h)
                    rr_ratio = round((profit_target - latest['close']) / stop_distance, 2)
                elif bear_score >= 3:
                    profit_target = max(latest['close'] - stop_distance * 2, support_1h)
                    rr_ratio = round((latest['close'] - profit_target) / stop_distance, 2)
        
        return {
            'symbol': symbol,
            'price': latest['close'],
            'regime': market_regime,
            'bull_score': bull_score,
            'bear_score': bear_score,
            'stop_loss': round(stop_loss, 4) if stop_loss else None,
            'profit_target': round(profit_target, 4) if profit_target else None,
            'rr_ratio': rr_ratio,
            'vol_strength': round(vol_strength_5m, 1),
            'strong_bull': bull_score >= 3 and market_regime != "CHOP",
            'strong_bear': bear_score >= 3 and market_regime != "CHOP"
        }
    except:
        return {
        'symbol': symbol,
        'price': None,
        'regime': 'ERROR',
        'bull_score': 0,
        'bear_score': 0,
        'stop_loss': None,
        'profit_target': None,
        'rr_ratio': 0,
        'vol_strength': 0,
        'strong_bull': False,
        'strong_bear': False}

async def send_telegram_message(message):
   try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode='HTML')
        print(f"✅ Telegram sent: {datetime.now()}")
       
   except Exception as e:
        print(f"❌ Telegram error: {e}")

def format_telegram_message(analysis):
    emoji = "🟢" if analysis['strong_bull'] else "🔴" if analysis['strong_bear'] else "⚪"
    signal = "🚀 STRONG BULL" if analysis['strong_bull'] else "🔻 STRONG BEAR" if analysis['strong_bear'] else "⏳ WAIT"
    
    stop_str = f"<b>{analysis['stop_loss']}</b>" if analysis['stop_loss'] else "—"
    target_str = f"<b>{analysis['profit_target']}</b>" if analysis['profit_target'] else "—"
    rr_str = f"<b>{analysis['rr_ratio']}:1</b>" if analysis['rr_ratio'] > 0 else "—"
    
    message = f"""
{emoji} <b>{analysis['symbol']}</b> | ${analysis['price']:.4f}

📊 <b>Dashboard:</b>
• Regime: <b>{analysis['regime']}</b>
• Bull: <b>{analysis['bull_score']}/6</b> | Bear: <b>{analysis['bear_score']}/6</b>

🎯 <b>{signal}</b>
• Stop: {stop_str}
• Target: {target_str} 
• R:R: {rr_str}

⏰ {datetime.now().strftime('%H:%M:%S IST')}
    """
    return message.strip()

async def main():
    print("🚀 Pro Scalping Bot")
    print("📡 Monitoring:", ', '.join(COINS))
    
    while True:
        try:
            for symbol in COINS:
                analysis = analyze_symbol(symbol)
                
                if analysis['strong_bull'] or analysis['strong_bear']:
                    message = format_telegram_message(analysis)
                    await send_telegram_message(message)
                
                print(f"📊 {symbol}: Bull={analysis['bull_score']}/6, Bear={analysis['bear_score']}/6, Regime={analysis['regime']}")
            
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
