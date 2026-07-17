import pandas as pd
import sqlite3
from pathlib import Path

# ======================================================
# Project Paths
# ======================================================

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "output"

DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)

# ======================================================
# Read CSV Files
# ======================================================

profitability = pd.read_csv(
    OUTPUT_DIR / "profitability_ratios.csv"
)

leverage = pd.read_csv(
    OUTPUT_DIR / "leverage_efficiency_ratios.csv"
)

cagr = pd.read_csv(
    OUTPUT_DIR / "cagr_results.csv"
)

cashflow = pd.read_csv(
    OUTPUT_DIR / "cashflow_kpis.csv"
)

print("Profitability:", profitability.shape)
print("Leverage:", leverage.shape)
print("CAGR:", cagr.shape)
print("Cashflow:", cashflow.shape)

# ======================================================
# Start with Profitability
# ======================================================

financial_ratios = profitability.copy()

# ======================================================
# Merge Leverage KPIs
# ======================================================

financial_ratios = financial_ratios.merge(

    leverage[
        [
            "company_id",
            "year",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "net_debt",
            "high_leverage_flag",
            "icr_label",
            "icr_warning"
        ]
    ],

    on=["company_id", "year"],

    how="left"

)

# ======================================================
# Merge CAGR KPIs
# ======================================================

financial_ratios = financial_ratios.merge(

    cagr[
        [
            "company_id",
            "revenue_cagr_5yr",
            "revenue_flag",
            "pat_cagr_5yr",
            "pat_flag",
            "eps_cagr_5yr",
            "eps_flag"
        ]
    ],

    on="company_id",

    how="left"

)

# ======================================================
# Merge Cash Flow KPIs
# ======================================================

financial_ratios = financial_ratios.merge(

    cashflow[
        [
            "company_id",
            "year",
            "free_cash_flow",
            "cfo_quality",
            "capex_pct",
            "capex_label",
            "fcf_conversion",
            "pattern_label"
        ]
    ],

    on=["company_id", "year"],

    how="left"

)

# ======================================================
# Save Combined CSV
# ======================================================

financial_ratios.to_csv(
    OUTPUT_DIR / "financial_ratios.csv",
    index=False
)

print("\nfinancial_ratios.csv saved successfully!")

# ======================================================
# Create SQLite Database
# ======================================================

connection = sqlite3.connect(
    DATABASE_DIR / "financial_data.db"
)

financial_ratios.to_sql(
    "financial_ratios",
    connection,
    if_exists="replace",
    index=False
)

print("\nfinancial_ratios table created!")

# ======================================================
# Verify Row Count
# ======================================================

rows = pd.read_sql(
    "SELECT COUNT(*) AS total_rows FROM financial_ratios",
    connection
)

print(rows)

# ======================================================
# Preview
# ======================================================

preview = pd.read_sql(
    "SELECT * FROM financial_ratios LIMIT 5",
    connection
)

print(preview)

connection.close()

print("\nDatabase Saved Successfully!")
print(DATABASE_DIR / "financial_data.db")