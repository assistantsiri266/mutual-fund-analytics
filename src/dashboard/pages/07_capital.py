import pandas as pd
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_valuation,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Capital & Valuation",
    page_icon="💰",
    layout="wide",
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("💰 Capital & Valuation")

st.caption(
    "Analyze company market capitalization and valuation metrics."
)


# ============================================================
# LOAD COMPANIES
# ============================================================

companies_df = get_companies()

if companies_df.empty:

    st.warning(
        "No companies are available in the database."
    )

    st.stop()


company_list = (
    companies_df["company_id"]
    .dropna()
    .astype(str)
    .sort_values()
    .tolist()
)


# ============================================================
# COMPANY SELECTOR
# ============================================================

selected_company = st.selectbox(
    "Select a company",
    options=company_list,
    index=0,
)


# ============================================================
# LOAD VALUATION DATA
# ============================================================

valuation_df = get_valuation(
    selected_company
)


# ============================================================
# NO VALUATION DATA
# ============================================================

if valuation_df.empty:

    st.warning(
        f"Valuation data is not available "
        f"for {selected_company}."
    )

    st.info(
        "Currently, the valuation table contains "
        "data only for ABB, ADANIENSOL, and ADANIENT."
    )

    st.stop()


# ============================================================
# GET THE LATEST RECORD
# ============================================================

latest_data = valuation_df.iloc[0]


# ============================================================
# READ VALUATION VALUES
# ============================================================

market_cap = pd.to_numeric(
    latest_data.get(
        "market_cap_crore",
        0
    ),
    errors="coerce",
)

pe_ratio = pd.to_numeric(
    latest_data.get(
        "pe_ratio",
        0
    ),
    errors="coerce",
)

pb_ratio = pd.to_numeric(
    latest_data.get(
        "pb_ratio",
        0
    ),
    errors="coerce",
)

ev_ebitda = pd.to_numeric(
    latest_data.get(
        "ev_ebitda",
        0
    ),
    errors="coerce",
)


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

if pd.isna(market_cap):

    market_cap = 0


if pd.isna(pe_ratio):

    pe_ratio = 0


if pd.isna(pb_ratio):

    pb_ratio = 0


if pd.isna(ev_ebitda):

    ev_ebitda = 0


# ============================================================
# COMPANY HEADING
# ============================================================

st.subheader(
    f"📊 {selected_company} Valuation Summary"
)


# ============================================================
# KPI CARDS
# ============================================================

column_1, column_2, column_3, column_4 = st.columns(4)


with column_1:

    st.metric(
        label="Market Capitalization",
        value=(
            f"₹ {market_cap:,.2f} Cr"
        ),
    )


with column_2:

    st.metric(
        label="P/E Ratio",
        value=(
            f"{pe_ratio:,.2f}"
        ),
    )


with column_3:

    st.metric(
        label="P/B Ratio",
        value=(
            f"{pb_ratio:,.2f}"
        ),
    )


with column_4:

    st.metric(
        label="EV / EBITDA",
        value=(
            f"{ev_ebitda:,.2f}"
        ),
    )


# ============================================================
# DIVIDER
# ============================================================

st.divider()


# ============================================================
# VALUATION INTERPRETATION
# ============================================================

st.subheader(
    "📌 Valuation Interpretation"
)


interpretation_column_1, interpretation_column_2 = (
    st.columns(2)
)


with interpretation_column_1:

    if pe_ratio == 0:

        st.info(
            "P/E ratio data is currently recorded "
            "as 0, so valuation interpretation is "
            "not available."
        )

    elif pe_ratio < 15:

        st.success(
            "The P/E ratio is below 15. "
            "The company may be relatively "
            "lower valued compared with companies "
            "that have higher P/E ratios."
        )

    elif pe_ratio <= 30:

        st.info(
            "The P/E ratio is between 15 and 30. "
            "This indicates a moderate valuation."
        )

    else:

        st.warning(
            "The P/E ratio is above 30. "
            "The company may be trading at "
            "a relatively high valuation."
        )


with interpretation_column_2:

    if pb_ratio == 0:

        st.info(
            "P/B ratio data is currently recorded "
            "as 0, so valuation interpretation is "
            "not available."
        )

    elif pb_ratio < 1:

        st.success(
            "The P/B ratio is below 1. "
            "The market value is below the "
            "company's book value."
        )

    elif pb_ratio <= 3:

        st.info(
            "The P/B ratio is between 1 and 3. "
            "This indicates a moderate "
            "price-to-book valuation."
        )

    else:

        st.warning(
            "The P/B ratio is above 3. "
            "The company is trading at a "
            "relatively high multiple of "
            "its book value."
        )


# ============================================================
# VALUATION DATA TABLE
# ============================================================

st.divider()

st.subheader(
    "📋 Available Valuation Data"
)


display_dataframe = valuation_df.copy()


st.dataframe(
    display_dataframe,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# DATA NOTE
# ============================================================

st.caption(
    "Note: The current valuation dataset contains "
    "placeholder values. Replace the values in "
    "data/raw/market_cap.csv with actual market "
    "capitalization and valuation data for a "
    "complete analysis."
)