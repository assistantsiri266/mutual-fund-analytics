from pathlib import Path
import sqlite3

import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = (
    PROJECT_ROOT
    / "database"
    / "financial_data.db"
)

MARKET_CAP_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "market_cap.csv"
)


# ============================================================
# DISPLAY PATH INFORMATION
# ============================================================

print("=" * 80)

print("DATABASE PATH:")
print(DB_PATH)

print()

print("DATABASE EXISTS:")
print(DB_PATH.exists())

print()

print("MARKET CAP FILE PATH:")
print(MARKET_CAP_PATH)

print()

print("MARKET CAP FILE EXISTS:")
print(MARKET_CAP_PATH.exists())

print("=" * 80)


# ============================================================
# VALIDATE FILES
# ============================================================

if not DB_PATH.exists():

    raise FileNotFoundError(
        f"Database file was not found:\n{DB_PATH}"
    )


if not MARKET_CAP_PATH.exists():

    raise FileNotFoundError(
        f"Market cap CSV file was not found:\n{MARKET_CAP_PATH}"
    )


# ============================================================
# LOAD MARKET CAP DATA
# ============================================================

market_cap_df = pd.read_csv(
    MARKET_CAP_PATH
)


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

market_cap_df.columns = (
    market_cap_df.columns
    .astype(str)
    .str.strip()
    .str.lower()
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "company_id",
    "market_cap_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
]


missing_columns = [
    column
    for column in required_columns
    if column not in market_cap_df.columns
]


if missing_columns:

    raise ValueError(
        "The following required columns are missing:\n"
        f"{missing_columns}"
    )


# ============================================================
# CLEAN COMPANY IDs
# ============================================================

market_cap_df["company_id"] = (
    market_cap_df["company_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ============================================================
# CONVERT VALUATION COLUMNS TO NUMERIC
# ============================================================

valuation_columns = [
    "market_cap_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
]


for column in valuation_columns:

    market_cap_df[column] = pd.to_numeric(
        market_cap_df[column],
        errors="coerce"
    )


# ============================================================
# REMOVE DUPLICATE COMPANIES
# ============================================================

market_cap_df = (
    market_cap_df
    .drop_duplicates(
        subset=["company_id"],
        keep="last"
    )
    .reset_index(
        drop=True
    )
)


# ============================================================
# DISPLAY CLEAN DATA
# ============================================================

print()

print("MARKET CAP DATA:")

print(
    market_cap_df
)

print()

print("TOTAL COMPANIES:")

print(
    market_cap_df.shape[0]
)


# ============================================================
# SAVE DATA TO SQLITE
# ============================================================

connection = sqlite3.connect(
    DB_PATH
)


try:

    market_cap_df.to_sql(
        name="valuation",
        con=connection,
        if_exists="replace",
        index=False
    )


finally:

    connection.close()


# ============================================================
# VERIFY DATABASE TABLE
# ============================================================

connection = sqlite3.connect(
    DB_PATH
)


try:

    verification_df = pd.read_sql_query(
        """
        SELECT *
        FROM valuation
        ORDER BY company_id
        """,
        connection
    )


finally:

    connection.close()


# ============================================================
# DISPLAY VERIFICATION
# ============================================================

print()

print("=" * 80)

print("DATABASE VERIFICATION:")

print(
    verification_df
)

print()

print("VALUATION TABLE ROWS:")

print(
    verification_df.shape[0]
)

print()

print("VALUATION TABLE COLUMNS:")

print(
    verification_df.columns.tolist()
)

print("=" * 80)

print()

print(
    "MARKET CAP DATA ADDED TO "
    "valuation TABLE SUCCESSFULLY!"
)

print("=" * 80)