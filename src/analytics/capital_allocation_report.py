"""
DAY 32 — CAPITAL ALLOCATION REPORT

Creates summary reports from:
output/capital_allocation.csv
"""

from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "output" / "capital_allocation.csv"
OUTPUT_DIR = BASE_DIR / "output" / "capital_allocation"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HEADER
# ============================================================

print("=" * 80)
print("DAY 32 — CAPITAL ALLOCATION REPORT")
print("=" * 80)

print(f"\nInput file:")
print(INPUT_FILE)

print(f"\nInput exists: {INPUT_FILE.exists()}")

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Capital allocation history not found:\n{INPUT_FILE}"
    )


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("\nInput shape:", df.shape)
print("Columns:", df.columns.tolist())


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "company_id",
    "year",
    "cfo_sign",
    "cfi_sign",
    "cff_sign",
    "capital_allocation_label",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

print("\nRequired columns: PASSED")


# ============================================================
# BASIC CLEANING
# ============================================================

df["company_id"] = (
    df["company_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["year"] = pd.to_numeric(
    df["year"],
    errors="coerce"
)

df = df.dropna(
    subset=["company_id", "year"]
)

df["year"] = df["year"].astype(int)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

before = len(df)

df = df.drop_duplicates(
    subset=["company_id", "year"],
    keep="last"
)

after = len(df)

print("\nDuplicate company-year rows removed:", before - after)


# ============================================================
# BASIC VALIDATION
# ============================================================

print("\nFINAL INPUT DATA")
print("Rows:", len(df))
print("Companies:", df["company_id"].nunique())
print("Years:", sorted(df["year"].unique()))
print(
    "Duplicate company-year:",
    df.duplicated(["company_id", "year"]).sum()
)


# ============================================================
# 1. OVERALL PATTERN COUNTS
# ============================================================

pattern_counts = (
    df["capital_allocation_label"]
    .value_counts()
    .rename_axis("capital_allocation_label")
    .reset_index(name="count")
)

pattern_counts["percentage"] = (
    pattern_counts["count"]
    / pattern_counts["count"].sum()
    * 100
)

pattern_counts["percentage"] = pattern_counts[
    "percentage"
].round(2)

print("\n" + "=" * 80)
print("1. OVERALL CAPITAL ALLOCATION PATTERNS")
print("=" * 80)

print(pattern_counts.to_string(index=False))


# ============================================================
# 2. YEAR-WISE PATTERN COUNTS
# ============================================================

year_pattern = (
    df.groupby(
        ["year", "capital_allocation_label"]
    )
    .size()
    .reset_index(name="count")
    .sort_values(
        ["year", "count"],
        ascending=[True, False]
    )
)

print("\n" + "=" * 80)
print("2. YEAR-WISE CAPITAL ALLOCATION PATTERNS")
print("=" * 80)

print(year_pattern.head(30).to_string(index=False))


# ============================================================
# 3. COMPANY-WISE HISTORY
# ============================================================

company_history = (
    df.sort_values(
        ["company_id", "year"]
    )
    .copy()
)

print("\n" + "=" * 80)
print("3. COMPANY-WISE HISTORY")
print("=" * 80)

print(
    company_history.head(20).to_string(index=False)
)


# ============================================================
# 4. COMPANY PATTERN SUMMARY
# ============================================================

company_pattern_summary = (
    pd.crosstab(
        df["company_id"],
        df["capital_allocation_label"]
    )
    .reset_index()
)

print("\n" + "=" * 80)
print("4. COMPANY PATTERN SUMMARY")
print("=" * 80)

print(
    company_pattern_summary.head(20).to_string(
        index=False
    )
)


# ============================================================
# 5. DOMINANT PATTERN BY COMPANY
# ============================================================

dominant_pattern = (
    df.groupby("company_id")[
        "capital_allocation_label"
    ]
    .agg(
        lambda x: x.value_counts().index[0]
    )
    .reset_index()
)

dominant_pattern.columns = [
    "company_id",
    "dominant_capital_allocation"
]

print("\n" + "=" * 80)
print("5. DOMINANT CAPITAL ALLOCATION BY COMPANY")
print("=" * 80)

print(
    dominant_pattern.head(20).to_string(
        index=False
    )
)


# ============================================================
# 6. REINVESTOR ANALYSIS
# ============================================================

reinvestor_summary = (
    df.assign(
        is_reinvestor=(
            df["capital_allocation_label"]
            == "Reinvestor"
        )
    )
    .groupby("company_id")["is_reinvestor"]
    .agg(
        reinvestor_years="sum",
        total_years="count",
    )
    .reset_index()
)

reinvestor_summary["reinvestor_pct"] = (
    reinvestor_summary["reinvestor_years"]
    / reinvestor_summary["total_years"]
    * 100
).round(2)

print("\n" + "=" * 80)
print("6. REINVESTOR ANALYSIS")
print("=" * 80)

print(
    reinvestor_summary
    .sort_values(
        "reinvestor_pct",
        ascending=False
    )
    .head(20)
    .to_string(index=False)
)


# ============================================================
# 7. DISTRESS SIGNAL ANALYSIS
# ============================================================

distress_summary = (
    df.assign(
        distress_signal=(
            df["capital_allocation_label"]
            == "Distress Signal"
        )
    )
    .groupby("company_id")["distress_signal"]
    .agg(
        distress_years="sum",
        total_years="count",
    )
    .reset_index()
)

distress_summary["distress_pct"] = (
    distress_summary["distress_years"]
    / distress_summary["total_years"]
    * 100
).round(2)

distress_summary = distress_summary[
    distress_summary["distress_years"] > 0
].sort_values(
    "distress_years",
    ascending=False
)

print("\n" + "=" * 80)
print("7. DISTRESS SIGNAL COMPANIES")
print("=" * 80)

print(
    distress_summary.to_string(index=False)
)


# ============================================================
# 8. YEARLY DOMINANT PATTERN
# ============================================================

yearly_dominant = (
    df.groupby("year")[
        "capital_allocation_label"
    ]
    .agg(
        lambda x: x.value_counts().index[0]
    )
    .reset_index()
)

yearly_dominant.columns = [
    "year",
    "dominant_capital_allocation",
]

print("\n" + "=" * 80)
print("8. YEARLY DOMINANT PATTERN")
print("=" * 80)

print(
    yearly_dominant.to_string(index=False)
)


# ============================================================
# 9. SAVE REPORT FILES
# ============================================================

pattern_counts.to_csv(
    OUTPUT_DIR / "pattern_summary.csv",
    index=False
)

year_pattern.to_csv(
    OUTPUT_DIR / "year_pattern_summary.csv",
    index=False
)

company_pattern_summary.to_csv(
    OUTPUT_DIR / "company_pattern_summary.csv",
    index=False
)

dominant_pattern.to_csv(
    OUTPUT_DIR / "dominant_pattern_by_company.csv",
    index=False
)

reinvestor_summary.to_csv(
    OUTPUT_DIR / "reinvestor_summary.csv",
    index=False
)

distress_summary.to_csv(
    OUTPUT_DIR / "distress_pattern_summary.csv",
    index=False
)

yearly_dominant.to_csv(
    OUTPUT_DIR / "yearly_dominant_pattern.csv",
    index=False
)


# ============================================================
# 10. EXCEL REPORT
# ============================================================

excel_output = (
    OUTPUT_DIR / "capital_allocation_report.xlsx"
)

with pd.ExcelWriter(
    excel_output,
    engine="openpyxl"
) as writer:

    df.to_excel(
        writer,
        sheet_name="history",
        index=False
    )

    pattern_counts.to_excel(
        writer,
        sheet_name="pattern_summary",
        index=False
    )

    year_pattern.to_excel(
        writer,
        sheet_name="year_pattern",
        index=False
    )

    company_pattern_summary.to_excel(
        writer,
        sheet_name="company_summary",
        index=False
    )

    dominant_pattern.to_excel(
        writer,
        sheet_name="dominant_pattern",
        index=False
    )

    reinvestor_summary.to_excel(
        writer,
        sheet_name="reinvestor_analysis",
        index=False
    )

    distress_summary.to_excel(
        writer,
        sheet_name="distress_analysis",
        index=False
    )

    yearly_dominant.to_excel(
        writer,
        sheet_name="yearly_dominant",
        index=False
    )


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("FINAL VALIDATION")
print("=" * 80)

print("History rows:", len(df))
print("Companies:", df["company_id"].nunique())
print("Years:", sorted(df["year"].unique()))
print(
    "Duplicate company-year:",
    df.duplicated(
        ["company_id", "year"]
    ).sum()
)

print(
    "\nPattern summary:",
    pattern_counts["count"].sum()
)

print(
    "Distress companies:",
    len(distress_summary)
)

print(
    "\nExcel report saved:"
)

print(excel_output)

print("\nCSV reports saved in:")
print(OUTPUT_DIR)

print("\nDAY 32 STEP 32.2 COMPLETE.")
print("=" * 80)