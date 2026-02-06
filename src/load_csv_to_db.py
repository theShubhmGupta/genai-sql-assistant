import sqlite3
import pandas as pd
import os

# Database path
DB_PATH = "data/target.db"

# CSV folder path
CSV_FOLDER = "data/csv"

# Connect to database
conn = sqlite3.connect(DB_PATH)

# Mapping: table name -> csv file name
tables = {
    "customers": "customers.csv",
    "orders": "orders.csv",
    "order_items": "order_items.csv",
    "payments": "payments.csv",
    "products": "products.csv",
    "sellers": "sellers.csv",
    "geolocation": "geolocation.csv",
    "order_reviews": "order_reviews.csv"
}

for table, csv_file in tables.items():
    csv_path = os.path.join(CSV_FOLDER, csv_file)
    print(f"Loading {csv_file} into {table}...")

    df = pd.read_csv(csv_path, encoding="latin1")

    df.to_sql(
        table,
        conn,
        if_exists="replace",
        index=False
    )

    print(f"{table} loaded successfully!")

conn.close()

print("✅ All CSV files loaded into SQLite database")
