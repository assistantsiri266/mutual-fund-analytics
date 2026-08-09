import os
import sqlite3
import pandas as pd
import numpy as np


# =============================================================================
# DAY 32 — UNIFIED INVESTMENT INSIGHTS GENERATOR
# =============================================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
DB_PATH = os.path.join(PROJECT_ROOT, "database", "financial_data.db")


FINANCIAL_PROS_CONS = os.path.join(
    OUTPUT_DIR,
    "pros_cons_generated.csv"
)

CASHFLOW_PROS_CONS = os.path.join(
    OUTPUT_DIR,
    "cashflow_pros_cons.csv"
)

CAGR_VALIDATION = os.path.join(
    OUTPUT_DIR,
    "cagr_cross_validation.csv"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "unified_insights.csv"
)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def print_header(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def safe_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def normalize_company_id(value):
    if pd.isna(value):
        return None

    return str(value).strip().upper()


def safe_divide(a, b):
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")

    result = np.where(
        (b != 0) & (~pd.isna(b)),
        a / b,
        np.nan
    )

    return result


# =============================================================================
# LOAD FINANCIAL DATABASE
# =============================================================================

def load_financial_database():

    print_header("LOADING FINANCIAL DATABASE")

    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    print("DATABASE:")
    print(DB_PATH)
    print("EXISTS:", os.path.exists(DB_PATH))

    conn = sqlite3.connect(DB_PATH)

    tables = pd.read_sql_query(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
        """,
        conn
    )

    print("\nDATABASE TABLES:")

    for table in tables["name"].tolist():
        print("-", table)

    # -------------------------------------------------------------------------
    # Financial ratios
    # -------------------------------------------------------------------------

    financial = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        conn
    )

    # -------------------------------------------------------------------------
    # Valuation
    # -------------------------------------------------------------------------

    valuation = pd.DataFrame()

    if "valuation" in tables["name"].tolist():

        valuation = pd.read_sql_query(
            "SELECT * FROM valuation",
            conn
        )

    # -------------------------------------------------------------------------
    # Peer percentiles
    # -------------------------------------------------------------------------

    peer = pd.DataFrame()

    if "peer_percentiles" in tables["name"].tolist():

        peer = pd.read_sql_query(
            "SELECT * FROM peer_percentiles",
            conn
        )

    conn.close()

    print("\nFinancial database shape:", financial.shape)

    print("\nFinancial columns:")
    print(financial.columns.tolist())

    return financial, valuation, peer


# =============================================================================
# MAKE FINANCIAL DATA SCHEMA SAFE
# =============================================================================

def prepare_financial_data(df):

    print_header("PREPARING FINANCIAL DATA")

    df = df.copy()

    # -------------------------------------------------------------------------
    # Normalize company ID
    # -------------------------------------------------------------------------

    if "company_id" not in df.columns:
        raise ValueError(
            "financial_ratios table does not contain company_id"
        )

    df["company_id"] = df["company_id"].apply(
        normalize_company_id
    )

    # -------------------------------------------------------------------------
    # Convert important numeric columns
    # -------------------------------------------------------------------------

    numeric_columns = [
        "sales",
        "expenses",
        "operating_profit",
        "opm_percentage",
        "other_income",
        "interest",
        "depreciation",
        "profit_before_tax",
        "tax_percentage",
        "net_profit",
        "eps",
        "dividend_payout",
        "equity_capital",
        "reserves",
        "borrowings",
        "other_liabilities",
        "total_liabilities",
        "fixed_assets",
        "cwip",
        "investments",
        "other_asset",
        "total_assets",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "roe_calculated",
        "roce_calculated",
        "roa_calculated",
        "roce_percentage",
        "roe_percentage",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "net_debt",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
        "free_cash_flow",
        "capex_pct",
        "fcf_conversion"
    ]

    for col in numeric_columns:

        if col in df.columns:
            df[col] = safe_numeric(df[col])

    # -------------------------------------------------------------------------
    # IMPORTANT FIX
    #
    # Do NOT directly access:
    #
    # df["high_leverage_flag"]
    #
    # because your SQLite table does not contain this column.
    #
    # Instead calculate it from debt_to_equity.
    # -------------------------------------------------------------------------

    if "high_leverage_flag" in df.columns:

        df["high_leverage_flag"] = safe_numeric(
            df["high_leverage_flag"]
        ).fillna(0)

        print("\nUsing existing high_leverage_flag column.")

    elif "debt_to_equity" in df.columns:

        df["high_leverage_flag"] = np.where(
            df["debt_to_equity"] >= 2.0,
            1,
            0
        )

        print(
            "\nhigh_leverage_flag was missing."
            "\nCalculated from debt_to_equity >= 2.0."
        )

    else:

        df["high_leverage_flag"] = 0

        print(
            "\nWARNING:"
            "\nNeither high_leverage_flag nor debt_to_equity exists."
            "\nHigh leverage flag set to 0."
        )

    # -------------------------------------------------------------------------
    # Interest coverage
    # -------------------------------------------------------------------------

    if "interest_coverage" not in df.columns:

        if (
            "operating_profit" in df.columns
            and "interest" in df.columns
        ):

            df["interest_coverage"] = safe_divide(
                df["operating_profit"],
                df["interest"]
            )

        else:

            df["interest_coverage"] = np.nan

    # -------------------------------------------------------------------------
    # ROE
    # -------------------------------------------------------------------------

    if "roe_percentage" not in df.columns:

        if "roe_calculated" in df.columns:

            df["roe_percentage"] = df["roe_calculated"]

        elif (
            "net_profit" in df.columns
            and "reserves" in df.columns
        ):

            equity = (
                safe_numeric(df["equity_capital"])
                + safe_numeric(df["reserves"])
            )

            df["roe_percentage"] = safe_divide(
                df["net_profit"],
                equity
            ) * 100

        else:

            df["roe_percentage"] = np.nan

    # -------------------------------------------------------------------------
    # ROCE
    # -------------------------------------------------------------------------

    if "roce_percentage" not in df.columns:

        if "roce_calculated" in df.columns:

            df["roce_percentage"] = df["roce_calculated"]

        else:

            df["roce_percentage"] = np.nan

    # -------------------------------------------------------------------------
    # Net profit margin
    # -------------------------------------------------------------------------

    if "net_profit_margin_pct" not in df.columns:

        if (
            "net_profit" in df.columns
            and "sales" in df.columns
        ):

            df["net_profit_margin_pct"] = (
                safe_divide(
                    df["net_profit"],
                    df["sales"]
                ) * 100
            )

        else:

            df["net_profit_margin_pct"] = np.nan

    # -------------------------------------------------------------------------
    # FCF
    # -------------------------------------------------------------------------

    if "free_cash_flow" not in df.columns:

        df["free_cash_flow"] = np.nan

    # -------------------------------------------------------------------------
    # CAGR columns
    # -------------------------------------------------------------------------

    for col in [
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr"
    ]:

        if col not in df.columns:
            df[col] = np.nan

    print("\nPrepared financial data shape:", df.shape)

    return df


# =============================================================================
# LOAD FINANCIAL PROS / CONS
# =============================================================================

def load_financial_pros_cons():

    print_header("LOADING FINANCIAL PROS / CONS")

    if not os.path.exists(FINANCIAL_PROS_CONS):

        raise FileNotFoundError(
            f"Financial pros/cons file not found:\n"
            f"{FINANCIAL_PROS_CONS}"
        )

    df = pd.read_csv(FINANCIAL_PROS_CONS)

    print("FILE:")
    print(FINANCIAL_PROS_CONS)

    print("Shape:", df.shape)

    required = [
        "company_id",
        "type",
        "rule_id",
        "text",
        "confidence_pct"
    ]

    missing = [
        c for c in required
        if c not in df.columns
    ]

    if missing:

        raise ValueError(
            "Financial pros/cons missing columns: "
            + str(missing)
        )

    df["company_id"] = df["company_id"].apply(
        normalize_company_id
    )

    return df


# =============================================================================
# LOAD CASH FLOW PROS / CONS
# =============================================================================

def load_cashflow_pros_cons():

    print_header("LOADING CASH-FLOW PROS / CONS")

    if not os.path.exists(CASHFLOW_PROS_CONS):

        raise FileNotFoundError(
            f"Cash-flow pros/cons file not found:\n"
            f"{CASHFLOW_PROS_CONS}"
        )

    df = pd.read_csv(CASHFLOW_PROS_CONS)

    print("FILE:")
    print(CASHFLOW_PROS_CONS)

    print("Shape:", df.shape)

    required = [
        "company_id",
        "type",
        "rule_id",
        "text",
        "confidence_pct"
    ]

    missing = [
        c
        for c in required
        if c not in df.columns
    ]

    if missing:

        raise ValueError(
            "Cash-flow pros/cons missing columns: "
            + str(missing)
        )

    df["company_id"] = df["company_id"].apply(
        normalize_company_id
    )

    return df


# =============================================================================
# LOAD CAGR VALIDATION
# =============================================================================

def load_cagr_validation():

    print_header("LOADING CAGR CROSS-VALIDATION")

    if not os.path.exists(CAGR_VALIDATION):

        print(
            "WARNING: CAGR validation file not found."
        )

        return pd.DataFrame()

    df = pd.read_csv(CAGR_VALIDATION)

    print("FILE:")
    print(CAGR_VALIDATION)

    print("Shape:", df.shape)

    if "company_id" in df.columns:

        df["company_id"] = df["company_id"].apply(
            normalize_company_id
        )

    return df


# =============================================================================
# CREATE FINANCIAL SUMMARY
# =============================================================================

def create_financial_summary(df):

    print_header("CREATING FINANCIAL SUMMARY")

    rows = []

    for company_id, group in df.groupby(
        "company_id",
        dropna=True
    ):

        latest = group.iloc[-1]

        row = {
            "company_id": company_id,

            "latest_year": (
                latest["year"]
                if "year" in latest.index
                else None
            ),

            "roe": latest.get(
                "roe_percentage",
                np.nan
            ),

            "roce": latest.get(
                "roce_percentage",
                np.nan
            ),

            "debt_to_equity": latest.get(
                "debt_to_equity",
                np.nan
            ),

            "interest_coverage": latest.get(
                "interest_coverage",
                np.nan
            ),

            "net_profit_margin": latest.get(
                "net_profit_margin_pct",
                np.nan
            ),

            "revenue_cagr": latest.get(
                "revenue_cagr_5yr",
                np.nan
            ),

            "pat_cagr": latest.get(
                "pat_cagr_5yr",
                np.nan
            ),

            "eps_cagr": latest.get(
                "eps_cagr_5yr",
                np.nan
            ),

            "free_cash_flow": latest.get(
                "free_cash_flow",
                np.nan
            ),

            "high_leverage_flag": latest.get(
                "high_leverage_flag",
                0
            )
        }

        rows.append(row)

    result = pd.DataFrame(rows)

    print(
        "Financial summary shape:",
        result.shape
    )

    return result


# =============================================================================
# CREATE CASH-FLOW SUMMARY
# =============================================================================

def create_cashflow_summary(cashflow_df):

    print_header("CREATING CASH-FLOW SUMMARY")

    if cashflow_df.empty:

        return pd.DataFrame(
            columns=[
                "company_id",
                "cashflow_pros",
                "cashflow_cons",
                "cashflow_total"
            ]
        )

    rows = []

    for company_id, group in cashflow_df.groupby(
        "company_id",
        dropna=True
    ):

        pros = int(
            (group["type"].str.lower() == "pro").sum()
        )

        cons = int(
            (group["type"].str.lower() == "con").sum()
        )

        rows.append(
            {
                "company_id": company_id,
                "cashflow_pros": pros,
                "cashflow_cons": cons,
                "cashflow_total": pros + cons
            }
        )

    result = pd.DataFrame(rows)

    print(
        "Cash-flow summary shape:",
        result.shape
    )

    return result


# =============================================================================
# CREATE FINANCIAL PROS / CONS SUMMARY
# =============================================================================

def create_pros_cons_summary(df):

    print_header("CREATING FINANCIAL PROS / CONS SUMMARY")

    if df.empty:

        return pd.DataFrame(
            columns=[
                "company_id",
                "financial_pros",
                "financial_cons",
                "financial_total"
            ]
        )

    rows = []

    for company_id, group in df.groupby(
        "company_id",
        dropna=True
    ):

        pros = int(
            (group["type"].str.lower() == "pro").sum()
        )

        cons = int(
            (group["type"].str.lower() == "con").sum()
        )

        rows.append(
            {
                "company_id": company_id,
                "financial_pros": pros,
                "financial_cons": cons,
                "financial_total": pros + cons
            }
        )

    result = pd.DataFrame(rows)

    print(
        "Financial pros/cons summary shape:",
        result.shape
    )

    return result


# =============================================================================
# CREATE CAGR SUMMARY
# =============================================================================

def create_cagr_summary(df):

    print_header("CREATING CAGR SUMMARY")

    if df.empty:

        return pd.DataFrame(
            columns=[
                "company_id",
                "cagr_manual_review"
            ]
        )

    if "manual_review" not in df.columns:

        return pd.DataFrame(
            columns=[
                "company_id",
                "cagr_manual_review"
            ]
        )

    result = (
        df.groupby("company_id", dropna=True)
        ["manual_review"]
        .max()
        .reset_index()
    )

    result = result.rename(
        columns={
            "manual_review":
            "cagr_manual_review"
        }
    )

    result["cagr_manual_review"] = (
        result["cagr_manual_review"]
        .fillna(False)
        .astype(bool)
    )

    print(
        "CAGR summary shape:",
        result.shape
    )

    return result


# =============================================================================
# GENERATE INSIGHT TEXT
# =============================================================================

def generate_insight(row):

    company = row["company_id"]

    financial_pros = int(
        row.get("financial_pros", 0)
    )

    financial_cons = int(
        row.get("financial_cons", 0)
    )

    cashflow_pros = int(
        row.get("cashflow_pros", 0)
    )

    cashflow_cons = int(
        row.get("cashflow_cons", 0)
    )

    total_pros = (
        financial_pros +
        cashflow_pros
    )

    total_cons = (
        financial_cons +
        cashflow_cons
    )

    roe = row.get("roe", np.nan)
    roce = row.get("roce", np.nan)
    debt = row.get("debt_to_equity", np.nan)
    icr = row.get("interest_coverage", np.nan)
    revenue_cagr = row.get("revenue_cagr", np.nan)
    pat_cagr = row.get("pat_cagr", np.nan)
    fcf = row.get("free_cash_flow", np.nan)

    messages = []

    # -------------------------------------------------------------------------
    # ROE
    # -------------------------------------------------------------------------

    if pd.notna(roe):

        if roe >= 20:

            messages.append(
                f"{company} demonstrates strong return on equity "
                f"of {roe:.2f}%."
            )

        elif roe < 10:

            messages.append(
                f"{company} has relatively low return on equity "
                f"of {roe:.2f}%."
            )

    # -------------------------------------------------------------------------
    # ROCE
    # -------------------------------------------------------------------------

    if pd.notna(roce):

        if roce >= 15:

            messages.append(
                f"Return on capital employed is healthy at "
                f"{roce:.2f}%."
            )

        elif roce < 10:

            messages.append(
                f"Return on capital employed is relatively weak "
                f"at {roce:.2f}%."
            )

    # -------------------------------------------------------------------------
    # DEBT
    # -------------------------------------------------------------------------

    if pd.notna(debt):

        if debt >= 2:

            messages.append(
                f"Debt-to-equity of {debt:.2f} indicates elevated "
                f"leverage."
            )

        elif debt <= 0.5:

            messages.append(
                f"Debt-to-equity of {debt:.2f} indicates relatively "
                f"low financial leverage."
            )

    # -------------------------------------------------------------------------
    # INTEREST COVERAGE
    # -------------------------------------------------------------------------

    if pd.notna(icr):

        if icr >= 5:

            messages.append(
                f"Interest coverage of {icr:.2f}x indicates strong "
                f"ability to service interest obligations."
            )

        elif icr < 2:

            messages.append(
                f"Interest coverage of {icr:.2f}x indicates potential "
                f"debt-servicing pressure."
            )

    # -------------------------------------------------------------------------
    # REVENUE CAGR
    # -------------------------------------------------------------------------

    if pd.notna(revenue_cagr):

        if revenue_cagr >= 15:

            messages.append(
                f"Five-year revenue CAGR of {revenue_cagr:.2f}% "
                f"indicates strong growth."
            )

        elif revenue_cagr < 5:

            messages.append(
                f"Five-year revenue CAGR of {revenue_cagr:.2f}% "
                f"indicates relatively slow growth."
            )

    # -------------------------------------------------------------------------
    # PAT CAGR
    # -------------------------------------------------------------------------

    if pd.notna(pat_cagr):

        if pat_cagr >= 15:

            messages.append(
                f"Five-year profit CAGR of {pat_cagr:.2f}% "
                f"indicates strong earnings growth."
            )

        elif pat_cagr < 5:

            messages.append(
                f"Five-year profit CAGR of {pat_cagr:.2f}% "
                f"indicates relatively weak earnings growth."
            )

    # -------------------------------------------------------------------------
    # FCF
    # -------------------------------------------------------------------------

    if pd.notna(fcf):

        if fcf > 0:

            messages.append(
                f"Latest free cash flow is positive at {fcf:.2f}, "
                f"supporting internal cash generation."
            )

        elif fcf < 0:

            messages.append(
                f"Latest free cash flow is negative at {fcf:.2f}, "
                f"indicating cash-generation pressure."
            )

    # -------------------------------------------------------------------------
    # PRO / CON BALANCE
    # -------------------------------------------------------------------------

    if total_pros > total_cons:

        messages.append(
            f"Overall, the available analysis shows more positive "
            f"signals ({total_pros}) than negative signals ({total_cons})."
        )

    elif total_cons > total_pros:

        messages.append(
            f"Overall, the available analysis shows more negative "
            f"signals ({total_cons}) than positive signals ({total_pros})."
        )

    else:

        messages.append(
            f"Overall, positive and negative signals are balanced "
            f"at {total_pros} each."
        )

    return " ".join(messages)


# =============================================================================
# CREATE UNIFIED INSIGHTS
# =============================================================================

def create_unified_insights(
    financial_summary,
    financial_pros_summary,
    cashflow_summary,
    cagr_summary
):

    print_header("CREATING UNIFIED INVESTMENT INSIGHTS")

    # -------------------------------------------------------------------------
    # Start with financial summary
    # -------------------------------------------------------------------------

    unified = financial_summary.copy()

    # -------------------------------------------------------------------------
    # Merge financial pros/cons
    # -------------------------------------------------------------------------

    unified = unified.merge(
        financial_pros_summary,
        on="company_id",
        how="left"
    )

    # -------------------------------------------------------------------------
    # Merge cash-flow pros/cons
    # -------------------------------------------------------------------------

    unified = unified.merge(
        cashflow_summary,
        on="company_id",
        how="left"
    )

    # -------------------------------------------------------------------------
    # Merge CAGR validation
    # -------------------------------------------------------------------------

    unified = unified.merge(
        cagr_summary,
        on="company_id",
        how="left"
    )

    # -------------------------------------------------------------------------
    # Fill missing counts
    # -------------------------------------------------------------------------

    count_columns = [
        "financial_pros",
        "financial_cons",
        "financial_total",
        "cashflow_pros",
        "cashflow_cons",
        "cashflow_total"
    ]

    for col in count_columns:

        if col not in unified.columns:
            unified[col] = 0

        unified[col] = (
            pd.to_numeric(
                unified[col],
                errors="coerce"
            )
            .fillna(0)
            .astype(int)
        )

    # -------------------------------------------------------------------------
    # CAGR review
    # -------------------------------------------------------------------------

    if "cagr_manual_review" not in unified.columns:

        unified["cagr_manual_review"] = False

    unified["cagr_manual_review"] = (
        unified["cagr_manual_review"]
        .fillna(False)
        .astype(bool)
    )

    # -------------------------------------------------------------------------
    # Total pros / cons
    # -------------------------------------------------------------------------

    unified["total_pros"] = (
        unified["financial_pros"]
        + unified["cashflow_pros"]
    )

    unified["total_cons"] = (
        unified["financial_cons"]
        + unified["cashflow_cons"]
    )

    unified["total_signals"] = (
        unified["total_pros"]
        + unified["total_cons"]
    )

    # -------------------------------------------------------------------------
    # Signal balance
    # -------------------------------------------------------------------------

    unified["signal_balance"] = (
        unified["total_pros"]
        - unified["total_cons"]
    )

    # -------------------------------------------------------------------------
    # Signal classification
    # -------------------------------------------------------------------------

    unified["signal_class"] = np.select(
        [
            unified["signal_balance"] >= 5,
            unified["signal_balance"] >= 2,
            unified["signal_balance"] <= -5,
            unified["signal_balance"] <= -2
        ],
        [
            "Strong Positive",
            "Positive",
            "Strong Negative",
            "Negative"
        ],
        default="Balanced"
    )

    # -------------------------------------------------------------------------
    # Leverage classification
    #
    # This does NOT depend on high_leverage_flag.
    # -------------------------------------------------------------------------

    unified["leverage_class"] = np.select(
        [
            unified["debt_to_equity"] >= 2,
            unified["debt_to_equity"] >= 1
        ],
        [
            "High Leverage",
            "Moderate Leverage"
        ],
        default="Low Leverage"
    )

    # -------------------------------------------------------------------------
    # Growth classification
    # -------------------------------------------------------------------------

    unified["growth_class"] = np.select(
        [
            (
                unified["revenue_cagr"] >= 15
            ) &
            (
                unified["pat_cagr"] >= 15
            ),

            (
                unified["revenue_cagr"] >= 10
            ) |
            (
                unified["pat_cagr"] >= 10
            ),

            (
                unified["revenue_cagr"] < 5
            ) &
            (
                unified["pat_cagr"] < 5
            )
        ],
        [
            "High Growth",
            "Moderate Growth",
            "Low Growth"
        ],
        default="Mixed Growth"
    )

    # -------------------------------------------------------------------------
    # Cash-flow classification
    # -------------------------------------------------------------------------

    unified["cashflow_signal"] = np.select(
        [
            unified["cashflow_pros"]
            > unified["cashflow_cons"],

            unified["cashflow_cons"]
            > unified["cashflow_pros"]
        ],
        [
            "Positive Cash Flow Signals",
            "Negative Cash Flow Signals"
        ],
        default="Balanced Cash Flow Signals"
    )

    # -------------------------------------------------------------------------
    # Overall classification
    # -------------------------------------------------------------------------

    unified["overall_class"] = np.select(
        [
            (
                unified["signal_balance"] >= 5
            ) &
            (
                unified["leverage_class"]
                == "Low Leverage"
            ),

            unified["signal_balance"] >= 2,

            unified["signal_balance"] <= -5,

            unified["signal_balance"] <= -2
        ],
        [
            "Strong Positive",
            "Positive",
            "Strong Negative",
            "Negative"
        ],
        default="Balanced"
    )

    # -------------------------------------------------------------------------
    # Generate natural-language insight
    # -------------------------------------------------------------------------

    unified["unified_insight"] = unified.apply(
        generate_insight,
        axis=1
    )

    # -------------------------------------------------------------------------
    # Manual review flag
    # -------------------------------------------------------------------------

    unified["manual_review"] = (
        unified["cagr_manual_review"]
    )

    # -------------------------------------------------------------------------
    # Sort
    # -------------------------------------------------------------------------

    unified = unified.sort_values(
        by=[
            "signal_balance",
            "total_pros"
        ],
        ascending=[
            False,
            False
        ]
    )

    unified = unified.reset_index(drop=True)

    return unified


# =============================================================================
# VALIDATION
# =============================================================================

def validate_output(df):

    print_header("VALIDATION")

    print("Total rows:", len(df))

    print(
        "Companies:",
        df["company_id"].nunique()
    )

    # -------------------------------------------------------------------------
    # Required columns
    # -------------------------------------------------------------------------

    required_columns = [
        "company_id",
        "financial_pros",
        "financial_cons",
        "cashflow_pros",
        "cashflow_cons",
        "total_pros",
        "total_cons",
        "signal_balance",
        "signal_class",
        "leverage_class",
        "growth_class",
        "cashflow_signal",
        "overall_class",
        "unified_insight"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:

        print(
            "\nMISSING REQUIRED COLUMNS:"
        )

        for col in missing:
            print("-", col)

        raise ValueError(
            "Validation failed because required columns are missing."
        )

    print("\nRequired columns: PASSED")

    # -------------------------------------------------------------------------
    # Missing company IDs
    # -------------------------------------------------------------------------

    missing_company = df["company_id"].isna().sum()

    print(
        "Missing company_id:",
        missing_company
    )

    # -------------------------------------------------------------------------
    # Duplicate company rows
    # -------------------------------------------------------------------------

    duplicate_companies = (
        df["company_id"]
        .duplicated()
        .sum()
    )

    print(
        "Duplicate company rows:",
        duplicate_companies
    )

    # -------------------------------------------------------------------------
    # Empty insights
    # -------------------------------------------------------------------------

    empty_insights = (
        df["unified_insight"]
        .fillna("")
        .str.strip()
        .eq("")
        .sum()
    )

    print(
        "Empty unified insights:",
        empty_insights
    )

    # -------------------------------------------------------------------------
    # Signal class counts
    # -------------------------------------------------------------------------

    print("\nSIGNAL CLASS COUNTS:")

    print(
        df["signal_class"]
        .value_counts()
        .to_string()
    )

    # -------------------------------------------------------------------------
    # Overall class counts
    # -------------------------------------------------------------------------

    print("\nOVERALL CLASS COUNTS:")

    print(
        df["overall_class"]
        .value_counts()
        .to_string()
    )

    # -------------------------------------------------------------------------
    # Manual review
    # -------------------------------------------------------------------------

    print(
        "\nManual review:",
        int(df["manual_review"].sum())
    )

    if (
        missing_company == 0
        and empty_insights == 0
        and duplicate_companies == 0
    ):

        print("\nVALIDATION PASSED")

    else:

        print("\nVALIDATION WARNING")


# =============================================================================
# MAIN
# =============================================================================

def main():

    print_header(
        "DAY 32 — UNIFIED INVESTMENT INSIGHTS GENERATOR"
    )

    print("PROJECT ROOT:")
    print(PROJECT_ROOT)

    print("\nFINANCIAL PROS / CONS:")
    print(FINANCIAL_PROS_CONS)
    print(
        "EXISTS:",
        os.path.exists(FINANCIAL_PROS_CONS)
    )

    print("\nCASH-FLOW PROS / CONS:")
    print(CASHFLOW_PROS_CONS)
    print(
        "EXISTS:",
        os.path.exists(CASHFLOW_PROS_CONS)
    )

    print("\nCAGR CROSS-VALIDATION:")
    print(CAGR_VALIDATION)
    print(
        "EXISTS:",
        os.path.exists(CAGR_VALIDATION)
    )

    print("\nDATABASE:")
    print(DB_PATH)
    print(
        "EXISTS:",
        os.path.exists(DB_PATH)
    )

    # -------------------------------------------------------------------------
    # Load files
    # -------------------------------------------------------------------------

    financial_pros_cons = (
        load_financial_pros_cons()
    )

    cashflow_pros_cons = (
        load_cashflow_pros_cons()
    )

    cagr_validation = (
        load_cagr_validation()
    )

    financial_db, valuation, peer = (
        load_financial_database()
    )

    # -------------------------------------------------------------------------
    # Prepare database
    # -------------------------------------------------------------------------

    financial_db = prepare_financial_data(
        financial_db
    )

    # -------------------------------------------------------------------------
    # Create summaries
    # -------------------------------------------------------------------------

    financial_summary = (
        create_financial_summary(
            financial_db
        )
    )

    financial_pros_summary = (
        create_pros_cons_summary(
            financial_pros_cons
        )
    )

    cashflow_summary = (
        create_cashflow_summary(
            cashflow_pros_cons
        )
    )

    cagr_summary = (
        create_cagr_summary(
            cagr_validation
        )
    )

    # -------------------------------------------------------------------------
    # Create unified output
    # -------------------------------------------------------------------------

    unified = create_unified_insights(
        financial_summary,
        financial_pros_summary,
        cashflow_summary,
        cagr_summary
    )

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    validate_output(
        unified
    )

    # -------------------------------------------------------------------------
    # Save
    # -------------------------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    unified.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print_header(
        "OUTPUT SAVED"
    )

    print(
        OUTPUT_FILE
    )

    print(
        "\nRows:",
        len(unified)
    )

    print(
        "Companies:",
        unified["company_id"].nunique()
    )

    print("\nFIRST 15 ROWS:")

    display_columns = [
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

    print(
        unified[
            display_columns
        ]
        .head(15)
        .to_string(index=False)
    )

    print_header(
        "DAY 32 COMPLETED SUCCESSFULLY"
    )


if __name__ == "__main__":
    main()