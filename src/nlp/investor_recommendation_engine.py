"""
DAY 36 — INVESTOR RECOMMENDATION ENGINE

Purpose:
    Generate investor-oriented recommendation categories
    using the existing Day 35 investment ranking.

Inputs:
    output/shortlist/top_investment_shortlist.csv
    output/investment_insights_report.csv
    output/unified_insights.csv

Outputs:
    output/recommendations/investor_recommendations.csv
    output/recommendations/top_5_overall.csv
    output/recommendations/best_growth_picks.csv
    output/recommendations/best_low_risk_picks.csv
    output/recommendations/best_cashflow_picks.csv
    output/recommendations/best_financial_strength_picks.csv
    output/recommendations/watchlist.csv
    output/recommendations/high_caution.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SHORTLIST_FILE = (
    PROJECT_ROOT
    / "output"
    / "shortlist"
    / "top_investment_shortlist.csv"
)

INVESTMENT_REPORT_FILE = (
    PROJECT_ROOT
    / "output"
    / "investment_insights_report.csv"
)

UNIFIED_FILE = (
    PROJECT_ROOT
    / "output"
    / "unified_insights.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "output"
    / "recommendations"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

SHORTLIST_REQUIRED = [
    "shortlist_rank",
    "company_id",
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

REPORT_REQUIRED = [
    "company_id",
    "investment_summary",
    "recommendation_category",
]

UNIFIED_REQUIRED = [
    "company_id",
    "signal_class",
    "leverage_class",
    "growth_class",
    "cashflow_signal",
    "overall_class",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def check_file(path: Path, label: str) -> None:
    print(f"{label}:")
    print(path)
    print("EXISTS:", path.exists())
    print()

    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )


def validate_columns(
    df: pd.DataFrame,
    required: list,
    label: str
) -> None:

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"{label} missing required columns: {missing}"
        )


def clean_company_id(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return df


def numeric_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:

    df = df.copy()

    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df


# ============================================================
# LOAD INPUT FILES
# ============================================================

def load_data():

    print("=" * 80)
    print("DAY 36 — INVESTOR RECOMMENDATION ENGINE")
    print("=" * 80)
    print()

    print("PROJECT ROOT:")
    print(PROJECT_ROOT)
    print()

    check_file(
        SHORTLIST_FILE,
        "DAY 35 SHORTLIST"
    )

    check_file(
        INVESTMENT_REPORT_FILE,
        "DAY 33 INVESTMENT REPORT"
    )

    check_file(
        UNIFIED_FILE,
        "DAY 32 UNIFIED INSIGHTS"
    )

    shortlist = pd.read_csv(
        SHORTLIST_FILE
    )

    report = pd.read_csv(
        INVESTMENT_REPORT_FILE
    )

    unified = pd.read_csv(
        UNIFIED_FILE
    )

    print("=" * 80)
    print("INPUT SHAPES")
    print("=" * 80)

    print(
        "Shortlist:",
        shortlist.shape
    )

    print(
        "Investment report:",
        report.shape
    )

    print(
        "Unified insights:",
        unified.shape
    )

    print()

    validate_columns(
        shortlist,
        SHORTLIST_REQUIRED,
        "Shortlist"
    )

    validate_columns(
        report,
        REPORT_REQUIRED,
        "Investment report"
    )

    validate_columns(
        unified,
        UNIFIED_REQUIRED,
        "Unified insights"
    )

    shortlist = clean_company_id(shortlist)
    report = clean_company_id(report)
    unified = clean_company_id(unified)

    numeric_cols = [
        "shortlist_rank",
        "final_score",
        "shortlist_score",
        "financial_score",
        "cashflow_score",
        "growth_score",
        "risk_score",
        "signal_score",
        "overall_score",
    ]

    shortlist = numeric_columns(
        shortlist,
        numeric_cols
    )

    print("INPUT VALIDATION PASSED")
    print()

    return shortlist, report, unified


# ============================================================
# MERGE DATA
# ============================================================

def prepare_dataset(
    shortlist,
    report,
    unified
):

    print("=" * 80)
    print("PREPARING RECOMMENDATION DATA")
    print("=" * 80)

    # Keep only useful report columns
    report_small = report[
        [
            "company_id",
            "investment_summary",
            "recommendation_category",
        ]
    ].drop_duplicates(
        subset=["company_id"]
    )

    unified_small = unified[
        [
            "company_id",
            "signal_class",
            "leverage_class",
            "growth_class",
            "cashflow_signal",
            "overall_class",
        ]
    ].drop_duplicates(
        subset=["company_id"]
    )

    df = shortlist.merge(
        report_small,
        on="company_id",
        how="left"
    )

    df = df.merge(
        unified_small,
        on="company_id",
        how="left",
        suffixes=("", "_unified")
    )

    # Prefer existing shortlist columns where available
    for col in [
        "overall_class",
    ]:

        unified_col = f"{col}_unified"

        if unified_col in df.columns:

            df[col] = df[col].fillna(
                df[unified_col]
            )

            df.drop(
                columns=[unified_col],
                inplace=True
            )

    print(
        "Prepared dataset shape:",
        df.shape
    )

    print()

    return df


# ============================================================
# RECOMMENDATION CATEGORY LOGIC
# ============================================================

def assign_primary_category(row):

    risk = str(
        row.get("risk_level", "")
    )

    overall = str(
        row.get("overall_class", "")
    )

    growth = str(
        row.get("growth_class", "")
    )

    cashflow = str(
        row.get("cashflow_signal", "")
    )

    final_score = row.get(
        "final_score",
        np.nan
    )

    growth_score = row.get(
        "growth_score",
        np.nan
    )

    cashflow_score = row.get(
        "cashflow_score",
        np.nan
    )

    financial_score = row.get(
        "financial_score",
        np.nan
    )

    # Highest priority:
    # strong overall + low risk
    if (
        overall == "Strong Positive"
        and risk == "Low Risk"
        and pd.notna(final_score)
        and final_score >= 85
    ):
        return "Top Overall Pick"

    # Growth category
    if (
        pd.notna(growth_score)
        and growth_score >= 90
        and growth in [
            "High Growth",
            "Strong Growth"
        ]
    ):
        return "Growth Pick"

    # Cash-flow category
    if (
        pd.notna(cashflow_score)
        and cashflow_score >= 90
        and (
            "Positive" in cashflow
            or "Strong" in cashflow
        )
    ):
        return "Cash-Flow Pick"

    # Financial strength
    if (
        pd.notna(financial_score)
        and financial_score >= 80
        and risk == "Low Risk"
    ):
        return "Financial Strength Pick"

    # Watch category
    if (
        overall in [
            "Positive",
            "Balanced"
        ]
        and risk in [
            "Moderate Risk",
            "Low Risk"
        ]
    ):
        return "Watchlist"

    # High caution
    if (
        overall == "Negative"
        or risk == "High Risk"
    ):
        return "High Caution"

    return "Watchlist"


# ============================================================
# INVESTOR PROFILE TAGS
# ============================================================

def assign_investor_profiles(row):

    profiles = []

    risk = str(
        row.get("risk_level", "")
    )

    growth = str(
        row.get("growth_class", "")
    )

    cashflow = str(
        row.get("cashflow_signal", "")
    )

    financial_score = row.get(
        "financial_score",
        np.nan
    )

    growth_score = row.get(
        "growth_score",
        np.nan
    )

    cashflow_score = row.get(
        "cashflow_score",
        np.nan
    )

    # Conservative
    if (
        risk == "Low Risk"
        and pd.notna(financial_score)
        and financial_score >= 70
    ):
        profiles.append(
            "Conservative"
        )

    # Growth
    if (
        pd.notna(growth_score)
        and growth_score >= 80
    ):
        profiles.append(
            "Growth"
        )

    # Cash-flow
    if (
        pd.notna(cashflow_score)
        and cashflow_score >= 80
    ):
        profiles.append(
            "Cash Flow"
        )

    # Balanced
    if (
        risk in [
            "Low Risk",
            "Moderate Risk"
        ]
        and len(profiles) >= 2
    ):
        profiles.append(
            "Balanced"
        )

    # If nothing matched
    if not profiles:
        profiles.append(
            "General Watch"
        )

    return ", ".join(profiles)


# ============================================================
# INVESTMENT ACTION
# ============================================================

def assign_action(row):

    category = str(
        row.get(
            "primary_category",
            ""
        )
    )

    risk = str(
        row.get(
            "risk_level",
            ""
        )
    )

    overall = str(
        row.get(
            "overall_class",
            ""
        )
    )

    if category == "Top Overall Pick":
        return "Priority Review"

    if category == "Growth Pick":
        return "Growth Review"

    if category == "Cash-Flow Pick":
        return "Cash-Flow Review"

    if category == "Financial Strength Pick":
        return "Financial Strength Review"

    if category == "High Caution":
        return "Avoid / High Caution"

    if (
        overall == "Positive"
        and risk == "Low Risk"
    ):
        return "Positive Review"

    return "Monitor"


# ============================================================
# BUILD INVESTMENT SUMMARY
# ============================================================

def build_summary(row):

    company = row["company_id"]

    category = row[
        "primary_category"
    ]

    risk = row[
        "risk_level"
    ]

    overall = row[
        "overall_class"
    ]

    final_score = row[
        "final_score"
    ]

    profiles = row[
        "investor_profiles"
    ]

    return (
        f"{company} is classified as "
        f"{category} with an overall "
        f"classification of {overall} "
        f"and a risk level of {risk}. "
        f"The final score is "
        f"{final_score:.2f}. "
        f"Relevant investor profiles: "
        f"{profiles}."
    )


# ============================================================
# CREATE RECOMMENDATIONS
# ============================================================

def create_recommendations(df):

    print("=" * 80)
    print("GENERATING INVESTOR RECOMMENDATIONS")
    print("=" * 80)

    df = df.copy()

    df["primary_category"] = df.apply(
        assign_primary_category,
        axis=1
    )

    df["investor_profiles"] = df.apply(
        assign_investor_profiles,
        axis=1
    )

    df["recommended_action"] = df.apply(
        assign_action,
        axis=1
    )

    df["recommendation_summary"] = df.apply(
        build_summary,
        axis=1
    )

    # --------------------------------------------------------
    # Recommendation priority score
    # --------------------------------------------------------

    category_bonus = {
        "Top Overall Pick": 10,
        "Growth Pick": 7,
        "Cash-Flow Pick": 6,
        "Financial Strength Pick": 5,
        "Watchlist": 2,
        "High Caution": -5,
    }

    df["recommendation_score"] = (
        df["final_score"].fillna(0)
        + df["primary_category"]
        .map(category_bonus)
        .fillna(0)
    )

    # --------------------------------------------------------
    # Final recommendation rank
    # --------------------------------------------------------

    df = df.sort_values(
        [
            "recommendation_score",
            "final_score",
            "shortlist_rank",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    ).reset_index(
        drop=True
    )

    df.insert(
        0,
        "recommendation_rank",
        range(1, len(df) + 1)
    )

    return df


# ============================================================
# CREATE CATEGORY FILES
# ============================================================

def save_category_outputs(df):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 80)
    print("SAVING RECOMMENDATION FILES")
    print("=" * 80)

    # Main complete dataset
    main_file = (
        OUTPUT_DIR
        / "investor_recommendations.csv"
    )

    df.to_csv(
        main_file,
        index=False
    )

    print(
        "Main file:",
        main_file
    )

    # --------------------------------------------------------
    # Top 5 overall
    # --------------------------------------------------------

    top_5 = (
        df[
            df["primary_category"]
            == "Top Overall Pick"
        ]
        .sort_values(
            "final_score",
            ascending=False
        )
        .head(5)
        .copy()
    )

    top_5_file = (
        OUTPUT_DIR
        / "top_5_overall.csv"
    )

    top_5.to_csv(
        top_5_file,
        index=False
    )

    # --------------------------------------------------------
    # Growth picks
    # --------------------------------------------------------

    growth = (
        df[
            df["primary_category"]
            == "Growth Pick"
        ]
        .sort_values(
            "growth_score",
            ascending=False
        )
        .head(10)
        .copy()
    )

    growth_file = (
        OUTPUT_DIR
        / "best_growth_picks.csv"
    )

    growth.to_csv(
        growth_file,
        index=False
    )

    # --------------------------------------------------------
    # Low-risk picks
    # --------------------------------------------------------

    low_risk = (
        df[
            df["risk_level"]
            == "Low Risk"
        ]
        .sort_values(
            "final_score",
            ascending=False
        )
        .head(10)
        .copy()
    )

    low_risk_file = (
        OUTPUT_DIR
        / "best_low_risk_picks.csv"
    )

    low_risk.to_csv(
        low_risk_file,
        index=False
    )

    # --------------------------------------------------------
    # Cash-flow picks
    # --------------------------------------------------------

    cashflow = (
        df[
            df["primary_category"]
            == "Cash-Flow Pick"
        ]
        .sort_values(
            "cashflow_score",
            ascending=False
        )
        .head(10)
        .copy()
    )

    cashflow_file = (
        OUTPUT_DIR
        / "best_cashflow_picks.csv"
    )

    cashflow.to_csv(
        cashflow_file,
        index=False
    )

    # --------------------------------------------------------
    # Financial strength
    # --------------------------------------------------------

    financial = (
        df[
            df["primary_category"]
            == "Financial Strength Pick"
        ]
        .sort_values(
            "financial_score",
            ascending=False
        )
        .head(10)
        .copy()
    )

    financial_file = (
        OUTPUT_DIR
        / "best_financial_strength_picks.csv"
    )

    financial.to_csv(
        financial_file,
        index=False
    )

    # --------------------------------------------------------
    # Watchlist
    # --------------------------------------------------------

    watchlist = (
        df[
            df["primary_category"]
            == "Watchlist"
        ]
        .sort_values(
            "final_score",
            ascending=False
        )
        .copy()
    )

    watch_file = (
        OUTPUT_DIR
        / "watchlist.csv"
    )

    watchlist.to_csv(
        watch_file,
        index=False
    )

    # --------------------------------------------------------
    # High caution
    # --------------------------------------------------------

    caution = (
        df[
            df["primary_category"]
            == "High Caution"
        ]
        .sort_values(
            "final_score",
            ascending=True
        )
        .copy()
    )

    caution_file = (
        OUTPUT_DIR
        / "high_caution.csv"
    )

    caution.to_csv(
        caution_file,
        index=False
    )

    print()
    print("OUTPUT FILES CREATED:")
    print()

    for file in [
        main_file,
        top_5_file,
        growth_file,
        low_risk_file,
        cashflow_file,
        financial_file,
        watch_file,
        caution_file,
    ]:
        print(
            "-",
            file
        )

    print()

    return {
        "main": main_file,
        "top5": top_5_file,
        "growth": growth_file,
        "low_risk": low_risk_file,
        "cashflow": cashflow_file,
        "financial": financial_file,
        "watchlist": watch_file,
        "caution": caution_file,
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_outputs(
    df,
    output_files
):

    print("=" * 80)
    print("DAY 36 VALIDATION")
    print("=" * 80)

    # --------------------------------------------------------
    # Main dataset validation
    # --------------------------------------------------------

    required_output = [
        "recommendation_rank",
        "company_id",
        "primary_category",
        "investor_profiles",
        "recommended_action",
        "recommendation_score",
        "recommendation_summary",
    ]

    missing = [
        col
        for col in required_output
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing output columns: {missing}"
        )

    print(
        "Required columns:",
        "PASSED"
    )

    # Missing company IDs
    missing_company = (
        df["company_id"]
        .isna()
        .sum()
    )

    print(
        "Missing company_id:",
        missing_company
    )

    if missing_company != 0:
        raise ValueError(
            "Missing company IDs found."
        )

    # Duplicate companies
    duplicate_companies = (
        df["company_id"]
        .duplicated()
        .sum()
    )

    print(
        "Duplicate companies:",
        duplicate_companies
    )

    if duplicate_companies != 0:
        raise ValueError(
            "Duplicate companies found."
        )

    # Missing scores
    missing_scores = (
        df["recommendation_score"]
        .isna()
        .sum()
    )

    print(
        "Missing recommendation scores:",
        missing_scores
    )

    if missing_scores != 0:
        raise ValueError(
            "Missing recommendation scores found."
        )

    # Empty summaries
    empty_summaries = (
        df["recommendation_summary"]
        .fillna("")
        .str.strip()
        .eq("")
        .sum()
    )

    print(
        "Empty recommendation summaries:",
        empty_summaries
    )

    if empty_summaries != 0:
        raise ValueError(
            "Empty recommendation summaries found."
        )

    # Rank validation
    expected_ranks = list(
        range(1, len(df) + 1)
    )

    actual_ranks = (
        df["recommendation_rank"]
        .astype(int)
        .tolist()
    )

    if actual_ranks != expected_ranks:
        raise ValueError(
            "Recommendation ranks are invalid."
        )

    print(
        "Recommendation ranks:",
        "PASSED"
    )

    # --------------------------------------------------------
    # File validation
    # --------------------------------------------------------

    for label, path in output_files.items():

        if not path.exists():
            raise FileNotFoundError(
                f"{label} output not created: {path}"
            )

    print(
        "Output files:",
        "PASSED"
    )

    # --------------------------------------------------------
    # Category counts
    # --------------------------------------------------------

    print()
    print("PRIMARY CATEGORY COUNTS:")

    print(
        df["primary_category"]
        .value_counts()
    )

    print()

    print("RISK LEVEL COUNTS:")

    print(
        df["risk_level"]
        .value_counts()
    )

    print()

    print(
        "TOTAL RECOMMENDATION ROWS:",
        len(df)
    )

    print(
        "UNIQUE COMPANIES:",
        df["company_id"].nunique()
    )

    if len(df) != df["company_id"].nunique():
        raise ValueError(
            "Company uniqueness validation failed."
        )

    print()
    print("VALIDATION PASSED")
    print()


# ============================================================
# MAIN
# ============================================================

def main():

    shortlist, report, unified = load_data()

    df = prepare_dataset(
        shortlist,
        report,
        unified
    )

    recommendations = create_recommendations(
        df
    )

    output_files = save_category_outputs(
        recommendations
    )

    validate_outputs(
        recommendations,
        output_files
    )

    print("=" * 80)
    print("DAY 36 COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print()

    print(
        "MAIN OUTPUT:"
    )

    print(
        output_files["main"]
    )

    print()

    print(
        "TOP 5 OVERALL:"
    )

    display_columns = [
        "recommendation_rank",
        "company_id",
        "final_score",
        "primary_category",
        "risk_level",
        "overall_class",
        "recommended_action",
    ]

    print(
        recommendations[
            display_columns
        ].head(10).to_string(
            index=False
        )
    )

    print()


if __name__ == "__main__":
    main()