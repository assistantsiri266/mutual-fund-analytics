import pandas as pd
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "output"

DB_DIR = BASE_DIR / "data" / "db"
DB_DIR.mkdir(exist_ok=True)

DATABASE = DB_DIR / "financial_data.db"

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

print(profitability.shape)
print(leverage.shape)
print(cagr.shape)
print(cashflow.shape)

financial_ratios = pd.merge(

    profitability,

    leverage[[
        "company_id",
        "year",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "net_debt"
    ]],

    on=["company_id","year"]

)

financial_ratios = pd.merge(

    financial_ratios,

    cagr,

    on="company_id",

    how="left"

)

financial_ratios = pd.merge(

    financial_ratios,

    cashflow[[
        "company_id",
        "year",
        "free_cash_flow",
        "cfo_quality",
        "fcf_conversion"
    ]],

    on=["company_id","year"],

    how="left"

)

print(financial_ratios.head())

print(financial_ratios.shape)

connection = sqlite3.connect(DATABASE)

cursor = connection.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS financial_ratios(

company_id TEXT,

year INTEGER,

net_profit_margin_pct REAL,

operating_profit_margin_pct REAL,

roe_calculated REAL,

roce_calculated REAL,

roa_calculated REAL,

debt_to_equity REAL,

interest_coverage REAL,

asset_turnover REAL,

net_debt REAL,

free_cash_flow REAL,

cfo_quality TEXT,

fcf_conversion REAL,

revenue_cagr_5yr REAL,

pat_cagr_5yr REAL,

eps_cagr_5yr REAL

)

""")

financial_ratios.to_sql(

    "financial_ratios",

    connection,

    if_exists="replace",

    index=False

)

rows = pd.read_sql(

    "SELECT COUNT(*) AS total FROM financial_ratios",

    connection

)

print(rows)

sample = pd.read_sql("""

SELECT

company_id,

year,

roe_calculated,

revenue_cagr_5yr

FROM financial_ratios

LIMIT 10

""", connection)

print(sample)

connection.commit()

connection.close()

print("Financial Ratios table created successfully!")

