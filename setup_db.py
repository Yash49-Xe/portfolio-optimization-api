import sqlite3

conn = sqlite3.connect("wealth.db")

cursor = conn.cursor()

query = """
    CREATE TABLE market_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        ticker TEXT,
        price REAL
    );

    CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        type TEXT,
        ticker TEXT,
        share REAL,
        price_per_share REAL,
        total_amount REAL
    );


    INSERT INTO market_data
    VALUES
    (1,"2026-06-08","ABC",1299),
    (2,"2026-06-08","AAC",1399),
    (3,"2026-06-08","ABB",1199),
    (4,"2026-06-08","ACC",1259);

    INSERT INTO transactions
    VALUES
    (1,"2026-06-08","deposit","AAB",12,247,24290),
    (2,"2026-06-08","deposit","NAB",10,272,24220),
    (3,"2026-06-08","deposit","CAB",11,243,242330);
"""
cursor.executescript(query)

conn.commit()
cursor.close()
conn.close()

print("Database 'wealth.db' created successfully with mock data!")