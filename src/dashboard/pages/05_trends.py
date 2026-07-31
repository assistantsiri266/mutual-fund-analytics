import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("📈 Trend Analysis")

st.caption(
    "Analyze company financial trends and compare up to "
    "three metrics over available financial years."
)


# ============================================================
# LOAD COMPANY LIST
# ============================================================

companies_df = get_companies()

if companies_df.empty:

    st.error(
        "No company data is available in the database."
    )

    st.stop()


company_list = (
    companies_df["company_id"]
    .dropna()
    .astype(str)
    .sort_values()
    .unique()
    .tolist()
)


# ============================================================
# COMPANY SEARCH / SELECT
# ============================================================

selected_company = st.selectbox(
    "Search or select a company ticker",
    options=company_list,
    index=0
)


# ============================================================
# LOAD COMPANY DATA
# ============================================================

company_data = get_ratios(
    selected_company
).copy()


if company_data.empty:

    st.warning(
        f"No financial data is available for "
        f"{selected_company}."
    )

    st.stop()


# ============================================================
# PREPARE FINANCIAL YEAR
# ============================================================

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


company_data = company_data.dropna(
    subset=["year_number"]
)


company_data = company_data.sort_values(
    "year_number"
)


if company_data.empty:

    st.warning(
        "The selected company does not contain "
        "valid financial-year information."
    )

    st.stop()


# ============================================================
# AVAILABLE METRICS
# ============================================================

metric_options = {
    "Revenue / Sales": "sales",
    "Net Profit": "net_profit",
    "Operating Profit": "operating_profit",
    "ROE (%)": "roe_calculated",
    "ROCE (%)": "roce_calculated",
    "Net Profit Margin (%)": "net_profit_margin_pct",
    "Operating Profit Margin (%)": (
        "operating_profit_margin_pct"
    ),
    "Debt-to-Equity": "debt_to_equity",
    "Free Cash Flow": "free_cash_flow",
    "Asset Turnover": "asset_turnover",
    "Revenue CAGR — 5 Year (%)": (
        "revenue_cagr_5yr"
    ),
    "PAT CAGR — 5 Year (%)": (
        "pat_cagr_5yr"
    ),
    "EPS CAGR — 5 Year (%)": (
        "eps_cagr_5yr"
    ),
}


# Keep only metrics available in the database
available_metrics = {
    display_name: column_name
    for display_name, column_name
    in metric_options.items()
    if column_name in company_data.columns
}


if not available_metrics:

    st.error(
        "None of the Trend Analysis metrics "
        "are available in the database."
    )

    st.stop()


# ============================================================
# MULTI-METRIC SELECTOR
# ============================================================

selected_metric_names = st.multiselect(
    "Select up to 3 metrics",
    options=list(
        available_metrics.keys()
    ),
    default=list(
        available_metrics.keys()
    )[:2],
    max_selections=3
)


if not selected_metric_names:

    st.info(
        "Please select at least one metric."
    )

    st.stop()


selected_columns = [
    available_metrics[name]
    for name in selected_metric_names
]


# ============================================================
# CONVERT SELECTED METRICS TO NUMERIC
# ============================================================

for column in selected_columns:

    company_data[column] = pd.to_numeric(
        company_data[column],
        errors="coerce"
    )


# ============================================================
# DISPLAY DATA AVAILABILITY
# ============================================================

available_years = (
    company_data["year_number"]
    .dropna()
    .astype(int)
    .tolist()
)


st.info(
    f"Data available for **{selected_company}**: "
    f"{len(available_years)} financial years "
    f"from **{min(available_years)}** "
    f"to **{max(available_years)}**."
)


if len(available_years) < 10:

    st.warning(
        "This company has fewer than 10 years "
        "of available data. The chart displays "
        "all available years."
    )


# ============================================================
# CREATE TREND CHART
# ============================================================

figure = go.Figure()


for metric_name in selected_metric_names:

    column = available_metrics[
        metric_name
    ]

    metric_data = company_data[
        [
            "year",
            "year_number",
            column
        ]
    ].dropna(
        subset=[column]
    ).copy()


    if metric_data.empty:

        continue


    # Calculate year-over-year percentage change
    metric_data["yoy_change"] = (
        metric_data[column]
        .pct_change()
        .mul(100)
    )


    # Create annotation text
    annotation_text = []


    for yoy_value in metric_data[
        "yoy_change"
    ]:

        if pd.isna(yoy_value):

            annotation_text.append(
                "First available year"
            )

        else:

            annotation_text.append(
                f"YoY: {yoy_value:.1f}%"
            )


    # Add metric line
    figure.add_trace(

        go.Scatter(

            x=metric_data["year"],

            y=metric_data[column],

            mode=(
                "lines+markers"
            ),

            name=metric_name,

            text=annotation_text,

            hovertemplate=(

                "<b>"
                + metric_name
                + "</b><br>"

                + "Year: %{x}<br>"

                + "Value: %{y:,.2f}<br>"

                + "%{text}"

                + "<extra></extra>"
            )

        )

    )


# ============================================================
# CHART LAYOUT
# ============================================================

figure.update_layout(

    title=(

        f"{selected_company} — "
        "Financial Trend"
    ),

    xaxis_title=(
        "Financial Year"
    ),

    yaxis_title=(
        "Metric Value"
    ),

    height=600,

    hovermode="x unified",

    legend_title=(
        "Selected Metrics"
    ),

    margin=dict(
        l=40,
        r=40,
        t=80,
        b=60
    )

)


figure.update_xaxes(

    type="category",

    tickangle=0

)


st.plotly_chart(

    figure,

    use_container_width=True

)


# ============================================================
# YEAR-OVER-YEAR CHANGE TABLE
# ============================================================

st.subheader(
    "📊 Year-over-Year Change"
)


yoy_table = company_data[
    [
        "year"
    ] + selected_columns
].copy()


for column in selected_columns:

    yoy_table[
        f"{column}_yoy_pct"
    ] = (

        yoy_table[column]
        .pct_change()
        .mul(100)

    )


# Rename columns for display
display_names = {

    "year": "Financial Year"

}


for metric_name in selected_metric_names:

    column = available_metrics[
        metric_name
    ]

    display_names[
        column
    ] = metric_name

    display_names[
        f"{column}_yoy_pct"
    ] = (

        f"{metric_name} "
        "YoY Change (%)"

    )


yoy_table = yoy_table.rename(
    columns=display_names
)


st.dataframe(

    yoy_table,

    use_container_width=True,

    hide_index=True

)


# ============================================================
# FOOTER
# ============================================================

st.caption(

    "YoY change is calculated as: "
    "((Current Year − Previous Year) / "
    "Previous Year) × 100."

)