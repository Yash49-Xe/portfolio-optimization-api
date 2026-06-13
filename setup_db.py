import sqlite3
import os

DB_PATH = "wealth.db"

def setup_database():
    if os.path.exists(DB_PATH):
        print(f"[SETUP] '{DB_PATH}' already exists. Ensuring all tables are present...")
    else:
        print(f"[SETUP] Creating new database '{DB_PATH}'...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode=WAL;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL,
            ticker      TEXT    NOT NULL,
            price       REAL    NOT NULL,
            UNIQUE(date, ticker)
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS treasury_rates (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT    NOT NULL UNIQUE,
            rate_10yr   REAL    NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT    NOT NULL,
            type            TEXT    NOT NULL,
            ticker          TEXT    NOT NULL,
            shares          REAL    NOT NULL,
            price_per_share REAL    NOT NULL,
            total_amount    REAL    NOT NULL
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"[SETUP] Database '{DB_PATH}' is ready.")
    print("[SETUP] Tables ensured: market_data, treasury_rates, transactions")
    print("[SETUP] Run the app — the background sync worker will populate market_data and treasury_rates automatically.")


if __name__ == "__main__":
    setup_database()