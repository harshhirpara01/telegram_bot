import asyncio
import logging
import requests
import pandas as pd
import ta
from telegram import Bot
from datetime import datetime

# Configure logging
logging.basicConfig(
    filename="forex_signal.log", 
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# API Keys and Configuration
API_KEY = "CDZ46H6B37H9V8L9"
TELEGRAM_BOT_TOKEN = "7954541244:AAH6_q08eesfGIgC0MBpqzwb2aGaUnJMVOs"
CHAT_ID = "-1002499455698"
BASE_URL = "https://www.alphavantage.co/query"

# Currency pairs to monitor
CURRENCY_PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD"]

# Function to fetch forex data
def get_historical_forex_data(from_currency, to_currency):
    params = {
        "function": "FX_DAILY",
        "from_symbol": from_currency,
        "to_symbol": to_currency,
        "apikey": API_KEY,
        "outputsize": "compact"
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if "Time Series FX (Daily)" in data:
        df = pd.DataFrame.from_dict(data["Time Series FX (Daily)"], orient="index")
        df = df.astype(float)
        df = df.rename(columns={"1. open": "open", "2. high": "high", "3. low": "low", "4. close": "close"})
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df
    return None

# Function to generate trading signals
def generate_signals(df):
    df["SMA_20"] = ta.trend.sma_indicator(df["close"], window=20)
    df["SMA_50"] = ta.trend.sma_indicator(df["close"], window=50)
    df["RSI"] = ta.momentum.rsi(df["close"], window=14)

    df["Signal"] = "HOLD"
    df.loc[df["SMA_20"] > df["SMA_50"], "Signal"] = "BUY"
    df.loc[df["SMA_20"] < df["SMA_50"], "Signal"] = "SELL"
    df.loc[df["RSI"] > 70, "Signal"] = "SELL"  
    df.loc[df["RSI"] < 30, "Signal"] = "BUY"  

    return df[["close", "SMA_20", "SMA_50", "RSI", "Signal"]]

# Async function to send Telegram messages
async def send_telegram_message(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

# Main function to check signals and send alerts
async def check_forex_signals():
    for pair in CURRENCY_PAIRS:
        from_currency, to_currency = pair.split("/")
        logging.info(f"Checking signals for {pair}")
        
        forex_df = get_historical_forex_data(from_currency, to_currency)
        if forex_df is not None:
            signals = generate_signals(forex_df)
            latest_signal = signals.iloc[-1]
            message = (f"\U0001F4C8 *Forex Signal* \U0001F4C9\n"
                       f"\U0001F539 *Pair:* {pair}\n"
                       f"\U0001F4B0 *Price:* {latest_signal['close']}\n"
                       f"\U0001F4CA *Signal:* {latest_signal['Signal']}\n"
                       f"\U0001F4C9 *RSI:* {latest_signal['RSI']:.2f}")
            
            if latest_signal['Signal'] in ["BUY", "SELL"]:
                await send_telegram_message(message)
                logging.info(f"✅ Signal sent for {pair}: {latest_signal['Signal']}")
            else:
                logging.info(f"⏳ No strong signal for {pair}, holding position.")
        else:
            logging.error(f"❌ Failed to fetch data for {pair}")
    
    logging.info("Waiting 5 minutes before next check...")
    await asyncio.sleep(300)  # Wait for 5 minutes before running again

# Run the bot
async def main():
    logging.info("🚀 Forex Signal Bot Started! Checking every 5 minutes...")
    print("🚀 Forex Signal Bot Started! Checking every 5 minutes...")
    while True:
        await check_forex_signals()

if __name__ == "__main__":
    asyncio.run(main())
