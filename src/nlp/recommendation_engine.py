import os
import pandas as pd
import numpy as np


# =============================================================================
# DAY 33 — INVESTMENT RECOMMENDATION ENGINE
# =============================================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

INPUT_FILE = os.path.join(
    PROJECT_ROOT,
    "output",
    "unified_insights.csv"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "output"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "investment_recommendations.csv"
)


# =============================================================================
# DISPLAY HEADER
# =============================================================================

print("=" * 80)
print("DAY 33 — INVESTMENT RECOMMENDATION ENGINE")
print("=" * 80)

print("\nPROJECT ROOT:")
print(PROJECT_ROOT)

print("\nINPUT:")
print(INPUT_FILE)

print("INPUT EXISTS:")
print(os.path.exists(INPUT_FILE))


# =============================================================================
# LOAD DATA
# =============================================================================

if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(
        f"\nRequired input file not found:\n{INPUT_FILE}\n"
        "\nPlease complete Day 32 first."
    )

df = pd.read_csv(INPUT_FILE)

print("\nINPUT SHAPE:")
print(df.shape)

print("\nINPUT COLUMNS:")
print(df.columns.tolist())


# =============================================================================
# REQUIRED COLUMNS
# =============================================================================

required_columns = [
    "company_id",
    "total_pros",
    "total_cons",
    "signal_balance",
    "signal_class",
    "leverage_class",
    "growth_class",
    "cashflow_signal",
    "overall_class"
]

print("\n" + "=" * 80)
print("CHECKING REQUIRED COLUMNS")
print("=" * 80)

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    print("\nMISSING COLUMNS:")
    print(missing_columns)

    raise ValueError(
        "\nRequired columns are missing from unified_insights.csv."
    )

print("\nAll required columns found.")


# =============================================================================
# BASIC CLEANING
# =============================================================================

df["company_id"] = df["company_id"].astype(str).str.strip()

numeric_columns = [
    "total_pros",
    "total_cons",
    "signal_balance"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )

df[numeric_columns] = df[numeric_columns].fillna(0)


# =============================================================================
# RECOMMENDATION LOGIC
# =============================================================================

def calculate_recommendation(row):

    score = 0
    reasons = []

    # -------------------------------------------------------------------------
    # 1. OVERALL CLASS
    # -------------------------------------------------------------------------

    overall = str(row["overall_class"]).strip()

    if overall == "Strong Positive":
        score += 4
        reasons.append("Strong overall investment signals")

    elif overall == "Positive":
        score += 2
        reasons.append("Positive overall investment signals")

    elif overall == "Balanced":
        score += 0
        reasons.append("Balanced investment signals")

    elif overall == "Negative":
        score -= 4
        reasons.append("Negative overall investment signals")


    # -------------------------------------------------------------------------
    # 2. SIGNAL CLASS
    # -------------------------------------------------------------------------

    signal_class = str(row["signal_class"]).strip()

    if signal_class == "Strong Positive":
        score += 3
        reasons.append("Strong financial signal balance")

    elif signal_class == "Positive":
        score += 2
        reasons.append("Positive financial signal balance")

    elif signal_class == "Balanced":
        score += 0

    elif signal_class == "Negative":
        score -= 3
        reasons.append("Negative financial signal balance")


    # -------------------------------------------------------------------------
    # 3. LEVERAGE
    # -------------------------------------------------------------------------

    leverage = str(row["leverage_class"]).strip()

    if leverage == "Low Leverage":
        score += 2
        reasons.append("Low leverage")

    elif leverage == "Moderate Leverage":
        score += 0

    elif leverage == "High Leverage":
        score -= 2
        reasons.append("High leverage")


    # -------------------------------------------------------------------------
    # 4. GROWTH
    # -------------------------------------------------------------------------

    growth = str(row["growth_class"]).strip()

    if growth == "High Growth":
        score += 2
        reasons.append("High growth")

    elif growth == "Moderate Growth":
        score += 1
        reasons.append("Moderate growth")

    elif growth == "Mixed Growth":
        score += 0

    elif growth == "Low Growth":
        score -= 1
        reasons.append("Low growth")

    elif growth == "Negative Growth":
        score -= 2
        reasons.append("Negative growth")


    # -------------------------------------------------------------------------
    # 5. CASH FLOW
    # -------------------------------------------------------------------------

    cashflow = str(row["cashflow_signal"]).strip()

    if cashflow == "Positive Cash Flow Signals":
        score += 2
        reasons.append("Positive cash-flow signals")

    elif cashflow == "Balanced Cash Flow Signals":
        score += 0

    elif cashflow == "Negative Cash Flow Signals":
        score -= 2
        reasons.append("Negative cash-flow signals")


    # -------------------------------------------------------------------------
    # FINAL RECOMMENDATION
    # -------------------------------------------------------------------------

    if score >= 8:
        recommendation = "BUY"

    elif score >= 3:
        recommendation = "HOLD"

    else:
        recommendation = "AVOID"


    return pd.Series(
        [
            score,
            recommendation,
            "; ".join(reasons)
        ],
        index=[
            "recommendation_score",
            "recommendation",
            "recommendation_reason"
        ]
    )


# =============================================================================
# GENERATE RECOMMENDATIONS
# =============================================================================

print("\n" + "=" * 80)
print("GENERATING INVESTMENT RECOMMENDATIONS")
print("=" * 80)

print("\nCOMPANIES:")
print(df["company_id"].nunique())

recommendation_data = df.apply(
    calculate_recommendation,
    axis=1
)

df = pd.concat(
    [
        df,
        recommendation_data
    ],
    axis=1
)


# =============================================================================
# RISK LEVEL
# =============================================================================

def calculate_risk(row):

    leverage = str(row["leverage_class"]).strip()
    overall = str(row["overall_class"]).strip()
    cashflow = str(row["cashflow_signal"]).strip()

    risk_points = 0

    if leverage == "High Leverage":
        risk_points += 2

    elif leverage == "Moderate Leverage":
        risk_points += 1

    if overall == "Negative":
        risk_points += 2

    elif overall == "Balanced":
        risk_points += 1

    if cashflow == "Negative Cash Flow Signals":
        risk_points += 2

    elif cashflow == "Balanced Cash Flow Signals":
        risk_points += 1


    if risk_points >= 4:
        return "High Risk"

    elif risk_points >= 2:
        return "Moderate Risk"

    else:
        return "Low Risk"


df["risk_level"] = df.apply(
    calculate_risk,
    axis=1
)


# =============================================================================
# INVESTMENT SCORE
# =============================================================================

def normalize_score(score):

    # Convert internal score to a 0–100 style score.
    # Expected approximate range is -11 to +13.

    normalized = ((score + 11) / 24) * 100

    normalized = max(
        0,
        min(
            100,
            normalized
        )
    )

    return round(
        normalized,
        2
    )


df["investment_score"] = df[
    "recommendation_score"
].apply(
    normalize_score
)


# =============================================================================
# PRIORITY
# =============================================================================

def calculate_priority(row):

    recommendation = row["recommendation"]
    risk = row["risk_level"]

    if recommendation == "BUY" and risk == "Low Risk":
        return "High Priority"

    elif recommendation == "BUY":
        return "Medium Priority"

    elif recommendation == "HOLD":
        return "Medium Priority"

    else:
        return "Low Priority"


df["investment_priority"] = df.apply(
    calculate_priority,
    axis=1
)


# =============================================================================
# SORT
# =============================================================================

df = df.sort_values(
    by=[
        "investment_score",
        "signal_balance"
    ],
    ascending=[
        False,
        False
    ]
).reset_index(drop=True)


# =============================================================================
# SELECT OUTPUT COLUMNS
# =============================================================================

output_columns = [
    "company_id",
    "total_pros",
    "total_cons",
    "signal_balance",
    "signal_class",
    "leverage_class",
    "growth_class",
    "cashflow_signal",
    "overall_class",
    "recommendation_score",
    "investment_score",
    "recommendation",
    "risk_level",
    "investment_priority",
    "recommendation_reason"
]

result = df[output_columns].copy()


# =============================================================================
# VALIDATION
# =============================================================================

print("\n" + "=" * 80)
print("VALIDATION")
print("=" * 80)

print("\nTOTAL ROWS:")
print(len(result))

print("\nCOMPANIES:")
print(result["company_id"].nunique())


# Required columns validation

missing_output_columns = [
    col for col in output_columns
    if col not in result.columns
]

if missing_output_columns:
    raise ValueError(
        f"Missing output columns: {missing_output_columns}"
    )

print("\nRequired output columns: PASSED")


# Missing company validation

missing_company_count = result[
    "company_id"
].isna().sum()

print("\nMissing company_id:")
print(missing_company_count)


if missing_company_count != 0:
    raise ValueError(
        "Some company_id values are missing."
    )


# Duplicate validation

duplicate_count = result[
    "company_id"
].duplicated().sum()

print("\nDuplicate company rows:")
print(duplicate_count)


if duplicate_count != 0:
    raise ValueError(
        "Duplicate company rows detected."
    )


# Empty recommendation validation

empty_recommendations = (
    result["recommendation"]
    .isna()
    .sum()
)

print("\nEmpty recommendations:")
print(empty_recommendations)


if empty_recommendations != 0:
    raise ValueError(
        "Some companies do not have a recommendation."
    )


# Score validation

invalid_scores = (
    (result["investment_score"] < 0)
    |
    (result["investment_score"] > 100)
).sum()

print("\nInvalid investment scores:")
print(invalid_scores)


if invalid_scores != 0:
    raise ValueError(
        "Investment score outside 0–100 range."
    )


# Recommendation validation

valid_recommendations = {
    "BUY",
    "HOLD",
    "AVOID"
}

invalid_recommendations = set(
    result["recommendation"].dropna().unique()
) - valid_recommendations

print("\nInvalid recommendation labels:")
print(invalid_recommendations)


if invalid_recommendations:
    raise ValueError(
        "Invalid recommendation labels found."
    )


print("\nVALIDATION PASSED")


# =============================================================================
# RECOMMENDATION COUNTS
# =============================================================================

print("\n" + "=" * 80)
print("RECOMMENDATION COUNTS")
print("=" * 80)

print(
    result["recommendation"]
    .value_counts()
    .to_string()
)


# =============================================================================
# RISK COUNTS
# =============================================================================

print("\n" + "=" * 80)
print("RISK LEVEL COUNTS")
print("=" * 80)

print(
    result["risk_level"]
    .value_counts()
    .to_string()
)


# =============================================================================
# PRIORITY COUNTS
# =============================================================================

print("\n" + "=" * 80)
print("INVESTMENT PRIORITY COUNTS")
print("=" * 80)

print(
    result["investment_priority"]
    .value_counts()
    .to_string()
)


# =============================================================================
# TOP COMPANIES
# =============================================================================

print("\n" + "=" * 80)
print("TOP 15 COMPANIES")
print("=" * 80)

print(
    result[
        [
            "company_id",
            "investment_score",
            "recommendation",
            "risk_level",
            "investment_priority"
        ]
    ]
    .head(15)
    .to_string(index=False)
)


# =============================================================================
# SAVE OUTPUT
# =============================================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

result.to_csv(
    OUTPUT_FILE,
    index=False
)


# =============================================================================
# FINAL MESSAGE
# =============================================================================

print("\n" + "=" * 80)
print("OUTPUT SAVED")
print("=" * 80)

print(OUTPUT_FILE)

print("\nRows:")
print(len(result))

print("\nCompanies:")
print(result["company_id"].nunique())

print("\n" + "=" * 80)
print("DAY 33 COMPLETED SUCCESSFULLY")
print("=" * 80)