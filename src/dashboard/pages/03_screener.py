import pandas as pd
import streamlit as st

from src.dashboard.utils.db import get_latest_ratios


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🔎 Financial Screener")

st.caption(
    "Filter companies using profitability, growth, "
    "cash-flow, leverage, and efficiency metrics."
)


# ============================================================
# LOAD LATEST DATA
# ============================================================

data = get_latest_ratios().copy()


# ============================================================
# CHECK DATABASE DATA
# ============================================================

if data.empty:

    st.error(
        "No financial data is available in the database."
    )

    st.stop()


# ============================================================
# CONVERT IMPORTANT COLUMNS TO NUMERIC
# ============================================================

numeric_columns = [

    "roe_calculated",

    "roce_calculated",

    "net_profit_margin_pct",

    "debt_to_equity",

    "free_cash_flow",

    "revenue_cagr_5yr",

    "pat_cagr_5yr",

    "operating_profit_margin_pct",

    "interest_coverage",

    "asset_turnover",

    "sales",

    "net_profit",

    "eps_cagr_5yr",

    "dividend_payout"
]


for column in numeric_columns:

    if column in data.columns:

        data[column] = pd.to_numeric(

            data[column],

            errors="coerce"

        )


# ============================================================
# CREATE COMPOSITE QUALITY SCORE
# ============================================================

def normalize_metric(series, higher_is_better=True):

    values = pd.to_numeric(

        series,

        errors="coerce"

    )

    valid_values = values.dropna()


    if valid_values.empty:

        return pd.Series(

            50.0,

            index=series.index

        )


    lower_limit = valid_values.quantile(

        0.10

    )

    upper_limit = valid_values.quantile(

        0.90

    )


    if pd.isna(lower_limit) or pd.isna(upper_limit):

        return pd.Series(

            50.0,

            index=series.index

        )


    if upper_limit == lower_limit:

        return pd.Series(

            50.0,

            index=series.index

        )


    clipped_values = values.clip(

        lower=lower_limit,

        upper=upper_limit

    )


    normalized = (

        (

            clipped_values

            - lower_limit

        )

        /

        (

            upper_limit

            - lower_limit

        )

        * 100

    )


    if not higher_is_better:

        normalized = 100 - normalized


    return normalized.fillna(

        50

    )


# ============================================================
# CALCULATE QUALITY SCORE
# ============================================================

score = pd.Series(

    0.0,

    index=data.index

)


# Profitability = 35%

if "roe_calculated" in data.columns:

    score += (

        normalize_metric(

            data["roe_calculated"]

        )

        * 0.15

    )


if "roce_calculated" in data.columns:

    score += (

        normalize_metric(

            data["roce_calculated"]

        )

        * 0.10

    )


if "net_profit_margin_pct" in data.columns:

    score += (

        normalize_metric(

            data["net_profit_margin_pct"]

        )

        * 0.10

    )


# Cash Quality = 20%

if "free_cash_flow" in data.columns:

    score += (

        normalize_metric(

            data["free_cash_flow"]

        )

        * 0.20

    )


# Growth = 25%

if "revenue_cagr_5yr" in data.columns:

    score += (

        normalize_metric(

            data["revenue_cagr_5yr"]

        )

        * 0.125

    )


if "pat_cagr_5yr" in data.columns:

    score += (

        normalize_metric(

            data["pat_cagr_5yr"]

        )

        * 0.125

    )


# Leverage = 20%

if "debt_to_equity" in data.columns:

    score += (

        normalize_metric(

            data["debt_to_equity"],

            higher_is_better=False

        )

        * 0.15

    )


if "interest_coverage" in data.columns:

    score += (

        normalize_metric(

            data["interest_coverage"]

        )

        * 0.05

    )


data["composite_quality_score"] = (

    score

    .clip(

        lower=0,

        upper=100

    )

    .round(2)

)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(

    "🎛️ Screener Filters"

)


# ============================================================
# PRESET SELECTOR
# ============================================================

preset = st.sidebar.selectbox(

    "Select Preset",

    [

        "Custom",

        "Quality Compounder",

        "Value Pick",

        "Growth Accelerator",

        "Dividend Champion",

        "Debt-Free Blue Chip",

        "Turnaround Watch"

    ]

)


# ============================================================
# DEFAULT FILTER VALUES
# ============================================================

roe_min = 0.0

de_max = 100.0

fcf_min = -100000.0

revenue_cagr_min = -100.0

pat_cagr_min = -100.0

opm_min = -100.0

pe_max = 1000.0

pb_max = 1000.0

dividend_yield_min = 0.0

icr_min = -100.0


# ============================================================
# APPLY PRESET VALUES
# ============================================================

if preset == "Quality Compounder":

    roe_min = 15.0

    de_max = 1.0

    fcf_min = 0.0

    revenue_cagr_min = 10.0


elif preset == "Value Pick":

    de_max = 2.0

    pe_max = 20.0

    pb_max = 3.0

    dividend_yield_min = 1.0


elif preset == "Growth Accelerator":

    pat_cagr_min = 20.0

    revenue_cagr_min = 15.0

    de_max = 2.0


elif preset == "Dividend Champion":

    fcf_min = 0.0

    dividend_yield_min = 2.0


elif preset == "Debt-Free Blue Chip":

    roe_min = 12.0

    de_max = 0.0


elif preset == "Turnaround Watch":

    revenue_cagr_min = 10.0

    fcf_min = 0.0


# ============================================================
# FILTER INPUTS
# ============================================================

roe_min = st.sidebar.number_input(

    "Minimum ROE (%)",

    value=roe_min,

    step=1.0

)


de_max = st.sidebar.number_input(

    "Maximum Debt-to-Equity",

    value=de_max,

    step=0.1

)


fcf_min = st.sidebar.number_input(

    "Minimum Free Cash Flow",

    value=fcf_min,

    step=100.0

)


revenue_cagr_min = st.sidebar.number_input(

    "Minimum Revenue CAGR 5Y (%)",

    value=revenue_cagr_min,

    step=1.0

)


pat_cagr_min = st.sidebar.number_input(

    "Minimum PAT CAGR 5Y (%)",

    value=pat_cagr_min,

    step=1.0

)


opm_min = st.sidebar.number_input(

    "Minimum OPM (%)",

    value=opm_min,

    step=1.0

)


pe_max = st.sidebar.number_input(

    "Maximum P/E",

    value=pe_max,

    step=1.0

)


pb_max = st.sidebar.number_input(

    "Maximum P/B",

    value=pb_max,

    step=0.1

)


dividend_yield_min = st.sidebar.number_input(

    "Minimum Dividend Yield (%)",

    value=dividend_yield_min,

    step=0.5

)


icr_min = st.sidebar.number_input(

    "Minimum Interest Coverage",

    value=icr_min,

    step=0.5

)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_data = data.copy()


# ROE

if "roe_calculated" in filtered_data.columns:

    filtered_data = filtered_data[

        filtered_data[

            "roe_calculated"

        ].fillna(

            -999999

        ) >= roe_min

    ]


# Debt-to-Equity

if "debt_to_equity" in filtered_data.columns:

    filtered_data = filtered_data[

        filtered_data[

            "debt_to_equity"

        ].fillna(

            999999

        ) <= de_max

    ]


# Free Cash Flow

if "free_cash_flow" in filtered_data.columns:

    filtered_data = filtered_data[

        filtered_data[

            "free_cash_flow"

        ].fillna(

            -999999

        ) >= fcf_min

    ]


# Revenue CAGR

if "revenue_cagr_5yr" in filtered_data.columns:

    filtered_data = filtered_data[

        filtered_data[

            "revenue_cagr_5yr"

        ].fillna(

            -999999

        ) >= revenue_cagr_min

    ]


# PAT CAGR

if "pat_cagr_5yr" in filtered_data.columns:

    filtered_data = filtered_data[

        filtered_data[

            "pat_cagr_5yr"

        ].fillna(

            -999999

        ) >= pat_cagr_min

    ]


# OPM

if "operating_profit_margin_pct" in filtered_data.columns:

    filtered_data = filtered_data[

        filtered_data[

            "operating_profit_margin_pct"

        ].fillna(

            -999999

        ) >= opm_min

    ]


# Interest Coverage

if "interest_coverage" in filtered_data.columns:

    filtered_data = filtered_data[

        filtered_data[

            "interest_coverage"

        ].fillna(

            -999999

        ) >= icr_min

    ]


# ============================================================
# OPTIONAL VALUATION FILTERS
# ============================================================

# Your current database does not contain
# P/E, P/B, and Dividend Yield columns.

missing_valuation_columns = []


for column in [

    "pe",

    "pb",

    "dividend_yield"

]:

    if column not in filtered_data.columns:

        missing_valuation_columns.append(

            column

        )


if missing_valuation_columns:

    st.sidebar.info(

        "P/E, P/B and Dividend Yield data are "

        "not currently available in the database. "

        "Those filters will be added after the "

        "valuation module is completed."

    )


# ============================================================
# SORT RESULTS
# ============================================================

filtered_data = (

    filtered_data

    .sort_values(

        by="composite_quality_score",

        ascending=False

    )

    .reset_index(

        drop=True

    )

)


# ============================================================
# RESULT COUNT
# ============================================================

st.subheader(

    f"📊 {len(filtered_data)} Companies Match Your Filters"

)


st.caption(

    f"Selected preset: {preset}"

)


# ============================================================
# SELECT DISPLAY COLUMNS
# ============================================================

display_columns = [

    "company_id",

    "year",

    "composite_quality_score",

    "roe_calculated",

    "roce_calculated",

    "net_profit_margin_pct",

    "debt_to_equity",

    "free_cash_flow",

    "revenue_cagr_5yr",

    "pat_cagr_5yr",

    "operating_profit_margin_pct",

    "interest_coverage",

    "asset_turnover",

    "sales",

    "net_profit"

]


available_columns = [

    column

    for column in display_columns

    if column in filtered_data.columns

]


result_table = (

    filtered_data[

        available_columns

    ]

    .copy()

)


# ============================================================
# ROUND NUMERIC VALUES
# ============================================================

for column in result_table.columns:

    if pd.api.types.is_numeric_dtype(

        result_table[column]

    ):

        result_table[column] = (

            result_table[column]

            .round(2)

        )


# ============================================================
# DISPLAY TABLE
# ============================================================

if result_table.empty:

    st.warning(

        "No companies match the selected filters. "

        "Try reducing one or more filter values."

    )

else:

    st.dataframe(

        result_table,

        use_container_width=True,

        hide_index=True

    )


# ============================================================
# CSV DOWNLOAD
# ============================================================

csv_data = (

    result_table

    .to_csv(

        index=False

    )

    .encode(

        "utf-8"

    )

)


st.download_button(

    label="⬇️ Download Filtered Results as CSV",

    data=csv_data,

    file_name="screener_results.csv",

    mime="text/csv",

    use_container_width=True

)


# ============================================================
# FOOTER
# ============================================================

st.divider()


st.caption(

    "Financial Screener • "

    "Latest available financial data is used "

    "for every company."

)