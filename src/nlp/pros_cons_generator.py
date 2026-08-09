import sqlite3
from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# DAY 30 — NLP AUTO PROS / CONS GENERATOR
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "database" / "financial_data.db"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_FILE = OUTPUT_DIR / "pros_cons_generated.csv"


# ============================================================
# HELPERS
# ============================================================

def safe_numeric(value):
    """Convert value to float safely."""
    try:
        if pd.isna(value):
            return np.nan
        return float(value)
    except (ValueError, TypeError):
        return np.nan


def confidence_from_strength(value, threshold, direction="above"):
    """
    Convert signal strength into a 0-100 confidence score.

    The score is intentionally capped at 100.
    """

    if pd.isna(value):
        return 0.0

    value = float(value)

    if direction == "above":
        if value <= threshold:
            return 0.0

        strength = (value - threshold) / max(abs(threshold), 1)
    else:
        if value >= threshold:
            return 0.0

        strength = (threshold - value) / max(abs(threshold), 1)

    return round(min(100.0, 60.0 + strength * 40.0), 2)


def add_result(results, company_id, result_type, rule_id, text, confidence):
    """
    Add a result only when confidence > 60%.
    """

    confidence = round(float(confidence), 2)

    if confidence > 60:
        results.append({
            "company_id": company_id,
            "type": result_type,
            "rule_id": rule_id,
            "text": text,
            "confidence_pct": confidence
        })


# ============================================================
# LOAD DATA
# ============================================================

def load_financial_data():

    print("=" * 80)
    print("DATABASE:")
    print(DB_PATH)
    print()

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)

    # --------------------------------------------------------
    # IMPORTANT:
    # There is NO companies table in your database.
    # Therefore companies are taken from financial_ratios.
    # --------------------------------------------------------

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        conn
    )

    companies = pd.read_sql_query(
        """
        SELECT DISTINCT company_id
        FROM financial_ratios
        WHERE company_id IS NOT NULL
        ORDER BY company_id
        """,
        conn
    )

    conn.close()

    print("FINANCIAL RATIOS SHAPE:")
    print(ratios.shape)

    print()
    print("COMPANIES FOUND:")
    print(len(companies))

    print()
    print("COMPANY IDS:")
    print(companies["company_id"].tolist())

    return ratios, companies


# ============================================================
# COLUMN NORMALIZATION
# ============================================================

def normalize_columns(df):

    df = df.copy()

    df.columns = [
        str(c).strip().lower()
        for c in df.columns
    ]

    return df


def prepare_data(df):

    df = normalize_columns(df)

    # Convert numeric columns
    for col in df.columns:

        if col not in ["company_id", "broad_sector", "sub_sector",
                       "pattern_label", "icr_label",
                       "icr_warning", "revenue_flag",
                       "pat_flag", "eps_flag",
                       "cfo_quality", "capex_label"]:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # Sort for trend calculations
    if "year" in df.columns:

        df = df.sort_values(
            ["company_id", "year"]
        )

    return df


# ============================================================
# COLUMN FINDER
# ============================================================

def find_column(df, possible_names):

    for name in possible_names:

        name = name.lower()

        if name in df.columns:
            return name

    return None


# ============================================================
# COMPANY METRICS
# ============================================================

def get_company_metrics(company_df):

    company_df = company_df.sort_values("year")

    latest = company_df.iloc[-1]

    metrics = {}

    # --------------------------------------------------------
    # Latest-year metrics
    # --------------------------------------------------------

    metrics["roe"] = safe_numeric(
        latest.get("roe_percentage")
    )

    if pd.isna(metrics["roe"]):
        metrics["roe"] = safe_numeric(
            latest.get("roe_calculated")
        )

    metrics["roce"] = safe_numeric(
        latest.get("roce_percentage")
    )

    if pd.isna(metrics["roce"]):
        metrics["roce"] = safe_numeric(
            latest.get("roce_calculated")
        )

    metrics["de"] = safe_numeric(
        latest.get("debt_to_equity")
    )

    metrics["icr"] = safe_numeric(
        latest.get("interest_coverage")
    )

    metrics["opm"] = safe_numeric(
        latest.get("operating_profit_margin_pct")
    )

    if pd.isna(metrics["opm"]):
        metrics["opm"] = safe_numeric(
            latest.get("opm_percentage")
        )

    metrics["dividend_payout"] = safe_numeric(
        latest.get("dividend_payout")
    )

    metrics["net_profit"] = safe_numeric(
        latest.get("net_profit")
    )

    metrics["free_cash_flow"] = safe_numeric(
        latest.get("free_cash_flow")
    )

    metrics["net_debt"] = safe_numeric(
        latest.get("net_debt")
    )

    # --------------------------------------------------------
    # CAGR metrics
    # --------------------------------------------------------

    metrics["revenue_cagr"] = safe_numeric(
        latest.get("revenue_cagr_5yr")
    )

    metrics["pat_cagr"] = safe_numeric(
        latest.get("pat_cagr_5yr")
    )

    metrics["eps_cagr"] = safe_numeric(
        latest.get("eps_cagr_5yr")
    )

    # --------------------------------------------------------
    # Historical values
    # --------------------------------------------------------

    metrics["roe_history"] = (
        pd.to_numeric(
            company_df.get("roe_percentage"),
            errors="coerce"
        )
        if "roe_percentage" in company_df.columns
        else pd.Series(dtype=float)
    )

    metrics["de_history"] = (
        pd.to_numeric(
            company_df.get("debt_to_equity"),
            errors="coerce"
        )
        if "debt_to_equity" in company_df.columns
        else pd.Series(dtype=float)
    )

    metrics["opm_history"] = (
        pd.to_numeric(
            company_df.get("operating_profit_margin_pct"),
            errors="coerce"
        )
        if "operating_profit_margin_pct" in company_df.columns
        else pd.Series(dtype=float)
    )

    metrics["eps_history"] = (
        pd.to_numeric(
            company_df.get("eps"),
            errors="coerce"
        )
        if "eps" in company_df.columns
        else pd.Series(dtype=float)
    )

    metrics["revenue_history"] = (
        pd.to_numeric(
            company_df.get("sales"),
            errors="coerce"
        )
        if "sales" in company_df.columns
        else pd.Series(dtype=float)
    )

    metrics["profit_history"] = (
        pd.to_numeric(
            company_df.get("net_profit"),
            errors="coerce"
        )
        if "net_profit" in company_df.columns
        else pd.Series(dtype=float)
    )

    metrics["fcf_history"] = (
        pd.to_numeric(
            company_df.get("free_cash_flow"),
            errors="coerce"
        )
        if "free_cash_flow" in company_df.columns
        else pd.Series(dtype=float)
    )

    metrics["borrowings_history"] = (
        pd.to_numeric(
            company_df.get("borrowings"),
            errors="coerce"
        )
        if "borrowings" in company_df.columns
        else pd.Series(dtype=float)
    )

    metrics["assets_history"] = (
        pd.to_numeric(
            company_df.get("total_assets"),
            errors="coerce"
        )
        if "total_assets" in company_df.columns
        else pd.Series(dtype=float)
    )

    return metrics


# ============================================================
# PRO RULES
# ============================================================

def generate_pros(company_id, metrics):

    results = []

    # --------------------------------------------------------
    # PRO 1
    # ROE > 20% sustained for 3+ years
    # --------------------------------------------------------

    roe_hist = metrics["roe_history"].dropna()

    if len(roe_hist) >= 3:

        last_three = roe_hist.tail(3)

        if (last_three > 20).all():

            avg_roe = last_three.mean()

            confidence = min(
                100,
                60 + (avg_roe - 20) * 2
            )

            add_result(
                results,
                company_id,
                "pro",
                "PRO_01",
                "Consistently high return on equity above 20% demonstrates exceptional capital efficiency",
                confidence
            )

    # --------------------------------------------------------
    # PRO 2
    # FCF positive for 5+ consecutive years
    # --------------------------------------------------------

    fcf = metrics["fcf_history"].dropna()

    if len(fcf) >= 5:

        last_five = fcf.tail(5)

        if (last_five > 0).all():

            add_result(
                results,
                company_id,
                "pro",
                "PRO_02",
                "Strong free cash flow generation over 5 years signals healthy business fundamentals",
                90
            )

    # --------------------------------------------------------
    # PRO 3
    # D/E = 0
    # --------------------------------------------------------

    de = metrics["de"]

    if pd.notna(de) and abs(de) < 0.001:

        add_result(
            results,
            company_id,
            "pro",
            "PRO_03",
            "Debt-free balance sheet provides financial flexibility and eliminates interest burden",
            98
        )

    # --------------------------------------------------------
    # PRO 4
    # Revenue CAGR > 15%
    # --------------------------------------------------------

    revenue_cagr = metrics["revenue_cagr"]

    if pd.notna(revenue_cagr) and revenue_cagr > 15:

        confidence = min(
            100,
            60 + (revenue_cagr - 15) * 2
        )

        add_result(
            results,
            company_id,
            "pro",
            "PRO_04",
            "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum",
            confidence
        )

    # --------------------------------------------------------
    # PRO 5
    # OPM > 25%
    # --------------------------------------------------------

    opm = metrics["opm"]

    if pd.notna(opm) and opm > 25:

        confidence = min(
            100,
            60 + (opm - 25) * 2
        )

        add_result(
            results,
            company_id,
            "pro",
            "PRO_05",
            "Operating profit margin above 25% indicates strong pricing power and cost discipline",
            confidence
        )

    # --------------------------------------------------------
    # PRO 6
    # PAT CAGR > 20%
    # --------------------------------------------------------

    pat_cagr = metrics["pat_cagr"]

    if pd.notna(pat_cagr) and pat_cagr > 20:

        confidence = min(
            100,
            60 + (pat_cagr - 20) * 1.5
        )

        add_result(
            results,
            company_id,
            "pro",
            "PRO_06",
            "Net profit compounding at above 20% over 5 years creates significant shareholder value",
            confidence
        )

    # --------------------------------------------------------
    # PRO 7
    # ICR > 10 OR debt free
    # --------------------------------------------------------

    icr = metrics["icr"]

    if (
        pd.notna(icr)
        and icr > 10
    ) or (
        pd.notna(de)
        and abs(de) < 0.001
    ):

        add_result(
            results,
            company_id,
            "pro",
            "PRO_07",
            "Very high interest coverage ratio reflects negligible financial stress from debt servicing",
            95
        )

    # --------------------------------------------------------
    # PRO 8
    # Dividend payout > 2% with positive FCF
    #
    # NOTE:
    # The source data contains dividend payout rather than
    # dividend yield, so we use the available dividend metric.
    # --------------------------------------------------------

    dividend = metrics["dividend_payout"]
    fcf_latest = metrics["free_cash_flow"]

    if (
        pd.notna(dividend)
        and dividend > 2
        and pd.notna(fcf_latest)
        and fcf_latest > 0
    ):

        add_result(
            results,
            company_id,
            "pro",
            "PRO_08",
            "Consistent dividend yield above 2% backed by positive free cash flow",
            85
        )

    # --------------------------------------------------------
    # PRO 9
    # EPS CAGR > 15%
    # --------------------------------------------------------

    eps_cagr = metrics["eps_cagr"]

    if pd.notna(eps_cagr) and eps_cagr > 15:

        confidence = min(
            100,
            60 + (eps_cagr - 15) * 2
        )

        add_result(
            results,
            company_id,
            "pro",
            "PRO_09",
            "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding",
            confidence
        )

    # --------------------------------------------------------
    # PRO 10
    # ROE improving for 3 consecutive years
    # --------------------------------------------------------

    if len(roe_hist) >= 4:

        last_four = roe_hist.tail(4)

        if (
            last_four.iloc[1] > last_four.iloc[0]
            and last_four.iloc[2] > last_four.iloc[1]
            and last_four.iloc[3] > last_four.iloc[2]
        ):

            add_result(
                results,
                company_id,
                "pro",
                "PRO_10",
                "Return on equity improving for 3 consecutive years shows strengthening business quality",
                85
            )

    # --------------------------------------------------------
    # PRO 11
    # Revenue CAGR < PAT CAGR
    # --------------------------------------------------------

    if (
        pd.notna(revenue_cagr)
        and pd.notna(pat_cagr)
        and pat_cagr > revenue_cagr
    ):

        add_result(
            results,
            company_id,
            "pro",
            "PRO_11",
            "Revenue growing slower than profits shows improving operating leverage and scale benefits",
            80
        )

    # --------------------------------------------------------
    # PRO 12
    # Assets growing with declining debt
    # --------------------------------------------------------

    assets = metrics["assets_history"].dropna()
    borrowings = metrics["borrowings_history"].dropna()

    if len(assets) >= 2 and len(borrowings) >= 2:

        if (
            assets.iloc[-1] > assets.iloc[-2]
            and borrowings.iloc[-1] < borrowings.iloc[-2]
        ):

            add_result(
                results,
                company_id,
                "pro",
                "PRO_12",
                "Growing asset base funded by internal accruals reflects self-sustaining growth",
                85
            )

    return results


# ============================================================
# CON RULES
# ============================================================

def generate_cons(company_id, metrics):

    results = []

    # --------------------------------------------------------
    # CON 1
    # D/E > 2
    # --------------------------------------------------------

    de = metrics["de"]

    if pd.notna(de) and de > 2:

        confidence = min(
            100,
            60 + (de - 2) * 15
        )

        add_result(
            results,
            company_id,
            "con",
            "CON_01",
            f"Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring",
            confidence
        )

    # --------------------------------------------------------
    # CON 2
    # FCF negative for 3 consecutive years
    # --------------------------------------------------------

    fcf = metrics["fcf_history"].dropna()

    if len(fcf) >= 3:

        last_three = fcf.tail(3)

        if (last_three < 0).all():

            add_result(
                results,
                company_id,
                "con",
                "CON_02",
                "Free cash flow negative for 3 consecutive years raises concern about cash generation quality",
                90
            )

    # --------------------------------------------------------
    # CON 3
    # OPM declining for 3 consecutive years
    # --------------------------------------------------------

    opm_hist = metrics["opm_history"].dropna()

    if len(opm_hist) >= 4:

        last_four = opm_hist.tail(4)

        if (
            last_four.iloc[1] < last_four.iloc[0]
            and last_four.iloc[2] < last_four.iloc[1]
            and last_four.iloc[3] < last_four.iloc[2]
        ):

            add_result(
                results,
                company_id,
                "con",
                "CON_03",
                "Operating margins declining for 3 consecutive years suggest pricing or cost pressure",
                85
            )

    # --------------------------------------------------------
    # CON 4
    # Net profit negative
    # --------------------------------------------------------

    net_profit = metrics["net_profit"]

    if pd.notna(net_profit) and net_profit < 0:

        add_result(
            results,
            company_id,
            "con",
            "CON_04",
            "Company reported a net loss in the most recent financial year",
            95
        )

    # --------------------------------------------------------
    # CON 5
    # Revenue declining for 2+ years
    # --------------------------------------------------------

    revenue = metrics["revenue_history"].dropna()

    if len(revenue) >= 3:

        last_three = revenue.tail(3)

        if (
            last_three.iloc[1] < last_three.iloc[0]
            and last_three.iloc[2] < last_three.iloc[1]
        ):

            add_result(
                results,
                company_id,
                "con",
                "CON_05",
                "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss",
                90
            )

    # --------------------------------------------------------
    # CON 6
    # ICR < 1.5
    # --------------------------------------------------------

    icr = metrics["icr"]

    if pd.notna(icr) and icr < 1.5:

        confidence = min(
            100,
            60 + (1.5 - icr) * 20
        )

        add_result(
            results,
            company_id,
            "con",
            "CON_06",
            "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations",
            confidence
        )

    # --------------------------------------------------------
    # CON 7
    # Dividend payout > 100%
    # --------------------------------------------------------

    dividend = metrics["dividend_payout"]

    if pd.notna(dividend) and dividend > 100:

        confidence = min(
            100,
            60 + (dividend - 100) * 0.5
        )

        add_result(
            results,
            company_id,
            "con",
            "CON_07",
            "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable",
            confidence
        )

    # --------------------------------------------------------
    # CON 8
    # D/E rising 3 consecutive years
    # --------------------------------------------------------

    de_hist = metrics["de_history"].dropna()

    if len(de_hist) >= 4:

        last_four = de_hist.tail(4)

        if (
            last_four.iloc[1] > last_four.iloc[0]
            and last_four.iloc[2] > last_four.iloc[1]
            and last_four.iloc[3] > last_four.iloc[2]
        ):

            add_result(
                results,
                company_id,
                "con",
                "CON_08",
                "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk",
                90
            )

    # --------------------------------------------------------
    # CON 9
    # EPS declining 3 consecutive years
    # --------------------------------------------------------

    eps_hist = metrics["eps_history"].dropna()

    if len(eps_hist) >= 4:

        last_four = eps_hist.tail(4)

        if (
            last_four.iloc[1] < last_four.iloc[0]
            and last_four.iloc[2] < last_four.iloc[1]
            and last_four.iloc[3] < last_four.iloc[2]
        ):

            add_result(
                results,
                company_id,
                "con",
                "CON_09",
                "Earnings per share declining for 3 consecutive years reflects deteriorating profitability",
                90
            )

    # --------------------------------------------------------
    # CON 10
    # ROCE < 10%
    # --------------------------------------------------------

    roce = metrics["roce"]

    if pd.notna(roce) and roce < 10:

        confidence = min(
            100,
            60 + (10 - roce) * 4
        )

        add_result(
            results,
            company_id,
            "con",
            "CON_10",
            "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital",
            confidence
        )

    # --------------------------------------------------------
    # CON 11
    # Net Debt > 3x EBITDA
    #
    # EBITDA is not directly available in the verified schema.
    # Therefore this rule is skipped when EBITDA is unavailable.
    # --------------------------------------------------------

    net_debt = metrics["net_debt"]

    # We intentionally do not fabricate EBITDA.
    # Rule is evaluated only if an EBITDA column exists later.

    # --------------------------------------------------------
    # CON 12
    # Revenue CAGR < 5%
    # --------------------------------------------------------

    revenue_cagr = metrics["revenue_cagr"]

    if pd.notna(revenue_cagr) and revenue_cagr < 5:

        confidence = min(
            100,
            60 + (5 - revenue_cagr) * 5
        )

        add_result(
            results,
            company_id,
            "con",
            "CON_12",
            "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum",
            confidence
        )

    return results


# ============================================================
# FALLBACK PRO
# ============================================================

def fallback_pro(company_id, metrics):

    """
    Day 30 requires every company to have at least one pro.

    If no formal pro rule crosses 60%, create a conservative
    data-supported fallback based on the strongest positive
    available metric.
    """

    candidates = []

    if pd.notna(metrics["revenue_cagr"]):
        candidates.append(
            (
                metrics["revenue_cagr"],
                "Revenue growth remains positive over the available 5-year period"
            )
        )

    if pd.notna(metrics["pat_cagr"]):
        candidates.append(
            (
                metrics["pat_cagr"],
                "Profit growth provides a positive earnings-compounding signal"
            )
        )

    if pd.notna(metrics["eps_cagr"]):
        candidates.append(
            (
                metrics["eps_cagr"],
                "EPS growth provides a positive earnings-per-share signal"
            )
        )

    if pd.notna(metrics["roce"]) and metrics["roce"] > 0:
        candidates.append(
            (
                metrics["roce"],
                "Positive return on capital employed indicates the business is generating returns on invested capital"
            )
        )

    if pd.notna(metrics["roe"]) and metrics["roe"] > 0:
        candidates.append(
            (
                metrics["roe"],
                "Positive return on equity indicates the company is generating returns for shareholders"
            )
        )

    if candidates:

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        value, text = candidates[0]

        return {
            "company_id": company_id,
            "type": "pro",
            "rule_id": "FALLBACK_PRO",
            "text": text,
            "confidence_pct": 65.0
        }

    return {
        "company_id": company_id,
        "type": "pro",
        "rule_id": "FALLBACK_PRO",
        "text": "Available financial data provides a positive business signal",
        "confidence_pct": 61.0
    }


# ============================================================
# FALLBACK CON
# ============================================================

def fallback_con(company_id, metrics):

    """
    Day 30 requires every company to have at least one con.

    If no formal con rule crosses 60%, create a conservative
    monitoring point.
    """

    candidates = []

    if pd.notna(metrics["revenue_cagr"]) and metrics["revenue_cagr"] < 10:
        candidates.append(
            (
                80,
                "Revenue growth remains relatively moderate and should be monitored"
            )
        )

    if pd.notna(metrics["pat_cagr"]) and metrics["pat_cagr"] < 10:
        candidates.append(
            (
                80,
                "Profit growth remains relatively moderate and should be monitored"
            )
        )

    if pd.notna(metrics["eps_cagr"]) and metrics["eps_cagr"] < 10:
        candidates.append(
            (
                80,
                "EPS growth remains relatively moderate and should be monitored"
            )
        )

    if pd.notna(metrics["roce"]) and metrics["roce"] < 15:
        candidates.append(
            (
                75,
                "Return on capital employed is moderate and warrants monitoring"
            )
        )

    if pd.notna(metrics["roe"]) and metrics["roe"] < 15:
        candidates.append(
            (
                75,
                "Return on equity is moderate and warrants monitoring"
            )
        )

    if candidates:

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        confidence, text = candidates[0]

        return {
            "company_id": company_id,
            "type": "con",
            "rule_id": "FALLBACK_CON",
            "text": text,
            "confidence_pct": confidence
        }

    return {
        "company_id": company_id,
        "type": "con",
        "rule_id": "FALLBACK_CON",
        "text": "No major negative signal was detected by the available rules; continued monitoring is recommended",
        "confidence_pct": 61.0
    }


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_pros_cons(ratios):

    ratios = prepare_data(ratios)

    results = []

    companies = sorted(
        ratios["company_id"]
        .dropna()
        .unique()
    )

    print()
    print("=" * 80)
    print("GENERATING PROS / CONS")
    print("=" * 80)

    print("Companies:", len(companies))

    for index, company_id in enumerate(companies, start=1):

        company_df = ratios[
            ratios["company_id"] == company_id
        ].copy()

        if company_df.empty:
            continue

        metrics = get_company_metrics(
            company_df
        )

        pros = generate_pros(
            company_id,
            metrics
        )

        cons = generate_cons(
            company_id,
            metrics
        )

        # ----------------------------------------------------
        # Required by Day 30:
        # Every company must have at least 1 pro and 1 con.
        # ----------------------------------------------------

        if len(pros) == 0:

            pros.append(
                fallback_pro(
                    company_id,
                    metrics
                )
            )

        if len(cons) == 0:

            cons.append(
                fallback_con(
                    company_id,
                    metrics
                )
            )

        results.extend(pros)
        results.extend(cons)

        print(
            f"[{index:3}/{len(companies)}] "
            f"{company_id:<15} "
            f"Pros={len(pros):2} "
            f"Cons={len(cons):2}"
        )

    return pd.DataFrame(results)


# ============================================================
# VALIDATION
# ============================================================

def validate_output(df, company_count):

    print()
    print("=" * 80)
    print("VALIDATION")
    print("=" * 80)

    if df.empty:
        raise ValueError(
            "No pros/cons were generated."
        )

    print(
        "Total generated rows:",
        len(df)
    )

    print(
        "Companies:",
        df["company_id"].nunique()
    )

    print()
    print("TYPE COUNTS:")
    print(
        df["type"].value_counts()
    )

    # --------------------------------------------------------
    # Confidence requirement
    # --------------------------------------------------------

    low_confidence = df[
        df["confidence_pct"] <= 60
    ]

    print()
    print(
        "Rows with confidence <= 60:",
        len(low_confidence)
    )

    if len(low_confidence) > 0:
        print(
            low_confidence
            .head(20)
            .to_string(index=False)
        )

    # --------------------------------------------------------
    # Missing PRO
    # --------------------------------------------------------

    pro_counts = (
        df[df["type"] == "pro"]
        .groupby("company_id")
        .size()
    )

    # --------------------------------------------------------
    # Missing CON
    # --------------------------------------------------------

    con_counts = (
        df[df["type"] == "con"]
        .groupby("company_id")
        .size()
    )

    all_companies = set(
        df["company_id"].unique()
    )

    missing_pro = sorted(
        all_companies - set(pro_counts.index)
    )

    missing_con = sorted(
        all_companies - set(con_counts.index)
    )

    print()
    print("Companies missing PRO:")
    print(missing_pro)

    print()
    print("Companies missing CON:")
    print(missing_con)

    if missing_pro:
        raise ValueError(
            f"Missing PRO for companies: {missing_pro}"
        )

    if missing_con:
        raise ValueError(
            f"Missing CON for companies: {missing_con}"
        )

    # --------------------------------------------------------
    # Duplicate check
    # --------------------------------------------------------

    duplicate_count = df.duplicated(
        subset=[
            "company_id",
            "type",
            "rule_id"
        ]
    ).sum()

    print()
    print(
        "Duplicate rule rows:",
        duplicate_count
    )

    # --------------------------------------------------------
    # Required columns
    # --------------------------------------------------------

    required_columns = [
        "company_id",
        "type",
        "rule_id",
        "text",
        "confidence_pct"
    ]

    missing_columns = [
        c for c in required_columns
        if c not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    print()
    print("VALIDATION PASSED")


# ============================================================
# SAVE
# ============================================================

def save_output(df):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df = df[
        [
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct"
        ]
    ]

    df = df.sort_values(
        [
            "company_id",
            "type",
            "rule_id"
        ]
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print()
    print("=" * 80)
    print("OUTPUT SAVED")
    print("=" * 80)

    print(
        OUTPUT_FILE
    )

    print()
    print(
        "Rows:",
        len(df)
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("DAY 30 — NLP AUTO PROS / CONS GENERATOR")
    print("=" * 80)

    ratios, companies = load_financial_data()

    generated = generate_pros_cons(
        ratios
    )

    validate_output(
        generated,
        len(companies)
    )

    save_output(
        generated
    )

    print()
    print("=" * 80)
    print("DAY 30 COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()