import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("database/financial_data.db")

print("=" * 80)
print("DAY 31 — FINANCIAL RATIOS CHECK")
print("=" * 80)

print("\nDATABASE:")
print(DB_PATH.resolve())

if not DB_PATH.exists():
    print("\nERROR: Database not found.")
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)

try:
    # Get table names
    tables = pd.read_sql_query(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """,
        conn
    )

    print("\nDATABASE TABLES:")
    for table in tables["name"]:
        print("-", table)

    # Read financial_ratios
    df = pd.read_sql_query(
        "SELECT * FROM financial_ratios LIMIT 5",
        conn
    )

    print("\n" + "=" * 80)
    print("FINANCIAL RATIOS")
    print("=" * 80)

    print("\nShape of first 5 rows:", df.shape)

    print("\nCOLUMNS:")
    for i, col in enumerate(df.columns, start=1):
        print(f"{i:2}. {col}")

    print("\nFIRST 5 ROWS:")
    print(df.to_string(index=False))

    # Full shape
    count_df = pd.read_sql_query(
        "SELECT COUNT(*) AS row_count FROM financial_ratios",
        conn
    )

    print("\nTOTAL ROWS:")
    print(count_df["row_count"].iloc[0])

finally:
    conn.close()

print("\n" + "=" * 80)
print("CHECK COMPLETED")
print("=" * 80)