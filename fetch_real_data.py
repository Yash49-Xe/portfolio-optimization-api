import sqlite3
import pandas as pd
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FMP_API_KEY")
DB_PATH  = "wealth.db"

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "JPM", "V", "WMT", "SPY", "BTCUSD", "ETHUSD"]

def _upsert_market_data(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    cursor = conn.cursor()
    rows = df[["date", "ticker", "price"]].values.tolist()
    cursor.executemany(
        "INSERT OR REPLACE INTO market_data (date, ticker, price) VALUES (?, ?, ?)",
        rows
    )
    conn.commit()
    cursor.close()


def _upsert_treasury_rate(conn: sqlite3.Connection, date: str, rate: float) -> None:
    """
    Insert or replace the 10-year treasury rate for a given date.
    """
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO treasury_rates (date, rate_10yr) VALUES (?, ?)",
        (date, rate)
    )
    conn.commit()
    cursor.close()

def update_market_data() -> None:
    print("[SYNC WORKER] Waking up to fetch live data from FMP...")

    if not API_KEY:
        print("[SYNC WORKER ERROR] FMP_API_KEY is missing. Check your .env file.")
        return

    with httpx.Client(timeout=30.0) as client:
        _sync_historical_prices(client)
        _sync_treasury_rate(client)

    print("[SYNC WORKER] Sync cycle complete.")


def _sync_historical_prices(client: httpx.Client) -> None:
    all_data = []

    for ticker in TICKERS:
        url = (
            f"https://financialmodelingprep.com/stable/historical-price-eod/full"
            f"?symbol={ticker}&apikey={API_KEY}"
        )

        try:
            response = client.get(url)
        except httpx.RequestError as e:
            print(f"[NETWORK ERROR] Could not reach FMP for {ticker}: {e}")
            continue

        if response.status_code != 200:
            print(f"[HTTP ERROR] FMP returned {response.status_code} for {ticker}: {response.text[:200]}")
            continue

        try:
            data = response.json()
        except Exception as e:
            print(f"[JSON ERROR] Could not parse FMP response for {ticker}: {e}")
            continue

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            df = df[["date", "close"]].copy()
            df["ticker"] = ticker
            df = df.rename(columns={"close": "price"})
            all_data.append(df)
            print(f"[SYNC WORKER] Fetched {len(df)} rows for {ticker}.")
        else:
            print(f"[API WARNING] No valid price data returned for {ticker}: {data}")

    if not all_data:
        print("[SYNC WORKER WARNING] No price data was fetched in this cycle. Skipping DB write.")
        return

    final_df = pd.concat(all_data, ignore_index=True)

    conn = sqlite3.connect(DB_PATH)
    _upsert_market_data(conn, final_df)
    conn.close()

    print(f"[SYNC WORKER] Upserted {len(final_df)} price rows into market_data.")


def _sync_treasury_rate(client: httpx.Client) -> None:
    """
    Fetch the current 10-Year US Treasury rate from FMP and store it in treasury_rates.
    The optimizer reads this instead of using a hardcoded risk-free rate.
    """
    url = f"https://financialmodelingprep.com/stable/treasury-rates?apikey={API_KEY}"

    try:
        response = client.get(url)
    except httpx.RequestError as e:
        print(f"[NETWORK ERROR] Could not reach FMP for treasury rates: {e}")
        return

    if response.status_code != 200:
        print(f"[HTTP ERROR] FMP returned {response.status_code} for treasury rates: {response.text[:200]}")
        return

    try:
        data = response.json()
    except Exception as e:
        print(f"[JSON ERROR] Could not parse treasury rate response: {e}")
        return

    if not isinstance(data, list) or len(data) == 0:
        print(f"[API WARNING] Unexpected treasury rate response format: {data}")
        return

    latest = data[0]

    rate_10yr = latest.get("year10") or latest.get("tenYear")
    date      = latest.get("date")

    if rate_10yr is None or date is None:
        print(f"[API WARNING] Could not extract 10yr rate from response: {latest}")
        return

    conn = sqlite3.connect(DB_PATH)
    _upsert_treasury_rate(conn, date, float(rate_10yr))
    conn.close()

    print(f"[SYNC WORKER] Treasury rate updated: {rate_10yr}% on {date}.")


if __name__ == "__main__":
    update_market_data()