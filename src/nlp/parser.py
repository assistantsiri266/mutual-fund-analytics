import os
import re
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

ANALYSIS_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "raw",
    "analysis.xlsx"
)

TEMP_ANALYSIS_FILE = os.path.join(
    os.environ.get("TEMP", ""),
    "analysis_day29.xlsx"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "output"
)

PARSED_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "analysis_parsed.csv"
)

FAILURE_OUTPUT = os.path.join(
    OUTPUT_DIR,
    "parse_failures.csv"
)


# ============================================================
# CREATE OUTPUT FOLDER
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# REGEX
# ============================================================

# Supports:
# 10 Years: 21%
# 5 Years: 22%
# 3 Years: -1%
#
# The original requirement gives:
# (\d+)\s*Years?:?\s*([\d.]+)%
#
# We add -? so negative values are also supported.

YEAR_PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*(-?[\d.]+)%"
)


# ============================================================
# LOAD EXCEL
# ============================================================

print("=" * 80)
print("DAY 29 — NLP ANALYSIS TEXT PARSER")
print("=" * 80)

print("\nAnalysis file:")
print(ANALYSIS_FILE)

print("\nOriginal file exists:")
print(os.path.exists(ANALYSIS_FILE))


# OneDrive can sometimes give PermissionError.
# Therefore, use the already-created TEMP copy if available.

if os.path.exists(TEMP_ANALYSIS_FILE):
    INPUT_FILE = TEMP_ANALYSIS_FILE
    print("\nUsing TEMP copy:")
    print(INPUT_FILE)

elif os.path.exists(ANALYSIS_FILE):
    INPUT_FILE = ANALYSIS_FILE
    print("\nUsing original file.")

else:
    raise FileNotFoundError(
        "analysis.xlsx was not found."
    )


# ============================================================
# READ EXCEL
# ============================================================

df_raw = pd.read_excel(
    INPUT_FILE,
    sheet_name="Analysis",
    header=None
)

print("\nRaw Excel shape:")
print(df_raw.shape)


# ============================================================
# IDENTIFY HEADER ROW
# ============================================================

header_row = None

for i in range(len(df_raw)):
    row_values = df_raw.iloc[i].astype(str).tolist()

    if "company_id" in row_values:
        header_row = i
        break


if header_row is None:
    raise ValueError(
        "Could not find company_id header row."
    )


print("\nHeader row:")
print(header_row)


# ============================================================
# SET HEADER
# ============================================================

headers = df_raw.iloc[header_row].tolist()

df = df_raw.iloc[header_row + 1:].copy()

df.columns = headers

df = df.reset_index(drop=True)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

required_columns = [
    "company_id",
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe"
]

print("\nChecking required columns...")

for column in required_columns:

    if column not in df.columns:
        raise ValueError(
            f"Missing required column: {column}"
        )

print("All required columns found.")


# ============================================================
# PARSE DATA
# ============================================================

metric_columns = {
    "compounded_sales_growth": "compounded_sales_growth",
    "compounded_profit_growth": "compounded_profit_growth",
    "stock_price_cagr": "stock_price_cagr",
    "roe": "roe"
}


parsed_rows = []
failure_rows = []


for _, row in df.iterrows():

    company_id = row["company_id"]

    if pd.isna(company_id):
        continue

    company_id = str(company_id).strip()

    for column_name, metric_type in metric_columns.items():

        raw_value = row[column_name]

        if pd.isna(raw_value):
            continue

        text = str(raw_value).strip()

        # ----------------------------------------------------
        # Find all Year-based values
        # ----------------------------------------------------

        matches = YEAR_PATTERN.findall(text)

        if matches:

            for period, value in matches:

                parsed_rows.append({
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "period_years": int(period),
                    "value_pct": float(value)
                })

        else:

            # TTM / 1 Year / Last Year values do not match
            # the required Years regex.
            #
            # We log them as failures for review.

            failure_rows.append({
                "company_id": company_id,
                "metric_type": metric_type,
                "raw_text": text,
                "reason": "No Year-based regex match"
            })


# ============================================================
# CREATE DATAFRAMES
# ============================================================

parsed_df = pd.DataFrame(
    parsed_rows,
    columns=[
        "company_id",
        "metric_type",
        "period_years",
        "value_pct"
    ]
)


failure_df = pd.DataFrame(
    failure_rows,
    columns=[
        "company_id",
        "metric_type",
        "raw_text",
        "reason"
    ]
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

parsed_df = parsed_df.drop_duplicates().reset_index(drop=True)


# ============================================================
# SAVE OUTPUT
# ============================================================

parsed_df.to_csv(
    PARSED_OUTPUT,
    index=False
)

failure_df.to_csv(
    FAILURE_OUTPUT,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("PARSING COMPLETED")
print("=" * 80)

print("\nParsed rows:")
print(len(parsed_df))

print("\nParse failures:")
print(len(failure_df))

print("\nParsed output:")
print(PARSED_OUTPUT)

print("\nFailure output:")
print(FAILURE_OUTPUT)


# ============================================================
# PREVIEW
# ============================================================

print("\n" + "=" * 80)
print("PARSED DATA PREVIEW")
print("=" * 80)

if len(parsed_df) > 0:
    print(
        parsed_df.head(20).to_string(index=False)
    )
else:
    print("No parsed records found.")


print("\n" + "=" * 80)
print("FAILURE PREVIEW")
print("=" * 80)

if len(failure_df) > 0:
    print(
        failure_df.head(20).to_string(index=False)
    )
else:
    print("No parsing failures.")


# ============================================================
# DAY 29 — CAGR CROSS-VALIDATION
# ============================================================

import os
import pandas as pd

PARSED_FILE = os.path.join(PROJECT_ROOT, "output", "analysis_parsed.csv")
CAGR_FILE = os.path.join(PROJECT_ROOT, "output", "cagr_results.csv")
VALIDATION_FILE = os.path.join(PROJECT_ROOT, "output", "cagr_cross_validation.csv")

print("\n" + "=" * 70)
print("CAGR CROSS-VALIDATION")
print("=" * 70)

parsed_df = pd.read_csv(PARSED_FILE)
cagr_df = pd.read_csv(CAGR_FILE)

# Only 5-year CAGR values can be compared directly
sales_df = parsed_df[
    (parsed_df["metric_type"] == "compounded_sales_growth") &
    (parsed_df["period_years"] == 5)
].copy()

profit_df = parsed_df[
    (parsed_df["metric_type"] == "compounded_profit_growth") &
    (parsed_df["period_years"] == 5)
].copy()

# Rename columns
sales_df = sales_df.rename(
    columns={"value_pct": "parsed_revenue_cagr_5yr"}
)

profit_df = profit_df.rename(
    columns={"value_pct": "parsed_pat_cagr_5yr"}
)

# Keep only required columns
sales_df = sales_df[
    ["company_id", "parsed_revenue_cagr_5yr"]
]

profit_df = profit_df[
    ["company_id", "parsed_pat_cagr_5yr"]
]

# Merge with Ratio Engine CAGR results
validation = cagr_df[
    [
        "company_id",
        "revenue_cagr_5yr",
        "pat_cagr_5yr"
    ]
].merge(
    sales_df,
    on="company_id",
    how="inner"
).merge(
    profit_df,
    on="company_id",
    how="inner"
)

# Calculate absolute percentage difference
validation["revenue_difference_pct"] = (
    validation["parsed_revenue_cagr_5yr"]
    - validation["revenue_cagr_5yr"]
).abs()

validation["pat_difference_pct"] = (
    validation["parsed_pat_cagr_5yr"]
    - validation["pat_cagr_5yr"]
).abs()

# Flag divergence greater than 5 percentage points
validation["revenue_manual_review"] = (
    validation["revenue_difference_pct"] > 5
)

validation["pat_manual_review"] = (
    validation["pat_difference_pct"] > 5
)

validation["manual_review"] = (
    validation["revenue_manual_review"]
    | validation["pat_manual_review"]
)

validation.to_csv(
    VALIDATION_FILE,
    index=False
)

print("\nCompanies cross-validated:", len(validation))

print("\nCross-validation results:")
print(validation.to_string(index=False))

print("\nManual review required:")
print(
    validation[
        validation["manual_review"]
    ].to_string(index=False)
)

print("\nOutput:")
print(VALIDATION_FILE)

print("=" * 70)
print("CAGR CROSS-VALIDATION COMPLETED")
print("=" * 70)