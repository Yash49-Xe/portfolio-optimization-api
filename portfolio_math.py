import sqlite3
import pandas as pd

conn = sqlite3.connect("wealth.db")

df = pd.read_sql_query("SELECT * FROM market_data",conn)

df = df.sort_values(by = ["ticker", "date"])

df["daily_return"] = df.groupby("ticker")["price"].pct_change()
metrices = df.groupby("ticker")["daily_return"].agg(["mean", "std"])
print(metrices)
print(df)
conn.close()