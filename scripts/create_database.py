import pandas as pd
import sqlite3
from pathlib import Path
PROCESSED_FOLDER = Path("data/processed")
DATABASE_FOLDER = Path("data/db")

DATABASE_FOLDER.mkdir(parents=True, exist_ok=True)

db_path = DATABASE_FOLDER / "bluestock_mf.db"
conn = sqlite3.connect(db_path)

print("Database Connected Successfully")
csv_files = list(PROCESSED_FOLDER.glob("*.csv"))

print("Processed CSV Files Found:")

for file in csv_files:
    print(file.name)
for file in csv_files:

    table_name = file.stem

    df = pd.read_csv(file)

    df.to_sql(
        table_name,
        conn,
        if_exists="replace",
        index=False
    )

    print(f"Loaded {table_name} into SQLite")
cursor = conn.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table';
""")

tables = cursor.fetchall()

print("\nTables Created:\n")

for table in tables:
    print(table[0])
conn.close()

print("\nDatabase Created Successfully!")