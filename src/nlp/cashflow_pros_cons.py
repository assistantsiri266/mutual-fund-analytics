import os
import pandas as pd


# ============================================================
# DAY 31 — CASH FLOW BASED PROS / CONS GENERATOR
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "output",
    "cashflow_kpis.csv"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "output",
    "cashflow_pros_cons.csv"
)


def clean_number(value):
    """Safely convert value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def add_row(rows, company_id, row_type, rule_id, text, confidence):
    """Add one pros/cons row."""

    rows.append({
        "company_id": company_id,
        "type": row_type,
        "rule_id": rule_id,
        "text": text,
        "confidence_pct": round(float(confidence), 2)
    })


def generate_company_rules(company_id, df):
    """
    Generate cash-flow based pros and cons for one company.
    """

    rows = []

    # --------------------------------------------------------
    # Aggregate company-level information
    # --------------------------------------------------------

    latest = df.iloc[-1]

    avg_fcf = pd.to_numeric(
        df["free_cash_flow"],
        errors="coerce"
    ).mean()

    negative_fcf_count = (
        pd.to_numeric(
            df["free_cash_flow"],
            errors="coerce"
        ) < 0
    ).sum()

    total_periods = len(df)

    high_quality_count = (
        df["cfo_quality"] == "High Quality"
    ).sum()

    accrual_risk_count = (
        df["cfo_quality"] == "Accrual Risk"
    ).sum()

    capital_intensive_count = (
        df["capex_label"] == "Capital Intensive"
    ).sum()

    asset_light_count = (
        df["capex_label"] == "Asset Light"
    ).sum()

    growth_debt_count = (
        df["pattern_label"] == "Growth Funded by Debt"
    ).sum()

    distress_count = (
        df["pattern_label"] == "Distress Signal"
    ).sum()

    liquidating_count = (
        df["pattern_label"] == "Liquidating Assets"
    ).sum()

    # --------------------------------------------------------
    # Latest values
    # --------------------------------------------------------

    latest_fcf = clean_number(
        latest.get("free_cash_flow")
    )

    latest_fcf_conversion = clean_number(
        latest.get("fcf_conversion")
    )

    latest_cfo_quality = latest.get(
        "cfo_quality"
    )

    latest_capex_label = latest.get(
        "capex_label"
    )

    latest_pattern = latest.get(
        "pattern_label"
    )

    # --------------------------------------------------------
    # PRO 1 — High quality CFO
    # --------------------------------------------------------

    if high_quality_count > 0:

        confidence = min(
            75 + (high_quality_count / total_periods) * 25,
            95
        )

        add_row(
            rows,
            company_id,
            "pro",
            "CF_PRO_01",
            f"Operating cash flow quality was High Quality in "
            f"{high_quality_count} of {total_periods} periods, "
            f"indicating strong cash support for reported earnings",
            confidence
        )

    # --------------------------------------------------------
    # PRO 2 — Positive FCF
    # --------------------------------------------------------

    positive_fcf_count = (
        pd.to_numeric(
            df["free_cash_flow"],
            errors="coerce"
        ) > 0
    ).sum()

    if positive_fcf_count > 0:

        confidence = min(
            70 + (positive_fcf_count / total_periods) * 25,
            95
        )

        add_row(
            rows,
            company_id,
            "pro",
            "CF_PRO_02",
            f"Free cash flow was positive in "
            f"{positive_fcf_count} of {total_periods} periods, "
            f"supporting internal cash generation",
            confidence
        )

    # --------------------------------------------------------
    # PRO 3 — Asset Light
    # --------------------------------------------------------

    if asset_light_count > 0:

        confidence = min(
            72 + (asset_light_count / total_periods) * 20,
            92
        )

        add_row(
            rows,
            company_id,
            "pro",
            "CF_PRO_03",
            f"Asset-light cash-flow characteristics appeared in "
            f"{asset_light_count} periods, suggesting relatively "
            f"lower capital expenditure intensity",
            confidence
        )

    # --------------------------------------------------------
    # PRO 4 — Strong FCF conversion
    # --------------------------------------------------------

    if (
        latest_fcf_conversion is not None
        and latest_fcf_conversion >= 50
    ):

        confidence = min(
            75 + latest_fcf_conversion / 10,
            95
        )

        add_row(
            rows,
            company_id,
            "pro",
            "CF_PRO_04",
            f"Latest free-cash-flow conversion was "
            f"{latest_fcf_conversion:.2f}%, indicating strong "
            f"conversion of reported profit into free cash flow",
            confidence
        )

    # --------------------------------------------------------
    # PRO 5 — Positive average FCF
    # --------------------------------------------------------

    if avg_fcf > 0:

        add_row(
            rows,
            company_id,
            "pro",
            "CF_PRO_05",
            f"Average free cash flow was positive at "
            f"{avg_fcf:.2f}, indicating positive cash generation "
            f"across the available periods",
            78
        )

    # --------------------------------------------------------
    # CON 1 — Accrual Risk
    # --------------------------------------------------------

    if accrual_risk_count > 0:

        confidence = min(
            70 + (accrual_risk_count / total_periods) * 30,
            95
        )

        add_row(
            rows,
            company_id,
            "con",
            "CF_CON_01",
            f"Accrual Risk was observed in "
            f"{accrual_risk_count} of {total_periods} periods, "
            f"indicating that reported earnings were not always "
            f"strongly supported by operating cash flow",
            confidence
        )

    # --------------------------------------------------------
    # CON 2 — Negative FCF
    # --------------------------------------------------------

    if negative_fcf_count > 0:

        confidence = min(
            68 + (negative_fcf_count / total_periods) * 25,
            94
        )

        add_row(
            rows,
            company_id,
            "con",
            "CF_CON_02",
            f"Negative free cash flow occurred in "
            f"{negative_fcf_count} of {total_periods} periods, "
            f"indicating periods of cash-generation pressure",
            confidence
        )

    # --------------------------------------------------------
    # CON 3 — Capital Intensive
    # --------------------------------------------------------

    if capital_intensive_count > 0:

        confidence = min(
            70 + (capital_intensive_count / total_periods) * 20,
            92
        )

        add_row(
            rows,
            company_id,
            "con",
            "CF_CON_03",
            f"Capital-intensive cash-flow characteristics appeared "
            f"in {capital_intensive_count} periods, indicating "
            f"higher investment requirements",
            confidence
        )

    # --------------------------------------------------------
    # CON 4 — Growth Funded by Debt
    # --------------------------------------------------------

    if growth_debt_count > 0:

        confidence = min(
            75 + (growth_debt_count / total_periods) * 20,
            95
        )

        add_row(
            rows,
            company_id,
            "con",
            "CF_CON_04",
            f"Growth funded by debt was observed in "
            f"{growth_debt_count} periods, indicating reliance "
            f"on debt financing for growth",
            confidence
        )

    # --------------------------------------------------------
    # CON 5 — Distress Signal
    # --------------------------------------------------------

    if distress_count > 0:

        confidence = min(
            80 + (distress_count / total_periods) * 15,
            95
        )

        add_row(
            rows,
            company_id,
            "con",
            "CF_CON_05",
            f"Distress Signal patterns appeared in "
            f"{distress_count} periods, indicating potential "
            f"cash-flow stress that should be monitored",
            confidence
        )

    # --------------------------------------------------------
    # CON 6 — Liquidating Assets
    # --------------------------------------------------------

    if liquidating_count > 0:

        confidence = min(
            72 + (liquidating_count / total_periods) * 20,
            92
        )

        add_row(
            rows,
            company_id,
            "con",
            "CF_CON_06",
            f"Liquidating Assets patterns appeared in "
            f"{liquidating_count} periods, indicating that "
            f"asset sales may have contributed to cash generation",
            confidence
        )

    # --------------------------------------------------------
    # Latest cash-flow warning
    # --------------------------------------------------------

    if (
        latest_fcf is not None
        and latest_fcf < 0
    ):

        add_row(
            rows,
            company_id,
            "con",
            "CF_CON_07",
            f"Latest free cash flow was negative at "
            f"{latest_fcf:.2f}, indicating current cash-generation "
            f"pressure",
            88
        )

    # --------------------------------------------------------
    # Latest high-quality CFO
    # --------------------------------------------------------

    if latest_cfo_quality == "High Quality":

        add_row(
            rows,
            company_id,
            "pro",
            "CF_PRO_06",
            "Latest operating cash-flow quality is High Quality, "
            "providing strong cash-flow support for current earnings",
            90
        )

    # --------------------------------------------------------
    # Latest capital intensity warning
    # --------------------------------------------------------

    if latest_capex_label == "Capital Intensive":

        add_row(
            rows,
            company_id,
            "con",
            "CF_CON_08",
            "Latest period is classified as Capital Intensive, "
            "indicating relatively high capital expenditure requirements",
            85
        )

    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------

    if not any(r["type"] == "pro" for r in rows):

        add_row(
            rows,
            company_id,
            "pro",
            "CF_FALLBACK_PRO",
            "Cash-flow indicators provide useful information for "
            "assessing the company's financial strength",
            70
        )

    if not any(r["type"] == "con" for r in rows):

        add_row(
            rows,
            company_id,
            "con",
            "CF_FALLBACK_CON",
            "Cash-flow trends should continue to be monitored "
            "for changes in financial quality",
            70
        )

    return rows


def validate_output(df):

    print("\n" + "=" * 80)
    print("VALIDATION")
    print("=" * 80)

    print("Total rows:", len(df))
    print("Companies:", df["company_id"].nunique())

    print("\nTYPE COUNTS:")
    print(df["type"].value_counts())

    print(
        "\nConfidence <= 60:",
        (df["confidence_pct"] <= 60).sum()
    )

    companies = sorted(
        df["company_id"].unique()
    )

    missing_pro = []
    missing_con = []

    for company in companies:

        company_df = df[
            df["company_id"] == company
        ]

        if not (company_df["type"] == "pro").any():
            missing_pro.append(company)

        if not (company_df["type"] == "con").any():
            missing_con.append(company)

    print("\nCompanies missing PRO:")
    print(missing_pro)

    print("\nCompanies missing CON:")
    print(missing_con)

    duplicate_rules = df.duplicated(
        subset=[
            "company_id",
            "rule_id"
        ]
    ).sum()

    print("\nDuplicate rule rows:", duplicate_rules)

    if (
        (df["confidence_pct"] <= 60).sum() == 0
        and len(missing_pro) == 0
        and len(missing_con) == 0
        and duplicate_rules == 0
    ):
        print("\nVALIDATION PASSED")
    else:
        print("\nVALIDATION WARNING")


def main():

    print("=" * 80)
    print("DAY 31 — CASH FLOW PROS / CONS GENERATOR")
    print("=" * 80)

    print("\nINPUT:")
    print(INPUT_FILE)

    if not os.path.exists(INPUT_FILE):

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    print("\nINPUT EXISTS:")
    print(True)

    df = pd.read_csv(INPUT_FILE)

    print("\nINPUT SHAPE:")
    print(df.shape)

    required_columns = [
        "company_id",
        "year",
        "free_cash_flow",
        "cfo_quality",
        "capex_label",
        "fcf_conversion",
        "pattern_label"
    ]

    print("\nCHECKING REQUIRED COLUMNS...")

    missing = [
        c for c in required_columns
        if c not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing required columns: {missing}"
        )

    print("All required columns found.")

    # Ensure numeric columns are numeric
    df["free_cash_flow"] = pd.to_numeric(
        df["free_cash_flow"],
        errors="coerce"
    )

    df["fcf_conversion"] = pd.to_numeric(
        df["fcf_conversion"],
        errors="coerce"
    )

    all_rows = []

    companies = sorted(
        df["company_id"]
        .dropna()
        .unique()
    )

    print("\nCOMPANIES:")
    print(len(companies))

    print("\nGENERATING CASH-FLOW PROS / CONS")
    print("=" * 80)

    for i, company in enumerate(companies, start=1):

        company_df = df[
            df["company_id"] == company
        ].copy()

        company_df = company_df.reset_index(
            drop=True
        )

        generated = generate_company_rules(
            company,
            company_df
        )

        all_rows.extend(generated)

        pro_count = sum(
            r["type"] == "pro"
            for r in generated
        )

        con_count = sum(
            r["type"] == "con"
            for r in generated
        )

        print(
            f"[{i:3d}/{len(companies)}] "
            f"{company:<15} "
            f"Pros={pro_count:2d} "
            f"Cons={con_count:2d}"
        )

    result = pd.DataFrame(all_rows)

    # Sort output
    result = result.sort_values(
        [
            "company_id",
            "type",
            "rule_id"
        ]
    ).reset_index(drop=True)

    validate_output(result)

    result.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n" + "=" * 80)
    print("OUTPUT SAVED")
    print("=" * 80)

    print(OUTPUT_FILE)

    print("\nRows:", len(result))

    print(
        "Companies:",
        result["company_id"].nunique()
    )

    print("\nDAY 31 COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()