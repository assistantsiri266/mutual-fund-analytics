import os
import pandas as pd
import numpy as np


# ============================================================
# DAY 34 — INVESTMENT RANKING ENGINE
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

INPUT_FILE = os.path.join(
    PROJECT_ROOT,
    "output",
    "investment_insights_report.csv"
)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "output"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "investment_ranking.csv"
)


# ============================================================
# SCORE MAPPINGS
# ============================================================

# Overall investment classification
OVERALL_SCORE = {
    "Strong Positive": 100,
    "Positive": 80,
    "Balanced": 60,
    "Negative": 35
}


# Signal classification
SIGNAL_SCORE = {
    "Strong Positive": 100,
    "Positive": 80,
    "Balanced": 60,
    "Negative": 35
}


# Growth classification
GROWTH_SCORE = {
    "High Growth": 100,
    "Moderate Growth": 80,
    "Mixed Growth": 60,
    "Low Growth": 45,
    "Negative Growth": 30
}


# Cash-flow classification
CASHFLOW_SCORE = {
    "Positive Cash Flow Signals": 100,
    "Balanced Cash Flow Signals": 70,
    "Negative Cash Flow Signals": 35
}


# Risk score
# Higher score = lower risk
RISK_SCORE = {
    "Low Risk": 100,
    "Moderate Risk": 65,
    "High Risk": 30
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_score(value, mapping, default=50):

    value = str(value).strip()

    return mapping.get(
        value,
        default
    )


def calculate_financial_score(row):

    total_pros = float(row["total_pros"])
    total_cons = float(row["total_cons"])

    total = total_pros + total_cons

    if total <= 0:
        return 50.0

    # Convert pros-cons balance to 0-100 scale
    balance_ratio = (
        (total_pros - total_cons) / total
    )

    score = 50 + (
        balance_ratio * 50
    )

    return round(
        max(0, min(100, score)),
        2
    )


def calculate_cashflow_score(row):

    return get_score(
        row["cashflow_signal"],
        CASHFLOW_SCORE
    )


def calculate_growth_score(row):

    return get_score(
        row["growth_class"],
        GROWTH_SCORE
    )


def calculate_risk_score(row):

    return get_score(
        row["risk_level"],
        RISK_SCORE
    )


def calculate_signal_score(row):

    return get_score(
        row["signal_class"],
        SIGNAL_SCORE
    )


def calculate_overall_score(row):

    return get_score(
        row["overall_class"],
        OVERALL_SCORE
    )


# ============================================================
# FINAL SCORE
# ============================================================

def calculate_final_score(row):

    financial = row["financial_score"]
    cashflow = row["cashflow_score"]
    growth = row["growth_score"]
    risk = row["risk_score"]
    signal = row["signal_score"]
    overall = row["overall_score"]

    # --------------------------------------------------------
    # Weighted scoring model
    # --------------------------------------------------------
    #
    # Financial signals : 25%
    # Cash flow         : 20%
    # Growth            : 15%
    # Risk              : 15%
    # Signal strength   : 10%
    # Overall class     : 15%
    #
    # Total = 100%
    # --------------------------------------------------------

    final_score = (
        financial * 0.25
        + cashflow * 0.20
        + growth * 0.15
        + risk * 0.15
        + signal * 0.10
        + overall * 0.15
    )

    return round(
        final_score,
        2
    )


# ============================================================
# RANKING CATEGORY
# ============================================================

def get_ranking_category(score):

    if score >= 85:
        return "Top Tier"

    elif score >= 75:
        return "Strong"

    elif score >= 65:
        return "Moderate"

    elif score >= 50:
        return "Watchlist"

    else:
        return "High Caution"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print("=" * 80)
    print("DAY 34 — INVESTMENT RANKING ENGINE")
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

    df = pd.read_csv(
        INPUT_FILE
    )

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
    print("INPUT VALIDATION")
    print("=" * 80)

    required_columns = [
        "company_id",
        "total_pros",
        "total_cons",
        "signal_balance",
        "signal_class",
        "growth_class",
        "cashflow_signal",
        "overall_class",
        "risk_level"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing required columns: {missing}"
        )

    print("\nRequired columns: PASSED")

    missing_company = (
        df["company_id"]
        .isna()
        .sum()
    )

    print(
        "Missing company_id:",
        missing_company
    )

    duplicate_companies = (
        df["company_id"]
        .duplicated()
        .sum()
    )

    print(
        "Duplicate company rows:",
        duplicate_companies
    )

    if missing_company > 0:

        raise ValueError(
            "Missing company_id detected."
        )

    if duplicate_companies > 0:

        raise ValueError(
            "Duplicate company rows detected."
        )

    print(
        "Input validation PASSED"
    )


# ============================================================
# CREATE SCORES
# ============================================================

def create_scores(df):

    print("\n" + "=" * 80)
    print("CALCULATING INVESTMENT SCORES")
    print("=" * 80)

    result = df.copy()

    # --------------------------------------------------------
    # Financial score
    # --------------------------------------------------------

    result["financial_score"] = (
        result.apply(
            calculate_financial_score,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Cash-flow score
    # --------------------------------------------------------

    result["cashflow_score"] = (
        result.apply(
            calculate_cashflow_score,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Growth score
    # --------------------------------------------------------

    result["growth_score"] = (
        result.apply(
            calculate_growth_score,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Risk score
    # --------------------------------------------------------

    result["risk_score"] = (
        result.apply(
            calculate_risk_score,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Signal score
    # --------------------------------------------------------

    result["signal_score"] = (
        result.apply(
            calculate_signal_score,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Overall score
    # --------------------------------------------------------

    result["overall_score"] = (
        result.apply(
            calculate_overall_score,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Final weighted score
    # --------------------------------------------------------

    result["final_score"] = (
        result.apply(
            calculate_final_score,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Ranking category
    # --------------------------------------------------------

    result["ranking_category"] = (
        result["final_score"]
        .apply(get_ranking_category)
    )

    return result


# ============================================================
# CREATE RANK
# ============================================================

def create_ranking(result):

    print("\n" + "=" * 80)
    print("CREATING COMPANY RANKING")
    print("=" * 80)

    result = result.sort_values(
        by=[
            "final_score",
            "signal_balance",
            "total_pros"
        ],
        ascending=[
            False,
            False,
            False
        ]
    ).reset_index(
        drop=True
    )

    result["rank"] = (
        result.index + 1
    )

    return result


# ============================================================
# PREPARE FINAL OUTPUT
# ============================================================

def prepare_output(result):

    columns = [
        "rank",
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
        "financial_score",
        "cashflow_score",
        "growth_score",
        "risk_score",
        "signal_score",
        "overall_score",
        "final_score",
        "ranking_category"
    ]

    return result[columns]


# ============================================================
# OUTPUT VALIDATION
# ============================================================

def validate_output(result):

    print("\n" + "=" * 80)
    print("OUTPUT VALIDATION")
    print("=" * 80)

    print(
        "\nTotal rows:",
        len(result)
    )

    print(
        "Companies:",
        result["company_id"].nunique()
    )

    print(
        "Missing company_id:",
        result["company_id"].isna().sum()
    )

    print(
        "Duplicate companies:",
        result["company_id"].duplicated().sum()
    )

    print(
        "Missing final scores:",
        result["final_score"].isna().sum()
    )

    print(
        "Missing ranks:",
        result["rank"].isna().sum()
    )

    # --------------------------------------------------------
    # Score range validation
    # --------------------------------------------------------

    print(
        "\nMinimum final score:",
        result["final_score"].min()
    )

    print(
        "Maximum final score:",
        result["final_score"].max()
    )

    # --------------------------------------------------------
    # Ranking category counts
    # --------------------------------------------------------

    print("\nRANKING CATEGORY COUNTS:")

    print(
        result["ranking_category"]
        .value_counts()
    )

    # --------------------------------------------------------
    # Overall class counts
    # --------------------------------------------------------

    print("\nOVERALL CLASS COUNTS:")

    print(
        result["overall_class"]
        .value_counts()
    )

    # --------------------------------------------------------
    # Risk counts
    # --------------------------------------------------------

    print("\nRISK LEVEL COUNTS:")

    print(
        result["risk_level"]
        .value_counts()
    )

    # --------------------------------------------------------
    # Hard validation
    # --------------------------------------------------------

    assert result["company_id"].isna().sum() == 0

    assert result["company_id"].duplicated().sum() == 0

    assert result["final_score"].isna().sum() == 0

    assert result["rank"].isna().sum() == 0

    assert result["rank"].nunique() == len(result)

    assert result["final_score"].between(
        0,
        100
    ).all()

    assert (
        result["rank"].min()
        == 1
    )

    assert (
        result["rank"].max()
        == len(result)
    )

    print(
        "\nVALIDATION PASSED"
    )


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_output(result):

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 80)
    print("OUTPUT SAVED")
    print("=" * 80)

    print("\nFILE:")
    print(OUTPUT_FILE)

    print(
        "\nRows:",
        len(result)
    )

    print(
        "Companies:",
        result["company_id"].nunique()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_data()

    validate_input(
        df
    )

    scored = create_scores(
        df
    )

    ranked = create_ranking(
        scored
    )

    final_output = prepare_output(
        ranked
    )

    validate_output(
        final_output
    )

    save_output(
        final_output
    )

    print("\n" + "=" * 80)
    print("TOP 15 COMPANIES")
    print("=" * 80)

    print(
        final_output[
            [
                "rank",
                "company_id",
                "final_score",
                "ranking_category",
                "risk_level",
                "overall_class"
            ]
        ]
        .head(15)
        .to_string(index=False)
    )

    print("\n" + "=" * 80)
    print("DAY 34 COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()