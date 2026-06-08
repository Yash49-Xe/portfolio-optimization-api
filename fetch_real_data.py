import yfinance as yf
import sqlite3
import pandas as pd

def update_market_data():
    print("[SYNC WORKER] Waking up to fetch live market data...")
    tickers = [
        "AAPL", "MSFT", "GOOGL", "AMZN",  # Tech Giants
        "JPM", "V",                       # Finance & Payments
        "WMT", "PG",                      # Retail & Consumer Goods
        "SPY", "QQQ",                     # Massive Index Funds
        "BTC-USD", "ETH-USD"              # Cryptocurrency
    ]
    all_data = []
    
    try:
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            df = stock.history(period="3y")
            
            df = df.reset_index()
            df = df[["Date", "Close"]].copy()
            df["ticker"] = ticker
            df = df.rename(columns={"Date": "date", "Close": "price"})
            df["date"] = df["date"].dt.strftime('%Y-%m-%d')
            all_data.append(df)
            
        final_df = pd.concat(all_data, ignore_index=True)
        
        conn = sqlite3.connect("wealth.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM market_data")
        final_df.to_sql("market_data", conn, if_exists="append", index=False)
        conn.commit()
        conn.close()
        
        print("[SYNC WORKER] Database successfully updated. Going back to sleep.")
        
    except Exception as e:
        print(f"[SYNC WORKER ERROR] Failed to update data: {e}")

if __name__ == "__main__":
    update_market_data()