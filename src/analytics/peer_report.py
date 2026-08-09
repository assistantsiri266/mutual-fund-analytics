import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# DAY 33 — PEER COMPARISON REPORT
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE = BASE_DIR / "database" / "financial_data.db"
OUTPUT_DIR = BASE_DIR / "output"

INPUT_CSV = OUTPUT_DIR / "peer_percentiles.csv"
OUTPUT_XLSX = OUTPUT_DIR / "peer_comparison.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "peer_comparison_summary.csv"

print("=" * 80)
print("DAY 33 — PEER COMPARISON REPORT")
print("=" * 80)

# ============================================================
# 1. CHECK INPUT
# ============================================================

print("\nInput:")
print(INPUT_CSV)

if not INPUT_CSV.exists():
    raise FileNotFoundError(
        f"Peer percentile file not found: {INPUT_CSV}"
    )

# ============================================================
# 2. LOAD PEER PERCENTILES
# ============================================================

df = pd.read_csv(INPUT_CSV)

print("\nInput shape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

required_columns = [
    "company_id",
    "year",
    "peer_group",
    "metric",
    "value",
    "percentile_rank"
]

missing_columns = [
    c for c in required_columns
    if c not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

# ============================================================
# 3. NORMALIZE DATA
# ============================================================

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

df["peer_group"] = (
    df["peer_group"]
    .astype(str)
    .str.strip()
)

df["metric"] = (
    df["metric"]
    .astype(str)
    .str.strip()
)

df["value"] = pd.to_numeric(
    df["value"],
    errors="coerce"
)

df["percentile_rank"] = pd.to_numeric(
    df["percentile_rank"],
    errors="coerce"
)

# Convert percentile from 0–1 to 0–100
df["percentile_score"] = (
    df["percentile_rank"] * 100
)

# ============================================================
# 4. REMOVE DUPLICATES
# ============================================================

before = len(df)

df = (
    df
    .drop_duplicates(
        subset=[
            "company_id",
            "year",
            "metric"
        ],
        keep="last"
    )
    .reset_index(drop=True)
)

print("\nDuplicate rows removed:")
print(before - len(df))

# ============================================================
# 5. VALIDATE
# ============================================================

duplicate_count = df.duplicated(
    [
        "company_id",
        "year",
        "metric"
    ]
).sum()

print("\nFINAL INPUT")
print("Rows:", len(df))
print(
    "Companies:",
    df["company_id"].nunique()
)
print(
    "Peer groups:",
    df["peer_group"].nunique()
)
print(
    "Metrics:",
    df["metric"].nunique()
)
print("Duplicates:", duplicate_count)

if duplicate_count != 0:
    raise ValueError(
        "Duplicate company-year-metric records remain."
    )

# ============================================================
# 6. COMPANY-LEVEL PEER SCORE
# ============================================================

print("\nCalculating company peer scores...")

company_metric = (
    df
    .groupby(
        [
            "company_id",
            "peer_group",
            "metric"
        ],
        as_index=False
    )
    .agg(
        average_percentile=(
            "percentile_score",
            "mean"
        ),
        latest_percentile=(
            "percentile_score",
            "last"
        ),
        average_value=(
            "value",
            "mean"
        )
    )
)

# ============================================================
# 7. WIDE PEER SCORE TABLE
# ============================================================

wide = (
    company_metric
    .pivot_table(
        index=[
            "company_id",
            "peer_group"
        ],
        columns="metric",
        values="average_percentile",
        aggfunc="mean"
    )
    .reset_index()
)

wide.columns.name = None

# ============================================================
# 8. OVERALL PEER SCORE
# ============================================================

metric_columns = [
    c for c in wide.columns
    if c not in [
        "company_id",
        "peer_group"
    ]
]

wide["overall_peer_score"] = (
    wide[metric_columns]
    .mean(
        axis=1,
        skipna=True
    )
)

# ============================================================
# 9. PEER RANK
# ============================================================

wide["peer_rank"] = (
    wide["overall_peer_score"]
    .rank(
        ascending=False,
        method="min"
    )
    .astype(int)
)

wide["peer_percentile"] = (
    wide["overall_peer_score"]
    .rank(
        pct=True
    ) * 100
)

# ============================================================
# 10. PEER CATEGORY
# ============================================================

def classify_peer(score):

    if pd.isna(score):
        return "Insufficient Data"

    if score >= 80:
        return "Top Peer"

    if score >= 60:
        return "Strong Peer"

    if score >= 40:
        return "Average Peer"

    if score >= 20:
        return "Weak Peer"

    return "Bottom Peer"


wide["peer_category"] = (
    wide["overall_peer_score"]
    .apply(classify_peer)
)

# ============================================================
# 11. BEST METRIC / WEAKEST METRIC
# ============================================================

def best_metric(row):

    values = row[metric_columns]

    if values.dropna().empty:
        return "N/A"

    return values.idxmax()


def weakest_metric(row):

    values = row[metric_columns]

    if values.dropna().empty:
        return "N/A"

    return values.idxmin()


wide["best_peer_metric"] = (
    wide.apply(
        best_metric,
        axis=1
    )
)

wide["weakest_peer_metric"] = (
    wide.apply(
        weakest_metric,
        axis=1
    )
)

# ============================================================
# 12. RANK COLUMNS
# ============================================================

wide = wide.sort_values(
    "peer_rank"
).reset_index(drop=True)

# ============================================================
# 13. METRIC SUMMARY
# ============================================================

metric_summary = (
    df
    .groupby("metric", as_index=False)
    .agg(
        observations=("percentile_score", "count"),
        average_percentile=("percentile_score", "mean"),
        median_percentile=("percentile_score", "median"),
        minimum_percentile=("percentile_score", "min"),
        maximum_percentile=("percentile_score", "max")
    )
)

metric_summary = metric_summary.sort_values(
    "average_percentile",
    ascending=False
)

# ============================================================
# 14. PEER GROUP SUMMARY
# ============================================================

group_summary = (
    wide
    .groupby("peer_group", as_index=False)
    .agg(
        companies=("company_id", "nunique"),
        average_peer_score=(
            "overall_peer_score",
            "mean"
        ),
        median_peer_score=(
            "overall_peer_score",
            "median"
        ),
        top_peer_score=(
            "overall_peer_score",
            "max"
        ),
        lowest_peer_score=(
            "overall_peer_score",
            "min"
        )
    )
)

group_summary = group_summary.sort_values(
    "average_peer_score",
    ascending=False
)

# ============================================================
# 15. TOP 20 PEERS
# ============================================================

top_20 = (
    wide
    .sort_values(
        "overall_peer_score",
        ascending=False
    )
    .head(20)
    .copy()
)

top_20.insert(
    0,
    "rank",
    range(
        1,
        len(top_20) + 1
    )
)

# ============================================================
# 16. BOTTOM 20 PEERS
# ============================================================

bottom_20 = (
    wide
    .sort_values(
        "overall_peer_score",
        ascending=True
    )
    .head(20)
    .copy()
)

bottom_20.insert(
    0,
    "rank",
    range(
        1,
        len(bottom_20) + 1
    )
)

# ============================================================
# 17. STRONG PEERS
# ============================================================

strong_peers = wide[
    wide["overall_peer_score"] >= 60
].copy()

strong_peers = strong_peers.sort_values(
    "overall_peer_score",
    ascending=False
)

# ============================================================
# 18. WEAK PEERS
# ============================================================

weak_peers = wide[
    wide["overall_peer_score"] < 40
].copy()

weak_peers = weak_peers.sort_values(
    "overall_peer_score",
    ascending=True
)

# ============================================================
# 19. SAVE EXCEL REPORT
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

print("\nSaving Excel report...")

with pd.ExcelWriter(
    OUTPUT_XLSX,
    engine="openpyxl"
) as writer:

    wide.to_excel(
        writer,
        sheet_name="company_peer_scores",
        index=False
    )

    top_20.to_excel(
        writer,
        sheet_name="top_20_peers",
        index=False
    )

    bottom_20.to_excel(
        writer,
        sheet_name="bottom_20_peers",
        index=False
    )

    strong_peers.to_excel(
        writer,
        sheet_name="strong_peers",
        index=False
    )

    weak_peers.to_excel(
        writer,
        sheet_name="weak_peers",
        index=False
    )

    metric_summary.to_excel(
        writer,
        sheet_name="metric_summary",
        index=False
    )

    group_summary.to_excel(
        writer,
        sheet_name="peer_group_summary",
        index=False
    )

    df.to_excel(
        writer,
        sheet_name="peer_percentiles",
        index=False
    )

print("\nExcel report saved:")
print(OUTPUT_XLSX)

# ============================================================
# 20. SAVE CSV SUMMARY
# ============================================================

wide.to_csv(
    OUTPUT_CSV,
    index=False
)

print("\nCSV summary saved:")
print(OUTPUT_CSV)

# ============================================================
# 21. SAVE SQLITE TABLES
# ============================================================

connection = sqlite3.connect(DATABASE)

wide.to_sql(
    "peer_company_scores",
    connection,
    if_exists="replace",
    index=False
)

metric_summary.to_sql(
    "peer_metric_summary",
    connection,
    if_exists="replace",
    index=False
)

group_summary.to_sql(
    "peer_group_summary",
    connection,
    if_exists="replace",
    index=False
)

connection.close()

print("\nSQLite tables created:")
print("peer_company_scores")
print("peer_metric_summary")
print("peer_group_summary")

# ============================================================
# 22. FINAL VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("DAY 33 PEER COMPARISON VALIDATION")
print("=" * 80)

print("Peer percentile rows:", len(df))
print(
    "Peer percentile companies:",
    df["company_id"].nunique()
)

print(
    "Company peer-score rows:",
    len(wide)
)

print(
    "Company peer-score companies:",
    wide["company_id"].nunique()
)

print(
    "Top 20 rows:",
    len(top_20)
)

print(
    "Bottom 20 rows:",
    len(bottom_20)
)

print(
    "Strong peers:",
    len(strong_peers)
)

print(
    "Weak peers:",
    len(weak_peers)
)

print(
    "Duplicate company peer-score rows:",
    wide.duplicated(
        ["company_id"]
    ).sum()
)

print("\nPeer category distribution:")
print(
    wide["peer_category"]
    .value_counts()
)

print("\nTOP 10 PEERS:")
print(
    top_20[
        [
            "rank",
            "company_id",
            "peer_group",
            "overall_peer_score",
            "peer_category"
        ]
    ]
    .head(10)
    .to_string(index=False)
)

# ============================================================
# 23. FINAL STATUS
# ============================================================

if (
    wide["company_id"].nunique()
    == df["company_id"].nunique()
    and
    wide.duplicated(["company_id"]).sum()
    == 0
    and
    len(top_20) > 0
):

    print("\n" + "=" * 80)
    print("DAY 33 STEP 33.3 COMPLETE")
    print("=" * 80)

    print("PASS: Peer comparison generated.")
    print("PASS: Company-level peer scores generated.")
    print("PASS: Peer ranking generated.")
    print("PASS: Top and bottom peer lists generated.")
    print("PASS: Excel report saved.")
    print("PASS: CSV summary saved.")
    print("PASS: SQLite tables updated.")

else:

    raise ValueError(
        "Peer comparison validation failed."
    )

print("\nDONE.")