import sqlite3
import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = (
    BASE_DIR
    / "database"
    / "financial_data.db"
)

SECTOR_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "company_sectors.csv"
)


# ============================================================
# CHECK FILES
# ============================================================

print("=" * 70)

print("DATABASE PATH:")
print(DATABASE_PATH)

print("\nDATABASE EXISTS:")
print(DATABASE_PATH.exists())

print("\nSECTOR FILE PATH:")
print(SECTOR_FILE)

print("\nSECTOR FILE EXISTS:")
print(SECTOR_FILE.exists())

print("=" * 70)


# ============================================================
# READ SECTOR DATA
# ============================================================

if not SECTOR_FILE.exists():

    raise FileNotFoundError(
        f"\nSector mapping file was not found:\n{SECTOR_FILE}"
    )


sector_data = pd.read_csv(
    SECTOR_FILE
)

print("\nSECTOR DATA:")

print(
    sector_data.head()
)

print("\nTOTAL SECTOR MAPPING ROWS:")

print(
    sector_data.shape[0]
)


# ============================================================
# CONNECT TO DATABASE
# ============================================================

connection = sqlite3.connect(
    DATABASE_PATH
)


# ============================================================
# READ FINANCIAL RATIOS
# ============================================================

financial_ratios = pd.read_sql_query(
    """
    SELECT *
    FROM financial_ratios
    """,
    connection
)

print("\nFINANCIAL RATIOS SHAPE:")

print(
    financial_ratios.shape
)


# ============================================================
# REMOVE OLD SECTOR COLUMNS
# ============================================================

old_sector_columns = [

    "broad_sector",

    "sub_sector"

]

for column in old_sector_columns:

    if column in financial_ratios.columns:

        financial_ratios.drop(

            columns=column,

            inplace=True

        )


# ============================================================
# MERGE SECTOR DATA
# ============================================================

financial_ratios = financial_ratios.merge(

    sector_data,

    on="company_id",

    how="left"

)


# ============================================================
# CHECK MERGE RESULT
# ============================================================

print("\nUPDATED FINANCIAL RATIOS COLUMNS:")

print(
    financial_ratios.columns.tolist()
)

print("\nSECTOR PREVIEW:")

print(

    financial_ratios[

        [

            "company_id",

            "broad_sector",

            "sub_sector"

        ]

    ]

    .drop_duplicates()

    .head(20)

)


# ============================================================
# COUNT COMPANIES WITH SECTOR DATA
# ============================================================

company_sector_status = (

    financial_ratios[

        [

            "company_id",

            "broad_sector"

        ]

    ]

    .drop_duplicates()

)


mapped_companies = (

    company_sector_status[

        "broad_sector"

    ]

    .notna()

    .sum()

)


unmapped_companies = (

    company_sector_status[

        "broad_sector"

    ]

    .isna()

    .sum()

)


print("\nCOMPANIES WITH SECTOR DATA:")

print(
    mapped_companies
)


print("\nCOMPANIES WITHOUT SECTOR DATA:")

print(
    unmapped_companies
)


# ============================================================
# SAVE UPDATED TABLE
# ============================================================

financial_ratios.to_sql(

    "financial_ratios",

    connection,

    if_exists="replace",

    index=False

)


# ============================================================
# VERIFY DATABASE
# ============================================================

verification = pd.read_sql_query(

    """

    SELECT

        company_id,

        broad_sector,

        sub_sector

    FROM financial_ratios

    WHERE broad_sector IS NOT NULL

    GROUP BY

        company_id,

        broad_sector,

        sub_sector

    ORDER BY company_id

    LIMIT 20

    """,

    connection

)


print("\nDATABASE VERIFICATION:")

print(
    verification
)


# ============================================================
# CLOSE CONNECTION
# ============================================================

connection.close()


print("\n" + "=" * 70)

print(
    "SECTOR DATA ADDED TO financial_ratios SUCCESSFULLY!"
)

print("=" * 70)