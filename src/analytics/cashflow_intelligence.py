from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd


# ============================================================
# DAY 31 — CASH FLOW INTELLIGENCE MODULE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_CASHFLOW = PROJECT_ROOT / "data" / "raw" / "cashflow.xlsx"
DATABASE = PROJECT_ROOT / "database" / "financial_data.db"

OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INTELLIGENCE_OUTPUT = OUTPUT_DIR / "cashflow_intelligence.xlsx"
DISTRESS_OUTPUT = OUTPUT_DIR / "distress_alerts.csv"


# ============================================================
# LOAD CASH FLOW DATA
# ============================================================

def load_cashflow():

    if not RAW_CASHFLOW.exists():
        raise FileNotFoundError(
            f"Cash-flow file not found: {RAW_CASHFLOW}"
        )

    df = pd.read_excel(
        RAW_CASHFLOW,
        sheet_name="Cash Flow",
        header=1
    )

    required = [
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ]

    missing = [c for c in required if c not in df.columns]

    if missing:
        raise ValueError(
            f"Missing cash-flow columns: {missing}"
        )

    return df


# ============================================================
# LOAD FINANCIAL DATA
# ============================================================

def load_financial_data():

    if not DATABASE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE}"
        )

    conn = sqlite3.connect(DATABASE)

    query = """
        SELECT
            company_id,
            year,
            sales,
            net_profit,
            borrowings
        FROM financial_ratios
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


# ============================================================
# CLEAN YEAR
# ============================================================

def clean_year(value):

    if pd.isna(value):
        return None

    value = str(value).strip()

    # Convert formats such as Mar-24 / Mar 2024 / Dec 2012
    try:
        dt = pd.to_datetime(value, errors="coerce")

        if not pd.isna(dt):
            return dt.year
    except Exception:
        pass

    # Extract four-digit year if possible
    import re

    match = re.search(r"(20\d{2}|19\d{2})", value)

    if match:
        return int(match.group(1))

    return None


# ============================================================
# CAPITAL ALLOCATION CLASSIFICATION
# ============================================================

def classify_capital_allocation(row):

    cfo = row["operating_activity"]
    cfi = row["investing_activity"]
    cff = row["financing_activity"]
    fcf = row["free_cash_flow"]

    if pd.isna(cfo):
        return "Other"

    # Distress
    if cfo < 0 and cff > 0:
        return "Distress Signal"

    # Growth funded by debt
    if fcf < 0 and cff > 0:
        return "Growth Funded by Debt"

    # Liquidating assets
    if cfo > 0 and cfi > 0:
        return "Liquidating Assets"

    # Cash accumulator
    if cfo > 0 and cfi == 0 and cff <= 0:
        return "Cash Accumulator"

    # Reinvestor
    if cfo > 0 and cfi < 0:
        return "Reinvestor"

    # Pre-revenue / weak operations
    if cfo <= 0 and cfi <= 0 and cff <= 0:
        return "Pre-Revenue"

    return "Mixed"


# ============================================================
# CFO QUALITY
# ============================================================

def cfo_quality_label(score):

    if pd.isna(score):
        return "Accrual Risk"

    if score > 1.0:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


# ============================================================
# CAPEX LABEL
# ============================================================

def capex_label(value):

    if pd.isna(value):
        return "Unknown"

    if value < 3:
        return "Asset Light"

    if value <= 8:
        return "Moderate"

    return "Capital Intensive"


# ============================================================
# FCF CAGR
# ============================================================

def calculate_fcf_cagr(group):

    group = group.sort_values("year")

    if len(group) < 6:
        return np.nan

    latest = group.iloc[-1]
    previous = group.iloc[-6]

    start = previous["free_cash_flow"]
    end = latest["free_cash_flow"]

    if pd.isna(start) or pd.isna(end):
        return np.nan

    if start <= 0 or end <= 0:
        return np.nan

    years = latest["year"] - previous["year"]

    if years <= 0:
        return np.nan

    return ((end / start) ** (1 / years) - 1) * 100


# ============================================================
# MAIN CALCULATION
# ============================================================

def build_intelligence():

    print("\n# DAY 31 — CASH FLOW INTELLIGENCE")

    print(f"\nPROJECT ROOT:\n{PROJECT_ROOT}")

    print("\nLOADING CASH FLOW...")
    cashflow = load_cashflow()

    print("Cash-flow shape:", cashflow.shape)

    print("\nLOADING FINANCIAL DATA...")
    financial = load_financial_data()

    print("Financial shape:", financial.shape)

    # --------------------------------------------------------
    # Clean years
    # --------------------------------------------------------

    cashflow["year_clean"] = cashflow["year"].apply(clean_year)
    financial["year_clean"] = financial["year"].apply(clean_year)

    cashflow["year"] = cashflow["year_clean"]
    financial["year"] = financial["year_clean"]

    cashflow.drop(columns=["year_clean"], inplace=True)
    financial.drop(columns=["year_clean"], inplace=True)

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    cash_cols = [
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow"
    ]

    for col in cash_cols:
        cashflow[col] = pd.to_numeric(
            cashflow[col],
            errors="coerce"
        )

    financial_cols = [
        "sales",
        "net_profit",
        "borrowings"
    ]

    for col in financial_cols:
        financial[col] = pd.to_numeric(
            financial[col],
            errors="coerce"
        )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    df = pd.merge(
        cashflow,
        financial,
        on=["company_id", "year"],
        how="left"
    )

    # --------------------------------------------------------
    # Free Cash Flow
    # --------------------------------------------------------

    df["free_cash_flow"] = (
        df["operating_activity"]
        + df["investing_activity"]
    )

    # --------------------------------------------------------
    # CFO / PAT
    # --------------------------------------------------------

    df["cfo_pat_ratio"] = np.where(
        df["net_profit"] != 0,
        df["operating_activity"] / df["net_profit"],
        np.nan
    )

    # --------------------------------------------------------
    # 5-year average CFO quality
    # --------------------------------------------------------

    df = df.sort_values(
        ["company_id", "year"]
    )

    df["cfo_quality_score"] = (
        df.groupby("company_id")["cfo_pat_ratio"]
        .transform(
            lambda x: x.rolling(
                window=5,
                min_periods=1
            ).mean()
        )
    )

    df["cfo_quality_label"] = (
        df["cfo_quality_score"]
        .apply(cfo_quality_label)
    )

    # --------------------------------------------------------
    # CapEx intensity
    # --------------------------------------------------------

    df["capex_intensity_pct"] = np.where(
        df["sales"] != 0,
        abs(df["investing_activity"]) /
        df["sales"] * 100,
        np.nan
    )

    df["capex_label"] = (
        df["capex_intensity_pct"]
        .apply(capex_label)
    )

    # --------------------------------------------------------
    # FCF conversion
    # --------------------------------------------------------

    df["fcf_conversion_pct"] = np.where(
        df["net_profit"] != 0,
        df["free_cash_flow"] /
        df["net_profit"] * 100,
        np.nan
    )

    # --------------------------------------------------------
    # Distress flag
    # --------------------------------------------------------

    df["distress_flag"] = (
        (df["operating_activity"] < 0)
        &
        (df["financing_activity"] > 0)
    )

    # --------------------------------------------------------
    # Deleveraging flag
    # --------------------------------------------------------

    df["previous_borrowings"] = (
        df.groupby("company_id")["borrowings"]
        .shift(1)
    )

    df["deleveraging_flag"] = (
        (df["financing_activity"] < 0)
        &
        (
            df["borrowings"]
            <
            df["previous_borrowings"]
        )
    )

    # --------------------------------------------------------
    # Capital allocation
    # --------------------------------------------------------

    df["capital_allocation_label"] = (
        df.apply(
            classify_capital_allocation,
            axis=1
        )
    )

    # --------------------------------------------------------
    # FCF CAGR
    # --------------------------------------------------------

    fcf_cagr = (
        df.groupby("company_id")
        .apply(
            calculate_fcf_cagr,
            include_groups=False
        )
        .rename("fcf_cagr_5yr")
        .reset_index()
    )

    df = df.merge(
        fcf_cagr,
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------
    # Latest year per company
    # --------------------------------------------------------

    latest = (
        df.sort_values(["company_id", "year"])
        .groupby("company_id")
        .tail(1)
        .copy()
    )

    # --------------------------------------------------------
    # Required output columns
    # --------------------------------------------------------

    output = latest[
        [
            "company_id",
            "cfo_quality_score",
            "cfo_quality_label",
            "capex_intensity_pct",
            "capex_label",
            "fcf_cagr_5yr",
            "fcf_conversion_pct",
            "distress_flag",
            "deleveraging_flag",
            "capital_allocation_label",
            "operating_activity",
            "financing_activity",
            "net_profit",
            "year",
        ]
    ].copy()

    # --------------------------------------------------------
    # Distress alerts
    # --------------------------------------------------------

    distress = output[
        output["distress_flag"] == True
    ].copy()

    distress = distress[
        [
            "company_id",
            "year",
            "operating_activity",
            "financing_activity",
            "net_profit"
        ]
    ]

    # --------------------------------------------------------
    # Save Excel
    # --------------------------------------------------------

    with pd.ExcelWriter(
        INTELLIGENCE_OUTPUT,
        engine="openpyxl"
    ) as writer:

        output.to_excel(
            writer,
            sheet_name="cashflow_intelligence",
            index=False
        )

        df.to_excel(
            writer,
            sheet_name="yearly_details",
            index=False
        )

    # --------------------------------------------------------
    # Save distress CSV
    # --------------------------------------------------------

    distress.to_csv(
        DISTRESS_OUTPUT,
        index=False
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    print("\n# VALIDATION")

    print("Companies:", output["company_id"].nunique())
    print("Rows:", len(output))

    print(
        "\nCFO QUALITY COUNTS:"
    )
    print(
        output["cfo_quality_label"]
        .value_counts(dropna=False)
    )

    print(
        "\nCAPEX LABEL COUNTS:"
    )
    print(
        output["capex_label"]
        .value_counts(dropna=False)
    )

    print(
        "\nCAPITAL ALLOCATION COUNTS:"
    )
    print(
        output["capital_allocation_label"]
        .value_counts(dropna=False)
    )

    print(
        "\nDISTRESS ALERTS:",
        len(distress)
    )

    print(
        "\nDELEVERAGING FLAGS:",
        int(output["deleveraging_flag"].sum())
    )

    print("\nOUTPUT:")
    print(INTELLIGENCE_OUTPUT)

    print("\nDISTRESS OUTPUT:")
    print(DISTRESS_OUTPUT)

    return output


if __name__ == "__main__":
    build_intelligence()