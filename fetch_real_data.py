import requests
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FMP_API_KEY")

def update_market_data():
    print("[SYNC WORKER] Waking up to fetch live data from FMP...")
    
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "JPM", "V", "WMT", "SPY", "BTCUSD", "ETHUSD"]
    all_data = []
    
    try:
        if not API_KEY:
            raise ValueError("API Key is missing! Check your .env file.")

        for ticker in tickers:
            url = f"https://financialmodelingprep.com/stable/historical-price-eod/full?symbol={ticker}&apikey={API_KEY}"
            
            response = requests.get(url)
            
            if response.status_code != 200:
                print(f"[API HTTP ERROR] FMP returned {response.status_code} for {ticker}: {response.text}")
                continue
            
            try:
                data = response.json()
            except Exception as e:
                print(f"[JSON ERROR] Could not parse FMP data for {ticker}. Raw text: {response.text[:200]}")
                continue
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                df = df[["date", "close"]].copy()
                df["ticker"] = ticker
                df = df.rename(columns={"close": "price"})
                all_data.append(df)
            else:
                print(f"[API WARNING] No valid data in FMP Response for {ticker}: {data}")

    except Exception as e:
        print(f"[SYNC WORKER ERROR] Failed to update data: {e}")

if __name__ == "__main__":
    update_market_data()