import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask

# === CONFIGURATION ===
DHAN_API_KEY = "your_dhan_api_key"
DHAN_CLIENT_ID = "your_client_id"
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_telegram_chat_id"

FO_SYMBOLS = ["RELIANCE", "TCS", "INFY", "ICICIBANK", "HDFCBANK", "SBIN", "AXISBANK", "LT", "ITC", "MARUTI"]

app = Flask(__name__)

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)

def fetch_ohlcv_dhan(symbol, interval="1d", limit=100):
    try:
        url = f"https://api.dhan.co/market/v1/chart/intraday/{symbol}/NSE/{interval}?limit={limit}"
        headers = {
            "accept": "application/json",
            "access-token": DHAN_API_KEY,
            "client-id": DHAN_CLIENT_ID
        }
        response = requests.get(url, headers=headers)
        candles = response.json().get("data", [])
        df = pd.DataFrame(candles, columns=["datetime", "open", "high", "low", "close", "volume"])
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}:", e)
        return pd.DataFrame()

def meets_criteria(symbol):
    try:
        df_daily = fetch_ohlcv_dhan(symbol, "1d", limit=15)
        df_1h = fetch_ohlcv_dhan(symbol, "1h", limit=100)

        if df_daily.empty or df_1h.empty:
            return False

        df_daily.ta.ema(length=88, append=True)
        df_daily.ta.rsi(length=14, append=True)
        df_daily.ta.kc(length=21, scalar=1.0, append=True)

        match_count = 0
        for i in range(-15, 0):
            row = df_daily.iloc[i]
            if (
                row["close"] < row["KC_Lower_21_1.0"] and
                row["close"] < row["EMA_88"] and
                row["RSI_14"] < 40
            ):
                match_count += 1

        if match_count < 3:
            return False

        df_1h.ta.rsi(length=14, append=True)
        df_1h.ta.kc(length=21, scalar=1.0, append=True)

        rsi = df_1h["RSI_14"]
        kc_lower = df_1h["KC_Lower_21_1.0"]
        close = df_1h["close"]

        i = 0
        while i < len(df_1h) - 3:
            if close[i] < kc_lower[i] and rsi[i] < 40:
                # pullback
                j = i + 1
                while j < len(df_1h) - 2 and close[j] > kc_lower[j] and 40 <= rsi[j] < 50:
                    j += 1
                if j < len(df_1h) - 1 and close[j] < kc_lower[j] and rsi[j] < 40:
                    return True
            i += 1

    except Exception as e:
        print(f"Error in {symbol}: {e}")
    return False

@app.route("/")
def index():
    return "✅ Bearish Keltner Screener is live!"

@app.route("/run")
def run_screener():
    matched = []
    for symbol in FO_SYMBOLS:
        if meets_criteria(symbol):
            matched.append(symbol)
    if matched:
        if matched:
    msg = "🔻 *Bearish Keltner Screener Alerts:*\n" + "\n".join(matched)
        send_telegram_alert(msg)
        return f"Matched: {matched}"
    else:
        return "No matches found."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
