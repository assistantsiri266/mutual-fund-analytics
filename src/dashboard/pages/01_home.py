import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# ADD PROJECT ROOT TO PYTHON PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:

    sys.path.append(
        str(PROJECT_ROOT)
    )


# ============================================================
# IMPORT DATABASE FUNCTIONS
# ============================================================

from src.dashboard.utils.db import (
    get_all_ratios,
    get_latest_ratios
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title(
    "🏠 Nifty 100 Analytics Dashboard"
)

st.caption(
    "Financial quality, growth, leverage, "
    "cash-flow and company-level analytics"
)


# ============================================================
# LOAD DATA
# ============================================================

try:

    all_data = get_all_ratios()

    latest_data = get_latest_ratios()

except Exception as error:

    st.error(
        f"Unable to load dashboard data: {error}"
    )

    st.stop()


# ============================================================
# CHECK DATA
# ============================================================

if latest_data.empty:

    st.warning(
        "No financial data is available "
        "in the database."
    )

    st.stop()


# ============================================================
# CLEAN NUMERIC COLUMNS
# ============================================================

numeric_columns = [

    "roe_calculated",

    "debt_to_equity",

    "revenue_cagr_5yr",

    "free_cash_flow",

    "sales",

    "net_profit",

    "operating_profit_margin_pct",

    "roce_calculated",

    "interest_coverage"

]


for column in numeric_columns:

    if column in latest_data.columns:

        latest_data[column] = pd.to_numeric(

            latest_data[column],

            errors="coerce"

        )


# ============================================================
# SIDEBAR YEAR SELECTOR
# ============================================================

st.sidebar.header(
    "Dashboard Filters"
)


# Extract available years

all_data = all_data.copy()

all_data["year"] = (

    all_data["year"]

    .astype(str)

    .str.strip()

)


all_data["year_number"] = (

    all_data["year"]

    .str.extract(

        r"(\d{4})"

    )[0]

)


all_data["year_number"] = pd.to_numeric(

    all_data["year_number"],

    errors="coerce"

)


available_years = (

    all_data["year_number"]

    .dropna()

    .astype(int)

    .unique()

    .tolist()

)


available_years = sorted(

    available_years

)


# Keep only years from 2019 onward

dashboard_years = [

    year

    for year in available_years

    if year >= 2019

]


if dashboard_years:

    selected_year = st.sidebar.selectbox(

        "Select Financial Year",

        options=dashboard_years,

        index=len(dashboard_years) - 1

    )

else:

    selected_year = None


# ============================================================
# FILTER DATA BY SELECTED YEAR
# ============================================================

if selected_year is not None:

    selected_data = (

        all_data[

            all_data["year_number"]

            == selected_year

        ]

        .copy()

    )

else:

    selected_data = (

        latest_data.copy()

    )


# Remove duplicate company-year records

selected_data = (

    selected_data

    .drop_duplicates(

        subset=[

            "company_id",

            "year"

        ],

        keep="last"

    )

)


# ============================================================
# CONVERT SELECTED DATA TO NUMERIC
# ============================================================

for column in numeric_columns:

    if column in selected_data.columns:

        selected_data[column] = pd.to_numeric(

            selected_data[column],

            errors="coerce"

        )


# ============================================================
# CALCULATE HOME KPI VALUES
# ============================================================

average_roe = (

    selected_data[

        "roe_calculated"

    ].mean()

    if "roe_calculated"

    in selected_data.columns

    else None

)


median_de = (

    selected_data[

        "debt_to_equity"

    ].median()

    if "debt_to_equity"

    in selected_data.columns

    else None

)


median_revenue_cagr = (

    selected_data[

        "revenue_cagr_5yr"

    ].median()

    if "revenue_cagr_5yr"

    in selected_data.columns

    else None

)


total_companies = (

    selected_data[

        "company_id"

    ]

    .nunique()

)


debt_free_companies = (

    selected_data[

        selected_data[

            "debt_to_equity"

        ]

        == 0

    ]

    [

        "company_id"

    ]

    .nunique()

    if "debt_to_equity"

    in selected_data.columns

    else 0

)


# P/E is not currently available
# in your financial_ratios database

median_pe = None


# ============================================================
# DISPLAY KPI CARDS
# ============================================================

st.subheader(

    f"Financial Summary — {selected_year}"

    if selected_year

    else "Financial Summary"

)


kpi_1, kpi_2, kpi_3 = (

    st.columns(3)

)


kpi_4, kpi_5, kpi_6 = (

    st.columns(3)

)


kpi_1.metric(

    "Average ROE",

    f"{average_roe:.2f}%"

    if pd.notna(average_roe)

    else "N/A"

)


kpi_2.metric(

    "Median P/E",

    "N/A"

)


kpi_3.metric(

    "Median D/E",

    f"{median_de:.2f}"

    if pd.notna(median_de)

    else "N/A"

)


kpi_4.metric(

    "Total Companies",

    total_companies

)


kpi_5.metric(

    "Median Revenue CAGR",

    f"{median_revenue_cagr:.2f}%"

    if pd.notna(

        median_revenue_cagr

    )

    else "N/A"

)


kpi_6.metric(

    "Debt-Free Companies",

    debt_free_companies

)


# ============================================================
# INFORMATION ABOUT UNAVAILABLE P/E
# ============================================================

if median_pe is None:

    st.caption(

        "P/E is displayed as N/A because "

        "P/E data is not currently present "

        "in the SQLite financial_ratios table."

    )


# ============================================================
# SECTOR BREAKDOWN
# ============================================================

st.divider()

st.subheader(

    "Sector-wise Company Distribution"

)


sector_column = None


for possible_column in [

    "broad_sector",

    "sector",

    "industry",

    "sub_sector"

]:

    if possible_column in selected_data.columns:

        sector_column = (

            possible_column

        )

        break


if sector_column is not None:

    sector_data = (

        selected_data

        .dropna(

            subset=[

                sector_column

            ]

        )

        .groupby(

            sector_column

        )

        [

            "company_id"

        ]

        .nunique()

        .reset_index(

            name="company_count"

        )

    )


    figure = px.pie(

        sector_data,

        names=sector_column,

        values="company_count",

        hole=0.50,

        title="Company Count by Sector"

    )


    figure.update_traces(

        textposition="inside",

        textinfo="percent+label"

    )


    st.plotly_chart(

        figure,

        use_container_width=True

    )


else:

    st.info(

        "Sector information is not currently "

        "available in the financial_ratios table."

    )


# ============================================================
# TOP COMPANIES TABLE
# ============================================================

st.divider()

st.subheader(

    "Top 5 Companies by Financial Quality"

)


# Temporary quality score

score_data = (

    latest_data.copy()

)


score_metrics = [

    "roe_calculated",

    "roce_calculated",

    "revenue_cagr_5yr",

    "pat_cagr_5yr",

    "free_cash_flow"

]


available_score_metrics = [

    column

    for column in score_metrics

    if column

    in score_data.columns

]


if available_score_metrics:

    for column in available_score_metrics:

        score_data[column] = pd.to_numeric(

            score_data[column],

            errors="coerce"

        )


    score_data[

        "temporary_quality_score"

    ] = (

        score_data[

            available_score_metrics

        ]

        .rank(

            pct=True

        )

        .mean(

            axis=1

        )

        * 100

    )


    top_companies = (

        score_data

        .sort_values(

            by=(

                "temporary_quality_score"

            ),

            ascending=False

        )

        .head(5)

    )


    display_columns = [

        "company_id",

        "temporary_quality_score"

    ]


    for column in [

        "roe_calculated",

        "roce_calculated",

        "revenue_cagr_5yr",

        "pat_cagr_5yr",

        "free_cash_flow"

    ]:

        if column in top_companies.columns:

            display_columns.append(

                column

            )


    top_companies = (

        top_companies[

            display_columns

        ]

        .rename(

            columns={

                "temporary_quality_score":

                    "quality_score"

            }

        )

    )


    top_companies[

        "quality_score"

    ] = (

        top_companies[

            "quality_score"

        ]

        .round(2)

    )


    st.dataframe(

        top_companies,

        use_container_width=True,

        hide_index=True

    )


else:

    st.info(

        "The required financial metrics "

        "are not available for the "

        "quality ranking."

    )


# ============================================================
# DATA STATUS
# ============================================================

st.divider()

st.caption(

    f"Showing {total_companies} companies "

    f"for the selected year. "

    f"Database records loaded: "

    f"{len(all_data):,}"

)