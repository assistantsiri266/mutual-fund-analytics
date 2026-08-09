import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# DAY 32 — CAPITAL ALLOCATION HISTORY
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

CASHFLOW_FILE = DATA_DIR / "cashflow.xlsx"
OUTPUT_FILE = OUTPUT_DIR / "capital_allocation.csv"


print("=" * 80)
print("DAY 32 — CAPITAL ALLOCATION HISTORY")
print("=" * 80)


# ============================================================
# 1. LOAD CASH FLOW
# ============================================================

cashflow = pd.read_excel(
    CASHFLOW_FILE,
    header=1
)

print("\nCash-flow shape:", cashflow.shape)
print("Columns:", cashflow.columns.tolist())


# ============================================================
# 2. CHECK REQUIRED COLUMNS
# ============================================================

required = [
    "company_id",
    "year",
    "operating_activity",
    "investing_activity",
    "financing_activity"
]

missing = [
    c for c in required
    if c not in cashflow.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )


# ============================================================
# 3. NORMALIZE COMPANY ID
# ============================================================

def normalize_company_id(value):

    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    # Source data uses AGTL,
    # canonical ticker is ATGL
    if value == "AGTL":
        value = "ATGL"

    return value


cashflow["company_id"] = (
    cashflow["company_id"]
    .apply(normalize_company_id)
)


# ============================================================
# 4. NORMALIZE YEAR
# ============================================================
#
# IMPORTANT:
# Raw data contains values such as:
#
# Mar 2018
# Mar 2019
# Mar 2020
#
# Extract only the four-digit year.
# ============================================================

cashflow["year"] = (
    cashflow["year"]
    .astype(str)
    .str.extract(
        r"(\d{4})",
        expand=False
    )
)

cashflow["year"] = pd.to_numeric(
    cashflow["year"],
    errors="coerce"
)


# ============================================================
# 5. NORMALIZE FINANCIAL COLUMNS
# ============================================================

financial_columns = [
    "operating_activity",
    "investing_activity",
    "financing_activity"
]

for column in financial_columns:

    cashflow[column] = pd.to_numeric(
        cashflow[column],
        errors="coerce"
    )


# ============================================================
# 6. REMOVE INVALID ROWS
# ============================================================

cashflow = cashflow[
    cashflow["company_id"].notna()
].copy()

cashflow = cashflow[
    cashflow["year"].notna()
].copy()

cashflow = cashflow[
    cashflow[
        financial_columns
    ].notna().any(axis=1)
].copy()


# Remove metadata/header-like IDs
invalid_ids = {
    "ID",
    "COMPANY_ID",
    "TICKER",
    "YEAR"
}

cashflow = cashflow[
    ~cashflow["company_id"].isin(
        invalid_ids
    )
].copy()


# ============================================================
# 7. CONVERT YEAR TO INTEGER
# ============================================================

cashflow["year"] = (
    cashflow["year"]
    .astype(int)
)


# ============================================================
# 8. REMOVE DUPLICATE COMPANY-YEAR
# ============================================================

cashflow = (
    cashflow
    .sort_values(
        [
            "company_id",
            "year"
        ]
    )
    .drop_duplicates(
        subset=[
            "company_id",
            "year"
        ],
        keep="last"
    )
    .reset_index(drop=True)
)


print("\n" + "=" * 80)
print("HISTORICAL DATA VALIDATION")
print("=" * 80)

print(
    "\nHistorical cash-flow rows:",
    len(cashflow)
)

print(
    "Historical companies:",
    cashflow["company_id"].nunique()
)

print(
    "Years:",
    sorted(
        cashflow["year"].unique()
    )
)


# ============================================================
# 9. CAPITAL ALLOCATION CLASSIFICATION
# ============================================================

def classify_pattern(cfo, cfi, cff):

    if pd.isna(cfo):
        return None

    if pd.isna(cfi):
        return None

    if pd.isna(cff):
        return None

    cfo_sign = "+" if cfo >= 0 else "-"
    cfi_sign = "+" if cfi >= 0 else "-"
    cff_sign = "+" if cff >= 0 else "-"

    pattern = (
        cfo_sign,
        cfi_sign,
        cff_sign
    )

    mapping = {

        # Operations generate cash,
        # investment consumes cash,
        # financing pays out debt/equity
        ("+", "-", "-"):
            "Reinvestor",

        # Operations +,
        # investments generate cash,
        # financing negative
        ("+", "+", "-"):
            "Liquidating Assets",

        # Operations negative,
        # investments positive,
        # financing positive
        ("-", "+", "+"):
            "Distress Signal",

        # Operations negative,
        # investments negative,
        # financing positive
        ("-", "-", "+"):
            "Growth Funded by Debt",

        # All positive
        ("+", "+", "+"):
            "Cash Accumulator",

        # All negative
        ("-", "-", "-"):
            "Pre-Revenue",

        # CFO positive,
        # investment negative,
        # financing positive
        ("+", "-", "+"):
            "Mixed",

        # CFO negative,
        # investment positive,
        # financing negative
        ("-", "+", "-"):
            "Mixed"
    }

    return mapping.get(
        pattern,
        "Mixed"
    )


# ============================================================
# 10. SIGNS
# ============================================================

cashflow["cfo_sign"] = np.where(
    cashflow["operating_activity"] >= 0,
    "+",
    "-"
)

cashflow["cfi_sign"] = np.where(
    cashflow["investing_activity"] >= 0,
    "+",
    "-"
)

cashflow["cff_sign"] = np.where(
    cashflow["financing_activity"] >= 0,
    "+",
    "-"
)


# ============================================================
# 11. CAPITAL ALLOCATION LABEL
# ============================================================

cashflow[
    "capital_allocation_label"
] = cashflow.apply(
    lambda row: classify_pattern(
        row["operating_activity"],
        row["investing_activity"],
        row["financing_activity"]
    ),
    axis=1
)


# ============================================================
# 12. FINAL OUTPUT
# ============================================================

capital_allocation = cashflow[
    [
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "capital_allocation_label"
    ]
].copy()


capital_allocation = (
    capital_allocation
    .sort_values(
        [
            "company_id",
            "year"
        ]
    )
    .reset_index(drop=True)
)


# ============================================================
# 13. VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("FINAL VALIDATION")
print("=" * 80)

print(
    "\nRows:",
    len(capital_allocation)
)

print(
    "Companies:",
    capital_allocation[
        "company_id"
    ].nunique()
)

print(
    "Years:",
    sorted(
        capital_allocation[
            "year"
        ].unique()
    )
)

print(
    "Missing company_id:",
    capital_allocation[
        "company_id"
    ].isna().sum()
)

print(
    "Missing year:",
    capital_allocation[
        "year"
    ].isna().sum()
)

print(
    "Duplicate company-year:",
    capital_allocation.duplicated(
        [
            "company_id",
            "year"
        ]
    ).sum()
)


# ============================================================
# 14. PATTERN DISTRIBUTION
# ============================================================

print("\nHistorical pattern distribution:")

print(
    capital_allocation[
        "capital_allocation_label"
    ].value_counts()
)


# ============================================================
# 15. SAVE
# ============================================================

capital_allocation.to_csv(
    OUTPUT_FILE,
    index=False
)

print(
    "\nCapital allocation history saved:"
)

print(OUTPUT_FILE)


# ============================================================
# 16. RELOAD & VERIFY
# ============================================================

check = pd.read_csv(
    OUTPUT_FILE
)

print("\n" + "=" * 80)
print("FINAL FILE CHECK")
print("=" * 80)

print(
    "Rows:",
    len(check)
)

print(
    "Companies:",
    check[
        "company_id"
    ].nunique()
)

print(
    "Years:",
    sorted(
        check[
            "year"
        ].unique()
    )
)

print(
    "Duplicate company-year:",
    check.duplicated(
        [
            "company_id",
            "year"
        ]
    ).sum()
)

print("\nColumns:")
print(check.columns.tolist())

print("\nFirst 20 rows:")
print(
    check.head(20).to_string(
        index=False
    )
)

print("\n" + "=" * 80)
print("DAY 32 STEP 32.1 COMPLETE")
print("=" * 80)