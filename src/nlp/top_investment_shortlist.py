import os
import pandas as pd

# ============================================================
# DAY 35 — TOP INVESTMENT SHORTLIST GENERATOR
# ============================================================

print("=" * 80)
print("DAY 35 — TOP INVESTMENT SHORTLIST GENERATOR")
print("=" * 80)

# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

INPUT_FILE = os.path.join(
    PROJECT_ROOT,
    "output",
    "investment_ranking.csv"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "output",
    "shortlist"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "top_investment_shortlist.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("\nPROJECT ROOT:")
print(PROJECT_ROOT)

print("\nINPUT FILE:")
print(INPUT_FILE)

print("\nINPUT EXISTS:")
print(os.path.exists(INPUT_FILE))


# ============================================================
# LOAD INPUT
# ============================================================

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"Input file not found:\n{INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE)

print("\nINPUT SHAPE:")
print(df.shape)

print("\nCOLUMNS:")
print(df.columns.tolist())


# ============================================================
# INPUT VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("INPUT VALIDATION")
print("=" * 80)

required_columns = [
    "rank",
    "company_id",
    "final_score",
    "ranking_category",
    "risk_level",
    "overall_class",
    "financial_score",
    "cashflow_score",
    "growth_score",
    "risk_score",
    "signal_score",
    "overall_score",
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

print("Required columns: PASSED")

missing_company = df["company_id"].isna().sum()
duplicate_companies = df["company_id"].duplicated().sum()

print("Missing company_id:", missing_company)
print("Duplicate company rows:", duplicate_companies)

if missing_company > 0:
    raise ValueError("Missing company_id detected.")

if duplicate_companies > 0:
    raise ValueError("Duplicate company_id detected.")

print("Input validation PASSED")


# ============================================================
# CLEAN NUMERIC COLUMNS
# ============================================================

numeric_columns = [
    "rank",
    "final_score",
    "financial_score",
    "cashflow_score",
    "growth_score",
    "risk_score",
    "signal_score",
    "overall_score",
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

if df[numeric_columns].isna().any().any():
    raise ValueError(
        "Missing/non-numeric values found in scoring columns."
    )


# ============================================================
# CREATE SHORTLIST SCORE
# ============================================================

print("\n" + "=" * 80)
print("CREATING SHORTLIST")
print("=" * 80)

# Final score is the primary ranking measure.
# Risk and overall classification are used as filters.

df["shortlist_score"] = (
    df["final_score"] * 0.60
    + df["overall_score"] * 0.20
    + df["risk_score"] * 0.20
)

df["shortlist_score"] = df["shortlist_score"].round(2)


# ============================================================
# INVESTMENT BUCKET
# ============================================================

def classify_shortlist(row):

    score = row["shortlist_score"]
    risk = str(row["risk_level"]).strip()
    overall = str(row["overall_class"]).strip()

    if (
        score >= 85
        and risk == "Low Risk"
        and overall in ["Strong Positive", "Positive"]
    ):
        return "Priority Shortlist"

    elif (
        score >= 75
        and risk in ["Low Risk", "Moderate Risk"]
        and overall in ["Strong Positive", "Positive"]
    ):
        return "Strong Candidate"

    elif (
        score >= 65
        and overall in ["Strong Positive", "Positive", "Balanced"]
    ):
        return "Watchlist Candidate"

    else:
        return "High Caution"


df["shortlist_category"] = df.apply(
    classify_shortlist,
    axis=1
)


# ============================================================
# INVESTMENT VIEW
# ============================================================

def create_investment_view(row):

    category = row["shortlist_category"]
    risk = row["risk_level"]
    overall = row["overall_class"]

    if category == "Priority Shortlist":
        return (
            "Strong candidate with favorable overall signals "
            "and comparatively low risk."
        )

    elif category == "Strong Candidate":
        return (
            "Potential candidate with positive investment signals; "
            "risk and growth should still be monitored."
        )

    elif category == "Watchlist Candidate":
        return (
            "Mixed or moderate signals; suitable for monitoring "
            "before making an investment decision."
        )

    return (
        "Higher caution is warranted due to weaker overall signals "
        "and/or elevated risk."
    )


df["investment_view"] = df.apply(
    create_investment_view,
    axis=1
)


# ============================================================
# FINAL SHORTLIST RANK
# ============================================================

df = df.sort_values(
    by=[
        "shortlist_score",
        "final_score",
        "overall_score"
    ],
    ascending=False
).reset_index(drop=True)

df["shortlist_rank"] = range(
    1,
    len(df) + 1
)


# ============================================================
# SELECT TOP 20
# ============================================================

top_20 = df.head(20).copy()


# ============================================================
# OUTPUT COLUMNS
# ============================================================

output_columns = [
    "shortlist_rank",
    "company_id",
    "rank",
    "final_score",
    "shortlist_score",
    "shortlist_category",
    "risk_level",
    "overall_class",
    "financial_score",
    "cashflow_score",
    "growth_score",
    "risk_score",
    "signal_score",
    "overall_score",
    "investment_view",
]

top_20 = top_20[output_columns]


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("OUTPUT VALIDATION")
print("=" * 80)

print("Total shortlist rows:", len(top_20))
print(
    "Unique companies:",
    top_20["company_id"].nunique()
)

print(
    "Missing company_id:",
    top_20["company_id"].isna().sum()
)

print(
    "Duplicate companies:",
    top_20["company_id"].duplicated().sum()
)

print(
    "Missing shortlist scores:",
    top_20["shortlist_score"].isna().sum()
)

print(
    "Missing shortlist ranks:",
    top_20["shortlist_rank"].isna().sum()
)

if top_20["company_id"].isna().sum() > 0:
    raise ValueError("Missing company_id in shortlist.")

if top_20["company_id"].duplicated().sum() > 0:
    raise ValueError("Duplicate company in shortlist.")

if top_20["shortlist_score"].isna().sum() > 0:
    raise ValueError("Missing shortlist score.")

if top_20["shortlist_rank"].isna().sum() > 0:
    raise ValueError("Missing shortlist rank.")


# ============================================================
# CATEGORY COUNTS
# ============================================================

print("\nSHORTLIST CATEGORY COUNTS:")

print(
    top_20["shortlist_category"]
    .value_counts()
)


# ============================================================
# RISK COUNTS
# ============================================================

print("\nRISK LEVEL COUNTS:")

print(
    top_20["risk_level"]
    .value_counts()
)


# ============================================================
# SAVE OUTPUT
# ============================================================

top_20.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 80)
print("OUTPUT SAVED")
print("=" * 80)

print("\nFILE:")
print(OUTPUT_FILE)

print("\nRows:")
print(len(top_20))

print(
    "\nCompanies:",
    top_20["company_id"].nunique()
)


# ============================================================
# DISPLAY TOP 20
# ============================================================

print("\n" + "=" * 80)
print("TOP 20 INVESTMENT SHORTLIST")
print("=" * 80)

print(
    top_20[
        [
            "shortlist_rank",
            "company_id",
            "final_score",
            "shortlist_score",
            "shortlist_category",
            "risk_level",
            "overall_class",
        ]
    ].to_string(index=False)
)


# ============================================================
# COMPLETION
# ============================================================

print("\n" + "=" * 80)
print("DAY 35 COMPLETED SUCCESSFULLY")
print("=" * 80)