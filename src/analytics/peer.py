import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# ============================================================
# DAY 33 — PEER ANALYSIS
# STEP 33.2 — PEER PERCENTILE ANALYSIS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE = BASE_DIR / "database" / "financial_data.db"
OUTPUT_DIR = BASE_DIR / "output"
PEER_CSV = OUTPUT_DIR / "peer_percentiles.csv"

print("=" * 80)
print("DAY 33 — PEER ANALYSIS")
print("=" * 80)

print("\nDatabase:")
print(DATABASE)

if not DATABASE.exists():
    raise FileNotFoundError(f"Database not found: {DATABASE}")

# ============================================================
# 1. LOAD FINANCIAL RATIOS
# ============================================================

connection = sqlite3.connect(DATABASE)

df = pd.read_sql_query(
    "SELECT * FROM financial_ratios",
    connection
)

connection.close()

print("\nFinancial ratios shape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

if df.empty:
    raise ValueError("financial_ratios table is empty.")

# ============================================================
# 2. NORMALIZE COMPANY ID
# ============================================================

df["company_id"] = (
    df["company_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

# ============================================================
# 3. NORMALIZE YEAR
# ============================================================

df["year"] = (
    df["year"]
    .astype(str)
    .str.strip()
)

# Remove invalid company/year records
df = df[
    (df["company_id"] != "")
    & (df["company_id"] != "NAN")
    & (df["company_id"] != "NONE")
    & (df["year"] != "")
    & (df["year"] != "NAN")
    & (df["year"] != "NONE")
].copy()

# ============================================================
# 4. REMOVE DUPLICATE COMPANY-YEAR RECORDS
# ============================================================

before = len(df)

df = (
    df
    .sort_values(
        ["company_id", "year"]
    )
    .drop_duplicates(
        subset=["company_id", "year"],
        keep="last"
    )
    .reset_index(drop=True)
)

after = len(df)

print("\nDuplicate company-year rows removed:")
print(before - after)

print("\nClean financial-ratio dataset:")
print("Rows:", len(df))
print("Companies:", df["company_id"].nunique())
print("Years:", sorted(df["year"].unique()))

# ============================================================
# 5. CREATE DETERMINISTIC PEER GROUPS
# ============================================================

companies = sorted(
    df["company_id"].unique()
)

print("\nCompanies:", len(companies))

group_names = [
    "Group A",
    "Group B",
    "Group C",
    "Group D",
    "Group E"
]

# Divide companies as evenly as possible
groups = np.array_split(
    companies,
    len(group_names)
)

peer_groups = {}

for group_name, members in zip(
    group_names,
    groups
):
    peer_groups[group_name] = set(members)

df["peer_group"] = "Unassigned"

for group_name, members in peer_groups.items():

    df.loc[
        df["company_id"].isin(members),
        "peer_group"
    ] = group_name

# ============================================================
# 6. VALIDATE PEER GROUP ASSIGNMENT
# ============================================================

unassigned = (
    df.loc[
        df["peer_group"] == "Unassigned",
        "company_id"
    ]
    .nunique()
)

if unassigned > 0:
    raise ValueError(
        f"{unassigned} companies remain unassigned to peer groups."
    )

print("\nPeer-group distribution:")

print(
    df[
        ["company_id", "peer_group"]
    ]
    .drop_duplicates()
    ["peer_group"]
    .value_counts()
    .sort_index()
)

# ============================================================
# 7. DEFINE PEER METRICS
# ============================================================

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

available_metrics = [
    metric
    for metric in metrics
    if metric in df.columns
]

missing_metrics = [
    metric
    for metric in metrics
    if metric not in df.columns
]

print("\nAvailable metrics:")
print(available_metrics)

if missing_metrics:
    print("\nMissing metrics:")
    print(missing_metrics)

if not available_metrics:
    raise ValueError(
        "None of the required peer metrics exist in financial_ratios."
    )

# ============================================================
# 8. CALCULATE PEER PERCENTILES
# ============================================================

records = []

for group_name in group_names:

    group_df = df[
        df["peer_group"] == group_name
    ].copy()

    if group_df.empty:
        continue

    for metric in available_metrics:

        values = pd.to_numeric(
            group_df[metric],
            errors="coerce"
        )

        # Percentile rank within the peer group
        ranks = values.rank(
            method="average",
            pct=True
        )

        # For debt-to-equity:
        # LOWER debt is considered better.
        if metric == "debt_to_equity":
            ranks = 1 - ranks

        temp = group_df[
            ["company_id", "year"]
        ].copy()

        temp["peer_group"] = group_name
        temp["metric"] = metric
        temp["value"] = values
        temp["percentile_rank"] = ranks

        records.append(temp)

# ============================================================
# 9. COMBINE RESULTS
# ============================================================

if not records:
    raise ValueError(
        "No peer percentile records were generated."
    )

peer_percentiles = pd.concat(
    records,
    ignore_index=True
)

# ============================================================
# 10. FINAL CLEANUP
# ============================================================

peer_percentiles["company_id"] = (
    peer_percentiles["company_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

peer_percentiles["year"] = (
    peer_percentiles["year"]
    .astype(str)
    .str.strip()
)

peer_percentiles["metric"] = (
    peer_percentiles["metric"]
    .astype(str)
    .str.strip()
)

peer_percentiles["peer_group"] = (
    peer_percentiles["peer_group"]
    .astype(str)
    .str.strip()
)

peer_percentiles["value"] = pd.to_numeric(
    peer_percentiles["value"],
    errors="coerce"
)

peer_percentiles["percentile_rank"] = pd.to_numeric(
    peer_percentiles["percentile_rank"],
    errors="coerce"
)

# Remove accidental duplicates
peer_percentiles = (
    peer_percentiles
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

# ============================================================
# 11. VALIDATION
# ============================================================

duplicate_count = peer_percentiles.duplicated(
    [
        "company_id",
        "year",
        "metric"
    ]
).sum()

missing_company = (
    peer_percentiles["company_id"]
    .isna()
    .sum()
)

missing_year = (
    peer_percentiles["year"]
    .isna()
    .sum()
)

missing_metric = (
    peer_percentiles["metric"]
    .isna()
    .sum()
)

print("\n" + "=" * 80)
print("PEER PERCENTILE VALIDATION")
print("=" * 80)

print("Rows:", len(peer_percentiles))
print(
    "Companies:",
    peer_percentiles["company_id"].nunique()
)
print(
    "Years:",
    sorted(peer_percentiles["year"].unique())
)
print(
    "Metrics:",
    peer_percentiles["metric"].nunique()
)
print("Duplicates:", duplicate_count)

print("\nMissing values:")
print("Company ID:", missing_company)
print("Year:", missing_year)
print("Metric:", missing_metric)

print("\nMetric distribution:")
print(
    peer_percentiles["metric"]
    .value_counts()
    .sort_index()
)

print("\nPeer-group distribution:")
print(
    peer_percentiles["peer_group"]
    .value_counts()
    .sort_index()
)

# Validate percentile range
invalid_percentiles = peer_percentiles[
    (
        peer_percentiles["percentile_rank"].notna()
    )
    &
    (
        (peer_percentiles["percentile_rank"] < 0)
        |
        (peer_percentiles["percentile_rank"] > 1)
    )
]

print(
    "\nInvalid percentile values:",
    len(invalid_percentiles)
)

if duplicate_count != 0:
    raise ValueError(
        f"Duplicate company-year-metric rows remain: "
        f"{duplicate_count}"
    )

if len(invalid_percentiles) != 0:
    raise ValueError(
        "Invalid percentile_rank values detected."
    )

# ============================================================
# 12. SAVE CSV
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

peer_percentiles.to_csv(
    PEER_CSV,
    index=False
)

print("\nPeer percentile CSV saved:")
print(PEER_CSV)

# ============================================================
# 13. SAVE SQLITE TABLE
# ============================================================

connection = sqlite3.connect(DATABASE)

peer_percentiles.to_sql(
    "peer_percentiles",
    connection,
    if_exists="replace",
    index=False
)

connection.close()

print("\nSQLite table created:")
print("peer_percentiles")

# ============================================================
# 14. FINAL STATUS
# ============================================================

print("\n" + "=" * 80)
print("DAY 33 STEP 33.2 COMPLETE")
print("=" * 80)

print("PASS: Peer percentile dataset generated.")
print("PASS: Company IDs normalized.")
print("PASS: Company-year duplicates removed.")
print("PASS: Company-year-metric duplicates checked.")
print("PASS: Percentile values validated.")
print("PASS: CSV saved.")
print("PASS: SQLite table updated.")

print("\nOutput:")
print(PEER_CSV)

print("\nDONE.")