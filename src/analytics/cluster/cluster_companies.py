import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parents[3]

DATABASE = BASE_DIR / "database" / "financial_data.db"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "cluster_labels.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print("=" * 70)
print("SPRINT 6 — COMPANY CLUSTERING")
print("=" * 70)


# ---------------------------------------------------------
# 1. Load financial ratios
# ---------------------------------------------------------

connection = sqlite3.connect(DATABASE)

df = pd.read_sql_query(
    "SELECT * FROM financial_ratios",
    connection
)

connection.close()


# ---------------------------------------------------------
# 2. Normalize company IDs and years
# ---------------------------------------------------------

df["company_id"] = (
    df["company_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["year"] = (
    df["year"]
    .astype(str)
    .str.strip()
)


df = df[
    (df["company_id"] != "")
    & (df["company_id"] != "NAN")
    & (df["year"] != "")
    & (df["year"] != "NAN")
].copy()


# ---------------------------------------------------------
# 3. Sort and select latest record per company
# ---------------------------------------------------------

df = df.sort_values(
    ["company_id", "year"]
)

latest = (
    df
    .drop_duplicates("company_id", keep="last")
    .copy()
)


print("Financial-ratio rows:", len(df))
print("Companies found:", latest["company_id"].nunique())


# ---------------------------------------------------------
# 4. Clustering features
# ---------------------------------------------------------

FEATURES = [
    "roe_calculated",
    "roce_calculated",
    "net_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "fcf_conversion",
]


missing = [
    column
    for column in FEATURES
    if column not in latest.columns
]

if missing:
    raise ValueError(
        f"Required clustering columns missing: {missing}"
    )


# ---------------------------------------------------------
# 5. Convert numeric columns
# ---------------------------------------------------------

for column in FEATURES:
    latest[column] = pd.to_numeric(
        latest[column],
        errors="coerce"
    )


# Replace infinite values
latest[FEATURES] = latest[FEATURES].replace(
    [np.inf, -np.inf],
    np.nan
)


# ---------------------------------------------------------
# 6. Fill missing values using feature medians
# ---------------------------------------------------------

for column in FEATURES:
    median = latest[column].median()

    if pd.isna(median):
        median = 0.0

    latest[column] = latest[column].fillna(median)


# ---------------------------------------------------------
# 7. Standardize features
# ---------------------------------------------------------

scaler = StandardScaler()

X = scaler.fit_transform(
    latest[FEATURES]
)


# ---------------------------------------------------------
# 8. K-Means clustering
# ---------------------------------------------------------

N_CLUSTERS = 4

model = KMeans(
    n_clusters=N_CLUSTERS,
    random_state=42,
    n_init=20
)

latest["cluster_id"] = model.fit_predict(X)


# ---------------------------------------------------------
# 9. Create human-readable cluster labels
# ---------------------------------------------------------

cluster_means = (
    latest
    .groupby("cluster_id")[FEATURES]
    .mean()
)


# Overall standardized cluster score.
# Higher = generally stronger financial characteristics.

cluster_scores = (
    pd.DataFrame(
        scaler.transform(
            cluster_means[FEATURES]
        ),
        index=cluster_means.index,
        columns=FEATURES,
    )
    .mean(axis=1)
)


ordered_clusters = (
    cluster_scores
    .sort_values()
    .index
    .tolist()
)


cluster_names = {}

names = [
    "Lower Financial Quality",
    "Stable / Moderate",
    "Growth & Quality",
    "Strong Financial Profile",
]

for cluster_id, name in zip(
    ordered_clusters,
    names
):
    cluster_names[cluster_id] = name


latest["cluster_label"] = (
    latest["cluster_id"]
    .map(cluster_names)
)


# ---------------------------------------------------------
# 10. Prepare output
# ---------------------------------------------------------

output_columns = [
    "company_id",
    "cluster_id",
    "cluster_label",
]

output = latest[output_columns].copy()

output = output.sort_values(
    "company_id"
)


# ---------------------------------------------------------
# 11. Save
# ---------------------------------------------------------

output.to_csv(
    OUTPUT_FILE,
    index=False
)


# ---------------------------------------------------------
# 12. Validation
# ---------------------------------------------------------

print()
print("=== CLUSTERING RESULTS ===")

print(
    "Output rows:",
    len(output)
)

print(
    "Unique companies:",
    output["company_id"].nunique()
)

print(
    "Missing cluster labels:",
    output["cluster_label"].isna().sum()
)

print()
print("Cluster distribution:")

print(
    output["cluster_label"]
    .value_counts()
    .sort_index()
)


print()
print("Output:")
print(OUTPUT_FILE)

print()
print("=== D-19 COMPLETE ===")