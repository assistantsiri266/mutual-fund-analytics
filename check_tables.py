import sqlite3
import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = (
    BASE_DIR
    / "database"
    / "financial_data.db"
)


# ============================================================
# CONNECT TO DATABASE
# ============================================================

connection = sqlite3.connect(
    DATABASE_PATH
)


# ============================================================
# FIND UNMAPPED COMPANIES
# ============================================================

unmapped = pd.read_sql_query(
    """
    SELECT DISTINCT
        company_id
    FROM financial_ratios
    WHERE broad_sector IS NULL
    ORDER BY company_id
    """,
    connection
)


# ============================================================
# FIND ALL COMPANIES
# ============================================================

all_companies = pd.read_sql_query(
    """
    SELECT DISTINCT
        company_id,
        broad_sector,
        sub_sector
    FROM financial_ratios
    ORDER BY company_id
    """,
    connection
)


# ============================================================
# CLOSE DATABASE
# ============================================================

connection.close()


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("=" * 70)

print("UNMAPPED COMPANY IDs:")

print(unmapped.to_string(index=False))

print("\nTOTAL UNMAPPED COMPANIES:")

print(
    unmapped.shape[0]
)

print("\n" + "=" * 70)

print("ALL COMPANY SECTOR STATUS:")

print(
    all_companies.to_string(
        index=False
    )
)

print("\n" + "=" * 70)