"""
load_db.py
----------
Creates the SQLite database (data/ecommerce.db) from schema.sql,
then loads the cleaned CSVs into it. Verifies row counts match after load.
"""

import sqlite3
import csv
import os

DB_PATH = "data/ecommerce.db"
SCHEMA_PATH = "sql/schema.sql"
CLEAN_DIR = "data/cleaned"


def load_csv_into_table(conn, csv_path, table_name):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        placeholders = ", ".join(["?"] * len(header))
        col_list = ", ".join(header)
        rows = []
        for row in reader:
            # convert empty strings to None so SQLite stores real NULLs
            rows.append([v if v != "" else None for v in row])
        conn.executemany(
            f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})",
            rows,
        )
        return len(rows)


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())

    # Load order matters: customers/products first (parents), then orders, then order_items
    counts = {}
    counts["customers"] = load_csv_into_table(conn, f"{CLEAN_DIR}/customers_clean.csv", "customers")
    counts["products"] = load_csv_into_table(conn, f"{CLEAN_DIR}/products_clean.csv", "products")
    counts["orders"] = load_csv_into_table(conn, f"{CLEAN_DIR}/orders_clean.csv", "orders")
    counts["order_items"] = load_csv_into_table(conn, f"{CLEAN_DIR}/order_items_clean.csv", "order_items")

    conn.commit()

    print("Rows inserted:")
    for table, n in counts.items():
        db_count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        status = "OK" if db_count == n else "MISMATCH"
        print(f"  {table:15s}: csv={n:5d}  db={db_count:5d}  [{status}]")

    conn.close()
    print(f"\nDatabase ready at {DB_PATH}")


if __name__ == "__main__":
    main()
