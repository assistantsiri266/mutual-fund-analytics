import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# DAY 31 — CASH FLOW INTELLIGENCE MODULE
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


COMPANIES_FILE = DATA_DIR / "companies.xlsx"
CASHFLOW_FILE = DATA_DIR / "cashflow.xlsx"
PNL_FILE = DATA_DIR / "profitandloss.xlsx"


# ============================================================
# HELPERS
# ============================================================

def normalize_company_id(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    # Source typo -> canonical ticker
    if value == "AGTL":
        value = "ATGL"

    return value


def sign(value):
    if pd.isna(value):
        return np.nan

    return "+" if float(value) >= 0 else "-"


def capital_allocation_pattern(cfo, cfi, cff):

    if pd.isna(cfo) or pd.isna(cfi) or pd.isna(cff):
        return "Unknown"

    pattern = (
        sign(cfo),
        sign(cfi),
        sign(cff)
    )

    mapping = {

        # Operating cash positive
        # Investing cash negative
        # Financing cash negative
        ("+", "-", "-"): "Reinvestor",

        # Operating positive
        # Investing positive
        # Financing negative
        ("+", "+", "-"): "Liquidating Assets",

        # Operating negative
        # Investing positive
        # Financing positive
        ("-", "+", "+"): "Distress Signal",

        # Operating negative
        # Investing negative
        # Financing positive
        ("-", "-", "+"): "Growth Funded by Debt",

        # All positive
        ("+", "+", "+"): "Cash Accumulator",

        # All negative
        ("-", "-", "-"): "Pre-Revenue",

        # Operating positive
        # Investing negative
        # Financing positive
        ("+", "-", "+"): "Mixed",

        # Operating negative
        # Investing positive
        # Financing negative
        ("-", "+", "-"): "Mixed",
    }

    return mapping.get(pattern, "Other")


def cfo_quality_label(score):

    if pd.isna(score):
        return "Accrual Risk"

    if score > 1.0:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def capex_label(value):

    if pd.isna(value):
        return "Unknown"

    if value < 3:
        return "Asset Light"

    if value <= 8:
        return "Moderate"

    return "Capital Intensive"


def safe_cagr(first_value, last_value, years):

    if pd.isna(first_value) or pd.isna(last_value):
        return np.nan

    if years <= 0:
        return np.nan

    if first_value <= 0 or last_value <= 0:
        return np.nan

    try:
        return ((last_value / first_value) ** (1 / years) - 1) * 100
    except Exception:
        return np.nan


# ============================================================
# START
# ============================================================

print("\n" + "=" * 80)
print("DAY 31 — CASH FLOW INTELLIGENCE MODULE")
print("=" * 80)

print("\nINPUT FILES:")
print("Companies :", COMPANIES_FILE)
print("Cash Flow :", CASHFLOW_FILE)
print("P&L       :", PNL_FILE)

print("\nEXISTS:")
print("companies.xlsx =", COMPANIES_FILE.exists())
print("cashflow.xlsx  =", CASHFLOW_FILE.exists())
print("profitandloss.xlsx =", PNL_FILE.exists())


if not COMPANIES_FILE.exists():
    raise FileNotFoundError("companies.xlsx not found")

if not CASHFLOW_FILE.exists():
    raise FileNotFoundError("cashflow.xlsx not found")

if not PNL_FILE.exists():
    raise FileNotFoundError("profitandloss.xlsx not found")


# ============================================================
# 1. COMPANY MASTER
# ============================================================

print("\n" + "=" * 80)
print("1. LOADING COMPANY MASTER")
print("=" * 80)

companies_raw = pd.read_excel(
    COMPANIES_FILE,
    header=None
)

print("\nCompany file raw shape:")
print(companies_raw.shape)


# ------------------------------------------------------------
# Find ticker column automatically
# ------------------------------------------------------------

possible_columns = []

for col in companies_raw.columns:

    values = (
        companies_raw[col]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
    )

    valid_count = values.isin(
        [
            "ABB",
            "ATGL",
            "BPCL",
            "TCS",
            "RELIANCE",
            "INFY",
            "HDFCBANK",
            "ULTRACEMCO",
            "UNIONBANK"
        ]
    ).sum()

    if valid_count > 0:
        possible_columns.append(col)


if possible_columns:

    company_column = possible_columns[0]

else:

    # In this project the ticker is the first column.
    company_column = companies_raw.columns[0]


print("\nDetected company/ticker column:")
print(company_column)


companies = companies_raw[
    [company_column]
].copy()

companies["company_id"] = (
    companies[company_column]
    .apply(normalize_company_id)
)


# Remove header / junk values
invalid_values = {
    None,
    "",
    "ID",
    "COMPANY_ID",
    "TICKER",
    "SYMBOL"
}

companies = companies[
    ~companies["company_id"].isin(invalid_values)
].copy()


# Keep only ticker-like values
companies = companies[
    companies["company_id"].str.len() <= 20
].copy()


canonical_companies = set(
    companies["company_id"]
    .dropna()
    .unique()
)


# ------------------------------------------------------------
# Add known canonical companies that exist in unified data
# but are missing from the master file.
# ------------------------------------------------------------

KNOWN_MISSING = {
    "ULTRACEMCO",
    "UNIONBANK"
}

canonical_companies.update(KNOWN_MISSING)


print("\nCANONICAL COMPANY UNIVERSE:")
print("Companies:", len(canonical_companies))

print("\nFirst 20 companies:")
print(sorted(canonical_companies)[:20])


# ============================================================
# 2. LOAD CASH FLOW
# ============================================================

cashflow = pd.read_excel(
    CASHFLOW_FILE,
    header=1
)

cashflow.columns = [
    str(c).strip().lower()
    for c in cashflow.columns
]

print("\nCash Flow shape:")
print(cashflow.shape)

print("Cash Flow columns:")
print(cashflow.columns.tolist())


required_cf = [
    "company_id",
    "year",
    "operating_activity",
    "investing_activity",
    "financing_activity"
]

missing_cf = [
    c for c in required_cf
    if c not in cashflow.columns
]

if missing_cf:
    raise ValueError(
        f"Missing Cash Flow columns: {missing_cf}"
    )


cashflow["company_id"] = (
    cashflow["company_id"]
    .apply(normalize_company_id)
)

cashflow["year"] = pd.to_numeric(
    cashflow["year"],
    errors="coerce"
)


for col in [
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow"
]:

    if col in cashflow.columns:

        cashflow[col] = pd.to_numeric(
            cashflow[col],
            errors="coerce"
        )


cashflow = cashflow[
    cashflow["company_id"].isin(
        canonical_companies
    )
].copy()


print("\nAfter company filter:")
print(
    "Cash-flow companies:",
    cashflow["company_id"].nunique()
)


# ============================================================
# 3. LOAD PROFIT & LOSS
# ============================================================

pnl = pd.read_excel(
    PNL_FILE,
    header=1
)

pnl.columns = [
    str(c).strip().lower()
    for c in pnl.columns
]

print("\nP&L shape:")
print(pnl.shape)

print("P&L columns:")
print(pnl.columns.tolist())


required_pnl = [
    "company_id",
    "year",
    "sales",
    "operating_profit",
    "net_profit",
    "eps",
    "dividend_payout"
]

missing_pnl = [
    c for c in required_pnl
    if c not in pnl.columns
]

if missing_pnl:
    raise ValueError(
        f"Missing P&L columns: {missing_pnl}"
    )


pnl["company_id"] = (
    pnl["company_id"]
    .apply(normalize_company_id)
)

pnl["year"] = pd.to_numeric(
    pnl["year"],
    errors="coerce"
)


numeric_pnl = [
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
    "dividend_payout"
]

for col in numeric_pnl:

    if col in pnl.columns:

        pnl[col] = pd.to_numeric(
            pnl[col],
            errors="coerce"
        )


pnl = pnl[
    pnl["company_id"].isin(
        canonical_companies
    )
].copy()


print("\nAfter company filter:")
print(
    "Profit/Loss companies:",
    pnl["company_id"].nunique()
)


# ============================================================
# 4. REMOVE DUPLICATES
# ============================================================

cashflow = (
    cashflow
    .sort_values(["company_id", "year"])
    .drop_duplicates(
        subset=["company_id", "year"],
        keep="last"
    )
)

pnl = (
    pnl
    .sort_values(["company_id", "year"])
    .drop_duplicates(
        subset=["company_id", "year"],
        keep="last"
    )
)

print(
    "\nCash-flow rows after deduplication:",
    len(cashflow)
)

print(
    "P&L rows after deduplication:",
    len(pnl)
)


# ============================================================
# 5. MERGE
# ============================================================

df = pd.merge(
    cashflow,
    pnl,
    on=["company_id", "year"],
    how="inner",
    suffixes=("", "_pnl")
)

print("\nMerged shape:")
print(df.shape)

print(
    "Merged companies:",
    df["company_id"].nunique()
)


# ============================================================
# 6. FCF
# ============================================================

df["free_cash_flow"] = (
    df["operating_activity"]
    + df["investing_activity"]
)


# ============================================================
# 7. CFO / PAT RATIO
# ============================================================

df["cfo_pat_ratio"] = np.where(
    df["net_profit"].notna()
    & (df["net_profit"] != 0),

    df["operating_activity"]
    / df["net_profit"],

    np.nan
)


# ============================================================
# 8. CAPEX INTENSITY
# ============================================================

df["capex_intensity_pct"] = np.where(

    df["sales"].notna()
    & (df["sales"] != 0),

    (
        df["investing_activity"].abs()
        / df["sales"]
        * 100
    ),

    np.nan
)


df["capex_label"] = (
    df["capex_intensity_pct"]
    .apply(capex_label)
)


# ============================================================
# 9. FCF CONVERSION
# ============================================================

df["fcf_conversion_pct"] = np.where(

    df["net_profit"].notna()
    & (df["net_profit"] != 0),

    df["free_cash_flow"]
    / df["net_profit"]
    * 100,

    np.nan
)


# ============================================================
# 10. COMPANY-LEVEL INTELLIGENCE
# ============================================================

results = []

distress_rows = []

capital_rows = []


for company_id, group in df.groupby(
    "company_id",
    sort=True
):

    group = group.sort_values("year").copy()

    latest = group.iloc[-1]

    # --------------------------------------------------------
    # CFO QUALITY — average CFO/PAT over available years
    # --------------------------------------------------------

    cfo_score = group[
        "cfo_pat_ratio"
    ].mean()

    cfo_label = cfo_quality_label(
        cfo_score
    )


    # --------------------------------------------------------
    # CAPEX
    # --------------------------------------------------------

    capex_score = latest[
        "capex_intensity_pct"
    ]

    capex_class = capex_label(
        capex_score
    )


    # --------------------------------------------------------
    # FCF CAGR
    # --------------------------------------------------------

    fcf_cagr = np.nan

    fcf_history = group[
        ["year", "free_cash_flow"]
    ].dropna()

    if len(fcf_history) >= 6:

        first = fcf_history.iloc[-6]
        last = fcf_history.iloc[-1]

        fcf_cagr = safe_cagr(
            first["free_cash_flow"],
            last["free_cash_flow"],
            5
        )


    # --------------------------------------------------------
    # Latest FCF conversion
    # --------------------------------------------------------

    fcf_conversion = latest[
        "fcf_conversion_pct"
    ]


    # --------------------------------------------------------
    # Distress signal
    #
    # CFO < 0 AND CFF > 0
    # --------------------------------------------------------

    distress_flag = (
        pd.notna(
            latest["operating_activity"]
        )
        and pd.notna(
            latest["financing_activity"]
        )
        and latest["operating_activity"] < 0
        and latest["financing_activity"] > 0
    )


    # --------------------------------------------------------
    # Deleveraging
    #
    # CFF < 0 AND financing cash negative
    # indicates capital repayment / debt reduction.
    # --------------------------------------------------------

    deleveraging_flag = (
        pd.notna(
            latest["financing_activity"]
        )
        and latest["financing_activity"] < 0
    )


    # --------------------------------------------------------
    # Capital allocation
    # --------------------------------------------------------

    capital_label = capital_allocation_pattern(
        latest["operating_activity"],
        latest["investing_activity"],
        latest["financing_activity"]
    )


    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    result = {

        "company_id": company_id,

        "cfo_quality_score": cfo_score,

        "cfo_quality_label": cfo_label,

        "capex_intensity_pct": capex_score,

        "capex_label": capex_class,

        "fcf_cagr_5yr": fcf_cagr,

        "fcf_conversion_pct": fcf_conversion,

        "distress_flag": distress_flag,

        "deleveraging_flag": deleveraging_flag,

        "capital_allocation_label": capital_label,

        "cfo_latest": latest[
            "operating_activity"
        ],

        "cff_latest": latest[
            "financing_activity"
        ],

        "net_profit_latest": latest[
            "net_profit"
        ],

        "latest_year": latest[
            "year"
        ]
    }

    results.append(result)


    # --------------------------------------------------------
    # Distress alert
    # --------------------------------------------------------

    if distress_flag:

        distress_rows.append({

            "company_id": company_id,

            "year": latest["year"],

            "cfo_value":
                latest["operating_activity"],

            "cff_value":
                latest["financing_activity"],

            "latest_net_profit":
                latest["net_profit"]

        })


    # --------------------------------------------------------
    # Capital allocation history
    # --------------------------------------------------------

    for _, row in group.iterrows():

        capital_rows.append({

            "company_id":
                company_id,

            "year":
                row["year"],

            "cfo_sign":
                sign(row["operating_activity"]),

            "cfi_sign":
                sign(row["investing_activity"]),

            "cff_sign":
                sign(row["financing_activity"]),

            "capital_allocation_label":
                capital_allocation_pattern(
                    row["operating_activity"],
                    row["investing_activity"],
                    row["financing_activity"]
                )
        })


# ============================================================
# 11. OUTPUT DATAFRAME
# ============================================================

intelligence = pd.DataFrame(
    results
)

intelligence = intelligence.sort_values(
    "company_id"
).reset_index(drop=True)


# ============================================================
# 12. VALIDATION
# ============================================================

print("\n" + "=" * 80)
print("FINAL VALIDATION")
print("=" * 80)

print(
    "\nRows:",
    len(intelligence)
)

print(
    "Companies:",
    intelligence["company_id"].nunique()
)


missing_companies = sorted(
    canonical_companies
    - set(
        intelligence["company_id"]
    )
)

extra_companies = sorted(
    set(
        intelligence["company_id"]
    )
    - canonical_companies
)


print(
    "Missing companies:",
    missing_companies
)

print(
    "Extra companies:",
    extra_companies
)


# ============================================================
# 13. SAVE CASH FLOW INTELLIGENCE
# ============================================================

intelligence_file = (
    OUTPUT_DIR
    / "cashflow_intelligence.xlsx"
)

with pd.ExcelWriter(
    intelligence_file,
    engine="openpyxl"
) as writer:

    intelligence.to_excel(
        writer,
        sheet_name="cashflow_intelligence",
        index=False
    )


print(
    "\nCash-flow intelligence saved:"
)

print(
    intelligence_file
)


# ============================================================
# 14. SAVE DISTRESS ALERTS
# ============================================================

distress_file = (
    OUTPUT_DIR
    / "distress_alerts.csv"
)

distress_df = pd.DataFrame(
    distress_rows
)

distress_df.to_csv(
    distress_file,
    index=False
)


print(
    "\nDistress alerts saved:"
)

print(
    distress_file
)

print(
    "Distress companies:",
    len(distress_df)
)


# ============================================================
# 15. SAVE CAPITAL ALLOCATION
# ============================================================

capital_file = (
    OUTPUT_DIR
    / "capital_allocation.csv"
)

capital_df = pd.DataFrame(
    capital_rows
)

capital_df.to_csv(
    capital_file,
    index=False
)


print(
    "\nCapital allocation saved:"
)

print(
    capital_file
)


# ============================================================
# 16. DISTRIBUTIONS
# ============================================================

print(
    "\nCapital allocation distribution:"
)

print(
    intelligence[
        "capital_allocation_label"
    ].value_counts()
)


print(
    "\nCFO quality distribution:"
)

print(
    intelligence[
        "cfo_quality_label"
    ].value_counts()
)


print(
    "\nCapEx intensity distribution:"
)

print(
    intelligence[
        "capex_label"
    ].value_counts()
)


# ============================================================
# 17. FINAL CHECKS
# ============================================================

required_output_columns = [

    "company_id",

    "cfo_quality_score",

    "cfo_quality_label",

    "capex_intensity_pct",

    "capex_label",

    "fcf_cagr_5yr",

    "fcf_conversion_pct",

    "distress_flag",

    "deleveraging_flag",

    "capital_allocation_label"
]


missing_output_columns = [
    c
    for c in required_output_columns
    if c not in intelligence.columns
]


if missing_output_columns:

    print(
        "\nFAIL: Missing output columns:",
        missing_output_columns
    )

else:

    print(
        "\nPASS: All required output columns present."
    )


if len(intelligence) == 0:

    print(
        "FAIL: Final dataset is empty."
    )

else:

    print(
        "PASS: Final dataset is not empty."
    )


print("\n" + "=" * 80)
print("DAY 31 CASH FLOW INTELLIGENCE COMPLETE")
print("=" * 80)