import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT DATABASE FUNCTIONS
# ============================================================

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🏢 Company Profile")

st.caption(
    "View company financial performance, "
    "profitability, growth, and cash-flow indicators."
)


# ============================================================
# LOAD COMPANY LIST
# ============================================================

companies = get_companies()

if companies.empty:

    st.error(
        "No companies were found in the database."
    )

    st.stop()


company_list = (
    companies["company_id"]
    .dropna()
    .astype(str)
    .sort_values()
    .tolist()
)


# ============================================================
# COMPANY SEARCH
# ============================================================

selected_company = st.selectbox(
    "Search or select a company ticker",
    options=company_list,
    index=0,
    placeholder="Type a company ticker..."
)


# ============================================================
# LOAD COMPANY DATA
# ============================================================

company_data = get_ratios(
    selected_company
)

profit_loss_data = get_pl(
    selected_company
)


# ============================================================
# HANDLE COMPANY NOT FOUND
# ============================================================

if company_data.empty:

    st.warning(
        "Ticker not found — please try another."
    )

    st.stop()


# ============================================================
# CLEAN YEAR DATA
# ============================================================

company_data = company_data.copy()

company_data["year"] = (
    company_data["year"]
    .astype(str)
    .str.strip()
)

company_data["year_number"] = (
    company_data["year"]
    .str.extract(
        r"(\d{4})"
    )[0]
)

company_data["year_number"] = pd.to_numeric(
    company_data["year_number"],
    errors="coerce"
)

company_data = company_data.sort_values(
    "year_number"
)


# ============================================================
# GET LATEST RECORD
# ============================================================

latest_data = (
    company_data
    .dropna(
        subset=["year_number"]
    )
    .sort_values(
        "year_number"
    )
    .iloc[-1]
)


# ============================================================
# SAFE VALUE FUNCTION
# ============================================================

def get_value(
    row,
    column,
    decimals=2,
    suffix=""
):

    if column not in row.index:
        return "N/A"

    value = row[column]

    if pd.isna(value):
        return "N/A"

    try:

        return (
            f"{float(value):,.{decimals}f}"
            f"{suffix}"
        )

    except (
        TypeError,
        ValueError
    ):

        return str(value)


# ============================================================
# COMPANY PROFILE CARD
# ============================================================

st.subheader(
    f"📌 {selected_company}"
)

st.caption(
    f"Latest financial year: "
    f"{latest_data['year']}"
)

st.divider()


# ============================================================
# KPI CARDS
# ============================================================

col1, col2, col3 = st.columns(3)

col4, col5, col6 = st.columns(3)


with col1:

    st.metric(
        "ROE",
        get_value(
            latest_data,
            "roe_calculated",
            suffix="%"
        )
    )


with col2:

    st.metric(
        "ROCE",
        get_value(
            latest_data,
            "roce_calculated",
            suffix="%"
        )
    )


with col3:

    st.metric(
        "Net Profit Margin",
        get_value(
            latest_data,
            "net_profit_margin_pct",
            suffix="%"
        )
    )


with col4:

    st.metric(
        "Debt-to-Equity",
        get_value(
            latest_data,
            "debt_to_equity"
        )
    )


with col5:

    st.metric(
        "Revenue CAGR — 5 Year",
        get_value(
            latest_data,
            "revenue_cagr_5yr",
            suffix="%"
        )
    )


with col6:

    st.metric(
        "Free Cash Flow",
        get_value(
            latest_data,
            "free_cash_flow",
            suffix=" Cr"
        )
    )


st.divider()


# ============================================================
# REVENUE AND NET PROFIT CHART
# ============================================================

st.subheader(
    "📊 Revenue and Net Profit Trend"
)


if profit_loss_data.empty:

    st.info(
        "Profit and loss data is not available "
        "for this company."
    )

else:

    profit_loss_data = (
        profit_loss_data.copy()
    )

    profit_loss_data["year"] = (
        profit_loss_data["year"]
        .astype(str)
        .str.strip()
    )

    profit_loss_data["year_number"] = (
        profit_loss_data["year"]
        .str.extract(
            r"(\d{4})"
        )[0]
    )

    profit_loss_data["year_number"] = (
        pd.to_numeric(
            profit_loss_data[
                "year_number"
            ],
            errors="coerce"
        )
    )

    profit_loss_data = (
        profit_loss_data
        .sort_values(
            "year_number"
        )
        .tail(10)
    )

    figure = go.Figure()

    figure.add_trace(

        go.Bar(

            x=profit_loss_data[
                "year"
            ],

            y=profit_loss_data[
                "sales"
            ],

            name="Revenue"

        )

    )

    figure.add_trace(

        go.Bar(

            x=profit_loss_data[
                "year"
            ],

            y=profit_loss_data[
                "net_profit"
            ],

            name="Net Profit"

        )

    )

    figure.update_layout(

        barmode="group",

        xaxis_title="Financial Year",

        yaxis_title="Amount",

        height=500,

        legend_title="Metric"

    )

    st.plotly_chart(

        figure,

        use_container_width=True

    )


st.divider()


# ============================================================
# ROE AND ROCE TREND
# ============================================================

st.subheader(
    "📈 ROE and ROCE Trend"
)


required_columns = [

    "year",

    "roe_calculated",

    "roce_calculated"

]


if all(

    column in company_data.columns

    for column in required_columns

):

    ratio_trend = (

        company_data[

            required_columns

        ]

        .dropna(

            how="all",

            subset=[

                "roe_calculated",

                "roce_calculated"

            ]

        )

        .tail(10)

    )


    if ratio_trend.empty:

        st.info(

            "ROE and ROCE trend data "

            "is not available."

        )

    else:

        figure = go.Figure()


        figure.add_trace(

            go.Scatter(

                x=ratio_trend["year"],

                y=ratio_trend[

                    "roe_calculated"

                ],

                mode="lines+markers",

                name="ROE"

            )

        )


        figure.add_trace(

            go.Scatter(

                x=ratio_trend["year"],

                y=ratio_trend[

                    "roce_calculated"

                ],

                mode="lines+markers",

                name="ROCE",

                yaxis="y2"

            )

        )


        figure.update_layout(

            xaxis=dict(

                title="Financial Year"

            ),

            yaxis=dict(

                title="ROE (%)"

            ),

            yaxis2=dict(

                title="ROCE (%)",

                overlaying="y",

                side="right"

            ),

            height=500,

            legend=dict(

                orientation="h"

            )

        )


        st.plotly_chart(

            figure,

            use_container_width=True

        )

else:

    st.info(

        "ROE and ROCE columns are "

        "not available in the database."

    )


st.divider()


# ============================================================
# PROS AND CONS
# ============================================================

st.subheader(
    "✅ Pros and ⚠️ Cons"
)


pros = []

cons = []


# ROE CHECK

roe_value = latest_data.get(

    "roe_calculated",

    None

)


if pd.notna(

    roe_value

):

    if roe_value >= 15:

        pros.append(

            "Strong return on equity "

            "(ROE above 15%)."

        )

    else:

        cons.append(

            "ROE is below the "

            "15% quality benchmark."

        )


# DEBT-TO-EQUITY CHECK

de_value = latest_data.get(

    "debt_to_equity",

    None

)


if pd.notna(

    de_value

):

    if de_value <= 1:

        pros.append(

            "Low debt-to-equity ratio."

        )

    else:

        cons.append(

            "High debt-to-equity ratio."

        )


# REVENUE CAGR CHECK

revenue_cagr = latest_data.get(

    "revenue_cagr_5yr",

    None

)


if pd.notna(

    revenue_cagr

):

    if revenue_cagr >= 10:

        pros.append(

            "Healthy 5-year revenue growth."

        )

    else:

        cons.append(

            "Revenue CAGR is below "

            "the 10% growth benchmark."

        )


# FREE CASH FLOW CHECK

fcf_value = latest_data.get(

    "free_cash_flow",

    None

)


if pd.notna(

    fcf_value

):

    if fcf_value > 0:

        pros.append(

            "Positive free cash flow."

        )

    else:

        cons.append(

            "Negative free cash flow."

        )


# ============================================================
# DISPLAY PROS AND CONS
# ============================================================

left_column, right_column = (

    st.columns(2)

)


with left_column:

    st.markdown(

        "#### ✅ Pros"

    )


    if pros:

        for item in pros:

            st.success(

                item

            )

    else:

        st.info(

            "No major positive "

            "indicators were identified."

        )


with right_column:

    st.markdown(

        "#### ⚠️ Cons"

    )


    if cons:

        for item in cons:

            st.error(

                item

            )

    else:

        st.success(

            "No major warning "

            "indicators were identified."

        )