import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE = BASE_DIR / "database" / "financial_data.db"

REPORT_DIR = BASE_DIR / "reports" / "radar_charts"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

connection = sqlite3.connect(DATABASE)

financial = pd.read_sql(
    "SELECT * FROM financial_ratios",
    connection
)

peer = pd.read_sql(
    "SELECT * FROM peer_percentiles",
    connection
)

connection.close()

print(financial.shape)
print(peer.shape)

metrics = [

    "roe_calculated",

    "roce_calculated",

    "net_profit_margin_pct",

    "debt_to_equity",

    "free_cash_flow",

    "pat_cagr_5yr",

    "revenue_cagr_5yr",

    "asset_turnover"

]

latest = financial.groupby("company_id").tail(1)

print(latest.shape)

for metric in metrics:

    minimum = latest[metric].min()

    maximum = latest[metric].max()

    latest[metric] = (

        latest[metric] - minimum

    ) / (

        maximum - minimum

    )

for _, row in latest.iterrows():

    values = row[metrics].tolist()

    values += values[:1]

    angles = np.linspace(

        0,

        2 * np.pi,

        len(metrics),

        endpoint=False

    ).tolist()

    angles += angles[:1]

    fig = plt.figure(figsize=(6,6))

    ax = plt.subplot(111, polar=True)

    ax.plot(
        angles,
        values,
        linewidth=2
    )

    ax.fill(
        angles,
        values,
        alpha=0.25
    )

    ax.set_xticks(angles[:-1])

    ax.set_xticklabels(metrics)

    plt.title(row["company_id"])

    plt.savefig(

        REPORT_DIR /

        f"{row['company_id']}_radar.png"

    )

    plt.close()