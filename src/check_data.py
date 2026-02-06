import sqlite3

conn = sqlite3.connect("data/target.db")
cursor = conn.cursor()

tables = [
    "customers", "orders", "order_items",
    "payments", "products", "sellers",
    "geolocation", "order_reviews"
]

for table in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"{table}: {count} rows")

conn.close()


