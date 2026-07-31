import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_all_ratios,
    get_latest_ratios,
    get_sectors,
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🏭 Sector Analysis")

st.caption(
    "Compare companies within a sector using revenue, "
    "return on equity, market size, and sector-level metrics."
)


# ============================================================
# LOAD LATEST FINANCIAL DATA
# ============================================================

latest_data = get_latest_ratios().copy()

if latest_data.empty:

    st.error(
        "No financial data is available in the database."
    )

    st.stop()


# ============================================================
# CHECK SECTOR INFORMATION
# ============================================================

sector_column = None

possible_sector_columns = [
    "broad_sector",
    "sector",
    "industry"
]

for column in possible_sector_columns:

    if column in latest_data.columns:

        sector_column = column

        break


# ============================================================
# IF SECTOR DATA IS NOT AVAILABLE
# ============================================================

if sector_column is None:

    st.warning(
        "Sector information is not currently available "
        "in the financial_ratios table."
    )

    st.info(
        "The Sector Analysis screen requires a sector "
        "column such as broad_sector or sector. "
        "The page is working correctly, but sector data "
        "must be added to the database to display "
        "sector comparisons."
    )

    st.subheader(
        "Available Database Columns"
    )

    st.code(
        "\n".join(
            latest_data.columns.tolist()
        )
    )

    st.stop()


# ============================================================
# CLEAN SECTOR DATA
# ============================================================

latest_data[sector_column] = (

    latest_data[sector_column]
    .astype(str)
    .str.strip()

)


latest_data = latest_data[

    latest_data[sector_column]
    .notna()

].copy()


latest_data = latest_data[

    latest_data[sector_column]
    .ne("")

].copy()


latest_data = latest_data[

    latest_data[sector_column]
    .ne("nan")

].copy()


if latest_data.empty:

    st.warning(
        "Sector information exists in the database, "
        "but no valid sector values are available."
    )

    st.stop()


# ============================================================
# SECTOR DROPDOWN
# ============================================================

sector_list = sorted(

    latest_data[sector_column]
    .dropna()
    .unique()
    .tolist()

)


selected_sector = st.selectbox(

    "Select a sector",

    options=sector_list

)


# ============================================================
# FILTER SELECTED SECTOR
# ============================================================

sector_data = latest_data[

    latest_data[sector_column]
    == selected_sector

].copy()


if sector_data.empty:

    st.warning(
        f"No company data is available for "
        f"{selected_sector}."
    )

    st.stop()


# ============================================================
# DISPLAY SECTOR SUMMARY
# ============================================================

st.subheader(

    f"📊 {selected_sector} — Sector Summary"

)


total_companies = (

    sector_data["company_id"]
    .nunique()

)


# ------------------------------------------------------------
# Convert important metrics to numeric
# ------------------------------------------------------------

numeric_columns = [

    "sales",

    "roe_calculated",

    "roce_calculated",

    "net_profit",

    "debt_to_equity",

    "free_cash_flow"

]


for column in numeric_columns:

    if column in sector_data.columns:

        sector_data[column] = pd.to_numeric(

            sector_data[column],

            errors="coerce"

        )


# ------------------------------------------------------------
# KPI calculations
# ------------------------------------------------------------

median_revenue = None

median_roe = None

median_roce = None

median_de = None


if "sales" in sector_data.columns:

    median_revenue = (

        sector_data["sales"]
        .median()

    )


if "roe_calculated" in sector_data.columns:

    median_roe = (

        sector_data["roe_calculated"]
        .median()

    )


if "roce_calculated" in sector_data.columns:

    median_roce = (

        sector_data["roce_calculated"]
        .median()

    )


if "debt_to_equity" in sector_data.columns:

    median_de = (

        sector_data["debt_to_equity"]
        .median()

    )


# ============================================================
# SECTOR KPI CARDS
# ============================================================

kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = (

    st.columns(5)

)


kpi_1.metric(

    "Companies",

    total_companies

)


kpi_2.metric(

    "Median Revenue",

    (
        f"₹{median_revenue:,.0f} Cr"
        if pd.notna(median_revenue)
        else "N/A"
    )

)


kpi_3.metric(

    "Median ROE",

    (
        f"{median_roe:.2f}%"
        if pd.notna(median_roe)
        else "N/A"
    )

)


kpi_4.metric(

    "Median ROCE",

    (
        f"{median_roce:.2f}%"
        if pd.notna(median_roce)
        else "N/A"
    )

)


kpi_5.metric(

    "Median D/E",

    (
        f"{median_de:.2f}"
        if pd.notna(median_de)
        else "N/A"
    )

)


st.divider()


# ============================================================
# CHECK REQUIRED BUBBLE-CHART COLUMNS
# ============================================================

required_columns = [

    "company_id",

    "sales",

    "roe_calculated"

]


missing_columns = [

    column

    for column in required_columns

    if column not in sector_data.columns

]


if missing_columns:

    st.error(

        "The following required columns are missing: "

        + ", ".join(
            missing_columns
        )

    )

    st.stop()


# ============================================================
# MARKET CAP COLUMN
# ============================================================

market_cap_column = None


possible_market_cap_columns = [

    "market_cap",

    "market_cap_crore",

    "market_capitalization"

]


for column in possible_market_cap_columns:

    if column in sector_data.columns:

        market_cap_column = column

        break


# ------------------------------------------------------------
# Create a bubble-size column
# ------------------------------------------------------------

if market_cap_column is not None:

    sector_data[market_cap_column] = (

        pd.to_numeric(

            sector_data[
                market_cap_column
            ],

            errors="coerce"

        )

    )


    sector_data["bubble_size"] = (

        sector_data[
            market_cap_column
        ]

    )


else:

    # Fallback when market-cap data is unavailable
    # Revenue is used only for bubble size

    sector_data["bubble_size"] = (

        sector_data["sales"]
        .abs()

    )


# ============================================================
# SUB-SECTOR / CATEGORY COLUMN
# ============================================================

category_column = None


possible_category_columns = [

    "sub_sector",

    "subsector",

    "industry",

    "category"

]


for column in possible_category_columns:

    if column in sector_data.columns:

        category_column = column

        break


if category_column is None:

    sector_data["company_category"] = (

        "All Companies"

    )

    category_column = (

        "company_category"

    )


# ============================================================
# CLEAN BUBBLE-CHART DATA
# ============================================================

bubble_data = sector_data[

    [

        "company_id",

        "sales",

        "roe_calculated",

        "bubble_size",

        category_column

    ]

].copy()


bubble_data = bubble_data.dropna(

    subset=[

        "sales",

        "roe_calculated"

    ]

)


bubble_data = bubble_data[

    bubble_data["sales"] >= 0

]


bubble_data["bubble_size"] = (

    bubble_data["bubble_size"]
    .fillna(0)
    .abs()

)


# Avoid zero-size bubbles
bubble_data.loc[

    bubble_data["bubble_size"] <= 0,

    "bubble_size"

] = 1


# ============================================================
# BUBBLE CHART
# ============================================================

st.subheader(

    "🫧 Revenue vs ROE"

)


if bubble_data.empty:

    st.warning(

        "Insufficient data is available to "
        "create the sector bubble chart."

    )


else:

    bubble_title = (

        f"{selected_sector}: "
        "Revenue vs ROE"

    )


    if market_cap_column is not None:

        bubble_description = (

            "Bubble size represents market "
            "capitalization."

        )

    else:

        bubble_description = (

            "Market-cap data is not available. "
            "Bubble size is based on revenue."

        )


    bubble_chart = px.scatter(

        bubble_data,

        x="sales",

        y="roe_calculated",

        size="bubble_size",

        color=category_column,

        hover_name="company_id",

        size_max=60,

        title=bubble_title,

        labels={

            "sales":
            "Revenue / Sales (₹ Crore)",

            "roe_calculated":
            "ROE (%)",

            category_column:
            "Category"

        }

    )


    bubble_chart.update_layout(

        height=650,

        legend_title="Category",

        margin=dict(

            l=40,

            r=40,

            t=80,

            b=60

        )

    )


    bubble_chart.update_xaxes(

        title="Revenue / Sales (₹ Crore)"

    )


    bubble_chart.update_yaxes(

        title="ROE (%)"

    )


    st.plotly_chart(

        bubble_chart,

        use_container_width=True

    )


    st.caption(

        bubble_description

    )


st.divider()


# ============================================================
# SECTOR MEDIAN KPI BAR CHART
# ============================================================

st.subheader(

    "📊 Sector Median Metrics"

)


median_metrics = []


# ------------------------------------------------------------
# Revenue
# ------------------------------------------------------------

if "sales" in sector_data.columns:

    revenue_value = (

        sector_data["sales"]
        .median()

    )


    if pd.notna(

        revenue_value

    ):

        median_metrics.append(

            {

                "Metric":
                "Revenue",

                "Median Value":
                revenue_value

            }

        )


# ------------------------------------------------------------
# ROE
# ------------------------------------------------------------

if "roe_calculated" in sector_data.columns:

    roe_value = (

        sector_data[
            "roe_calculated"
        ]
        .median()

    )


    if pd.notna(

        roe_value

    ):

        median_metrics.append(

            {

                "Metric":
                "ROE",

                "Median Value":
                roe_value

            }

        )


# ------------------------------------------------------------
# ROCE
# ------------------------------------------------------------

if "roce_calculated" in sector_data.columns:

    roce_value = (

        sector_data[
            "roce_calculated"
        ]
        .median()

    )


    if pd.notna(

        roce_value

    ):

        median_metrics.append(

            {

                "Metric":
                "ROCE",

                "Median Value":
                roce_value

            }

        )


# ------------------------------------------------------------
# Net Profit
# ------------------------------------------------------------

if "net_profit" in sector_data.columns:

    profit_value = (

        sector_data[
            "net_profit"
        ]
        .median()

    )


    if pd.notna(

        profit_value

    ):

        median_metrics.append(

            {

                "Metric":
                "Net Profit",

                "Median Value":
                profit_value

            }

        )


# ------------------------------------------------------------
# Debt-to-Equity
# ------------------------------------------------------------

if "debt_to_equity" in sector_data.columns:

    de_value = (

        sector_data[
            "debt_to_equity"
        ]
        .median()

    )


    if pd.notna(

        de_value

    ):

        median_metrics.append(

            {

                "Metric":
                "Debt-to-Equity",

                "Median Value":
                de_value

            }

        )


# ============================================================
# DISPLAY MEDIAN BAR CHART
# ============================================================

median_dataframe = pd.DataFrame(

    median_metrics

)


if median_dataframe.empty:

    st.warning(

        "Sector median metrics are not "
        "available."

    )


else:

    median_chart = px.bar(

        median_dataframe,

        x="Metric",

        y="Median Value",

        text="Median Value",

        title=(

            f"{selected_sector} — "
            "Median Financial Metrics"

        ),

        labels={

            "Median Value":
            "Median Value"

        }

    )


    median_chart.update_traces(

        texttemplate="%{text:,.2f}",

        textposition="outside"

    )


    median_chart.update_layout(

        height=550,

        showlegend=False,

        margin=dict(

            l=40,

            r=40,

            t=80,

            b=60

        )

    )


    st.plotly_chart(

        median_chart,

        use_container_width=True

    )


# ============================================================
# COMPANY TABLE
# ============================================================

st.divider()

st.subheader(

    f"🏢 Companies in {selected_sector}"

)


display_columns = [

    "company_id",

    "year",

    "sales",

    "net_profit",

    "roe_calculated",

    "roce_calculated",

    "debt_to_equity",

    "free_cash_flow"

]


available_display_columns = [

    column

    for column in display_columns

    if column in sector_data.columns

]


company_table = (

    sector_data[

        available_display_columns

    ]

    .sort_values(

        by="sales",

        ascending=False,

        na_position="last"

    )

    .reset_index(

        drop=True

    )

)


st.dataframe(

    company_table,

    use_container_width=True,

    hide_index=True

)


# ============================================================
# FOOTER
# ============================================================

st.caption(

    "The dashboard uses the latest available "
    "financial record for each company."

)