import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE = BASE_DIR / "database" / "financial_data.db"

OUTPUT = BASE_DIR / "output"

connection = sqlite3.connect(DATABASE)

df = pd.read_sql(
    "SELECT * FROM financial_ratios",
    connection
)

connection.close()

print(df.shape)
print(df.columns.tolist())


peer_groups = {

    "Group A": df["company_id"].unique()[:20],

    "Group B": df["company_id"].unique()[20:40],

    "Group C": df["company_id"].unique()[40:60],

    "Group D": df["company_id"].unique()[60:80],

    "Group E": df["company_id"].unique()[80:]

}

df["peer_group"] = "Unassigned"

for group, companies in peer_groups.items():

    df.loc[
        df["company_id"].isin(companies),
        "peer_group"
    ] = group

print(df[["company_id", "peer_group"]].head())


metrics = [

    "roe_calculated",

    "roce_calculated",

    "net_profit_margin_pct",

    "debt_to_equity",

    "free_cash_flow",

    "pat_cagr_5yr",

    "revenue_cagr_5yr",

    "eps_cagr_5yr",

    "interest_coverage",

    "asset_turnover"

]

records = []

for group in df["peer_group"].unique():

    group_df = df[df["peer_group"] == group]

    for metric in metrics:

        if metric not in group_df.columns:
            continue

        ranks = group_df[metric].rank(pct=True)

        if metric == "debt_to_equity":
            ranks = 1 - ranks

        temp = group_df[
            [
                "company_id",
                "year"
            ]
        ].copy()

        temp["peer_group"] = group

        temp["metric"] = metric

        temp["value"] = group_df[metric]

        temp["percentile_rank"] = ranks

        records.append(temp)


peer_percentiles = pd.concat(
    records,
    ignore_index=True
)

print(peer_percentiles.head())

print(peer_percentiles.shape)

OUTPUT.mkdir(exist_ok=True)

peer_percentiles.to_csv(

    OUTPUT / "peer_percentiles.csv",

    index=False

)

print("CSV Saved!")

connection = sqlite3.connect(DATABASE)

peer_percentiles.to_sql(

    "peer_percentiles",

    connection,

    if_exists="replace",

    index=False

)

connection.close()

print("SQLite Table Created!")