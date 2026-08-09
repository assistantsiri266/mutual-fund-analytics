import os
import pandas as pd
import numpy as np


# ============================================================
# DAY 33 — INVESTMENT INSIGHTS REPORT GENERATOR
# ============================================================

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
    "investment_insights_report.csv"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def classify_risk(row):

    overall = str(row["overall_class"])
    leverage = str(row["leverage_class"])
    growth = str(row["growth_class"])
    cashflow = str(row["cashflow_signal"])

    risk_score = 0

    # Overall classification
    if overall == "Strong Positive":
        risk_score += 0
    elif overall == "Positive":
        risk_score += 1
    elif overall == "Balanced":
        risk_score += 2
    else:
        risk_score += 3

    # Leverage
    if "High" in leverage:
        risk_score += 2
    elif "Moderate" in leverage:
        risk_score += 1

    # Growth
    if "Negative" in growth:
        risk_score += 2
    elif "Mixed" in growth:
        risk_score += 1

    # Cash flow
    if "Negative" in cashflow:
        risk_score += 2
    elif "Balanced" in cashflow:
        risk_score += 1

    if risk_score <= 1:
        return "Low Risk"

    elif risk_score <= 3:
        return "Moderate Risk"

    else:
        return "High Risk"


def generate_investment_view(row):

    overall = str(row["overall_class"])
    signal = str(row["signal_class"])
    risk = str(row["risk_level"])

    if overall == "Strong Positive":
        return "Strong Positive Investment Signals"

    elif overall == "Positive":
        return "Positive Investment Signals"

    elif overall == "Balanced":
        return "Balanced Investment Signals"

    elif overall == "Negative":
        return "Negative Investment Signals"

    elif signal == "Strong Positive":
        return "Strong Positive Investment Signals"

    elif risk == "High Risk":
        return "High Risk — Requires Careful Review"

    else:
        return "Requires Further Review"


def generate_summary(row):

    company = row["company_id"]

    return (
        f"{company} shows {row['overall_class'].lower()} overall "
        f"investment signals with {row['leverage_class'].lower()}, "
        f"{row['growth_class'].lower()}, and "
        f"{row['cashflow_signal'].lower()}. "
        f"The assessed risk level is {row['risk_level'].lower()}."
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 80)
    print("DAY 33 — INVESTMENT INSIGHTS REPORT GENERATOR")
    print("=" * 80)

    print("\nPROJECT ROOT:")
    print(PROJECT_ROOT)

    print("\nINPUT FILE:")
    print(INPUT_FILE)

    print("\nINPUT EXISTS:")
    print(os.path.exists(INPUT_FILE))

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Input file not found:\n{INPUT_FILE}"
        )

    df = pd.read_csv(INPUT_FILE)

    print("\nINPUT SHAPE:")
    print(df.shape)

    print("\nCOLUMNS:")
    print(df.columns.tolist())

    return df


# ============================================================
# VALIDATE INPUT
# ============================================================

def validate_input(df):

    print("\n" + "=" * 80)
    print("VALIDATING INPUT")
    print("=" * 80)

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

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    print("\nRequired columns: PASSED")

    print(
        "Missing company_id:",
        df["company_id"].isna().sum()
    )

    duplicate_count = df["company_id"].duplicated().sum()

    print(
        "Duplicate company rows:",
        duplicate_count
    )

    if duplicate_count > 0:
        raise ValueError(
            "Duplicate company rows detected."
        )

    print("Input validation PASSED")


# ============================================================
# CREATE REPORT
# ============================================================

def create_report(df):

    print("\n" + "=" * 80)
    print("CREATING INVESTMENT REPORT")
    print("=" * 80)

    report = df.copy()

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    report["risk_level"] = report.apply(
        classify_risk,
        axis=1
    )

    # --------------------------------------------------------
    # Investment view
    # --------------------------------------------------------

    report["investment_view"] = report.apply(
        generate_investment_view,
        axis=1
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    report["investment_summary"] = report.apply(
        generate_summary,
        axis=1
    )

    # --------------------------------------------------------
    # Final recommendation category
    # --------------------------------------------------------

    recommendation_map = {
        "Strong Positive": "Positive",
        "Positive": "Positive",
        "Balanced": "Watch",
        "Negative": "Avoid / High Caution"
    }

    report["recommendation_category"] = (
        report["overall_class"]
        .map(recommendation_map)
        .fillna("Review")
    )

    return report


# ============================================================
# SELECT FINAL COLUMNS
# ============================================================

def prepare_final_columns(report):

    columns = [
        "company_id",
        "total_pros",
        "total_cons",
        "signal_balance",
        "signal_class",
        "leverage_class",
        "growth_class",
        "cashflow_signal",
        "overall_class",
        "risk_level",
        "investment_view",
        "recommendation_category",
        "investment_summary"
    ]

    return report[columns]


# ============================================================
# VALIDATION OF FINAL REPORT
# ============================================================

def validate_output(report):

    print("\n" + "=" * 80)
    print("OUTPUT VALIDATION")
    print("=" * 80)

    print("\nTotal rows:", len(report))

    print(
        "Companies:",
        report["company_id"].nunique()
    )

    print(
        "Missing company_id:",
        report["company_id"].isna().sum()
    )

    print(
        "Duplicate companies:",
        report["company_id"].duplicated().sum()
    )

    print(
        "Empty investment summaries:",
        (
            report["investment_summary"]
            .fillna("")
            .str.strip()
            .eq("")
            .sum()
        )
    )

    print("\nRISK LEVEL COUNTS:")
    print(
        report["risk_level"]
        .value_counts()
    )

    print("\nOVERALL CLASS COUNTS:")
    print(
        report["overall_class"]
        .value_counts()
    )

    print("\nRECOMMENDATION COUNTS:")
    print(
        report["recommendation_category"]
        .value_counts()
    )

    # --------------------------------------------------------
    # Hard validation
    # --------------------------------------------------------

    assert report["company_id"].isna().sum() == 0

    assert report["company_id"].duplicated().sum() == 0

    assert (
        report["investment_summary"]
        .fillna("")
        .str.strip()
        .eq("")
        .sum()
        == 0
    )

    print("\nVALIDATION PASSED")


# ============================================================
# SAVE
# ============================================================

def save_report(report):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    report.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 80)
    print("OUTPUT SAVED")
    print("=" * 80)

    print("\nFILE:")
    print(OUTPUT_FILE)

    print("\nRows:")
    print(len(report))

    print("\nCompanies:")
    print(report["company_id"].nunique())


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_data()

    validate_input(df)

    report = create_report(df)

    final_report = prepare_final_columns(report)

    validate_output(final_report)

    save_report(final_report)

    print("\n" + "=" * 80)
    print("DAY 33 COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()