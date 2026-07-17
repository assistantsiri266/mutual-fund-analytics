import sqlite3
import pandas as pd
import yaml
from pathlib import Path

# ==========================================
# Project Paths
# ==========================================

BASE_DIR = Path(__file__).resolve().parents[3]

DATABASE = BASE_DIR / "database" / "financial_data.db"
CONFIG = BASE_DIR / "config" / "screener_config.yaml"
OUTPUT_DIR = BASE_DIR / "output"

print("BASE_DIR:", BASE_DIR)
print("DATABASE Exists:", DATABASE.exists())
print("CONFIG Exists:", CONFIG.exists())

# ==========================================
# Load Financial Ratios
# ==========================================

connection = sqlite3.connect(DATABASE)

financial_ratios = pd.read_sql(
    "SELECT * FROM financial_ratios",
    connection
)

connection.close()

print("\nFinancial Ratios")
print(financial_ratios.shape)

# ==========================================
# Load Composite Score
# ==========================================

composite = pd.read_csv(
    OUTPUT_DIR / "composite_scores.csv"
)

print("\nComposite Score")
print(composite.shape)

financial_ratios = financial_ratios.merge(

    composite[
        [
            "company_id",
            "year",
            "composite_score"
        ]
    ],

    on=["company_id", "year"],

    how="left"

)

# ==========================================
# Load YAML Config
# ==========================================

with open(CONFIG, "r") as file:
    config = yaml.safe_load(file)

print("\nConfig Loaded")

# ==========================================
# Generic Filter Function
# ==========================================

def apply_filters(df, filters):

    result = df.copy()

    if "roe" in filters:
        result = result[
            result["roe_calculated"] >= filters["roe"]
        ]

    if "debt_to_equity" in filters:
        result = result[
            result["debt_to_equity"] <= filters["debt_to_equity"]
        ]

    if "revenue_cagr_5yr" in filters:
        result = result[
            result["revenue_cagr_5yr"] >= filters["revenue_cagr_5yr"]
        ]

    if "pat_cagr_5yr" in filters:
        result = result[
            result["pat_cagr_5yr"] >= filters["pat_cagr_5yr"]
        ]

    if "free_cash_flow" in filters:
        result = result[
            result["free_cash_flow"] > filters["free_cash_flow"]
        ]

    return result

# ==========================================
# Create Preset Screeners
# ==========================================

quality = apply_filters(
    financial_ratios,
    config["quality_compounder"]
)

value_pick = apply_filters(
    financial_ratios,
    config["value_pick"]
)

growth = apply_filters(
    financial_ratios,
    config["growth_accelerator"]
)

dividend = apply_filters(
    financial_ratios,
    config["dividend_champion"]
)

debt_free = apply_filters(
    financial_ratios,
    config["debt_free_bluechip"]
)

turnaround = apply_filters(
    financial_ratios,
    config["turnaround_watch"]
)

# ==========================================
# Sort by Composite Score
# ==========================================

quality = quality.sort_values(
    by="composite_score",
    ascending=False
)

value_pick = value_pick.sort_values(
    by="composite_score",
    ascending=False
)

growth = growth.sort_values(
    by="composite_score",
    ascending=False
)

dividend = dividend.sort_values(
    by="composite_score",
    ascending=False
)

debt_free = debt_free.sort_values(
    by="composite_score",
    ascending=False
)

turnaround = turnaround.sort_values(
    by="composite_score",
    ascending=False
)

# ==========================================
# Display Results
# ==========================================

print("\nQuality Compounder:", quality.shape)
print("\nValue Pick:", value_pick.shape)
print("\nGrowth Accelerator:", growth.shape)
print("\nDividend Champion:", dividend.shape)
print("\nDebt Free Bluechip:", debt_free.shape)
print("\nTurnaround Watch:", turnaround.shape)

print("\nTop Quality Companies")

print(

quality[
    [
        "company_id",
        "composite_score"
    ]
].head(10)

)

# ==========================================
# Export Excel
# ==========================================

OUTPUT_DIR.mkdir(exist_ok=True)

output_file = OUTPUT_DIR / "screener_output.xlsx"

with pd.ExcelWriter(
    output_file,
    engine="openpyxl"
) as writer:

    quality.to_excel(
        writer,
        sheet_name="Quality Compounder",
        index=False
    )

    value_pick.to_excel(
        writer,
        sheet_name="Value Pick",
        index=False
    )

    growth.to_excel(
        writer,
        sheet_name="Growth Accelerator",
        index=False
    )

    dividend.to_excel(
        writer,
        sheet_name="Dividend Champion",
        index=False
    )

    debt_free.to_excel(
        writer,
        sheet_name="Debt Free Bluechip",
        index=False
    )

    turnaround.to_excel(
        writer,
        sheet_name="Turnaround Watch",
        index=False
    )

print("\n===================================")
print("Screener Output Generated")
print(output_file)
print("===================================")