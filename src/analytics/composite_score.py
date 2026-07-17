import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE = BASE_DIR / "database" / "financial_data.db"

connection = sqlite3.connect(DATABASE)

df = pd.read_sql(
    "SELECT * FROM financial_ratios",
    connection
)

connection.close()

print(df.shape)
print(df.columns.tolist())

def normalize(series):

    minimum = series.min()
    maximum = series.max()

    if maximum == minimum:
        return pd.Series(50, index=series.index)

    return (
        (series - minimum)
        / (maximum - minimum)
    ) * 100

df["roe_score"] = normalize(df["roe_calculated"])

df["roce_score"] = normalize(df["roce_calculated"])

df["npm_score"] = normalize(df["net_profit_margin_pct"])

df["fcf_score"] = normalize(df["free_cash_flow"])

df["revenue_score"] = normalize(df["revenue_cagr_5yr"])

df["pat_score"] = normalize(df["pat_cagr_5yr"])

df["de_score"] = 100 - normalize(df["debt_to_equity"])

df["icr_score"] = normalize(
    df["interest_coverage"].fillna(0)
)

df["composite_score"] = (

    df["roe_score"] * 0.15 +

    df["roce_score"] * 0.10 +

    df["npm_score"] * 0.10 +

    df["fcf_score"] * 0.15 +

    df["revenue_score"] * 0.10 +

    df["pat_score"] * 0.10 +

    df["de_score"] * 0.10 +

    df["icr_score"] * 0.05

)

df = df.sort_values(
    "composite_score",
    ascending=False
)

print(
    df[
        [
            "company_id",
            "composite_score"
        ]
    ].head(20)
)

OUTPUT = BASE_DIR / "output"

df.to_csv(
    OUTPUT / "composite_scores.csv",
    index=False
)

print("Composite Score Saved Successfully!")