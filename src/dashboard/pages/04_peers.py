import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Peer Comparison",
    page_icon="👥",
    layout="wide"
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = (
    PROJECT_ROOT
    / "database"
    / "financial_data.db"
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("👥 Peer Comparison")

st.caption(
    "Compare a company with other companies in its peer group."
)


# ============================================================
# DATABASE CHECK
# ============================================================

if not DB_PATH.exists():

    st.error(
        f"""
Database file was not found.

Expected database location:

{DB_PATH}
"""
    )

    st.stop()


# ============================================================
# LOAD PEER PERCENTILES
# ============================================================

@st.cache_data(ttl=600)
def load_peer_percentiles():

    connection = sqlite3.connect(
        str(DB_PATH)
    )

    try:

        dataframe = pd.read_sql_query(
            """
            SELECT *
            FROM peer_percentiles
            """,
            connection
        )

    finally:

        connection.close()

    return dataframe


# ============================================================
# LOAD LATEST FINANCIAL DATA
# ============================================================

@st.cache_data(ttl=600)
def load_latest_financial_data():

    connection = sqlite3.connect(
        str(DB_PATH)
    )

    try:

        dataframe = pd.read_sql_query(
            """
            SELECT *
            FROM financial_ratios
            """,
            connection
        )

    finally:

        connection.close()

    if dataframe.empty:

        return dataframe

    # --------------------------------------------------------
    # Convert year values such as:
    # Mar 2024
    # Dec 2023
    # 2024
    # --------------------------------------------------------

    dataframe["year_number"] = (
        dataframe["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0]
    )

    dataframe["year_number"] = pd.to_numeric(
        dataframe["year_number"],
        errors="coerce"
    )

    dataframe = dataframe.dropna(
        subset=["year_number"]
    )

    # --------------------------------------------------------
    # Keep latest year for every company
    # --------------------------------------------------------

    dataframe = dataframe.sort_values(
        by=[
            "company_id",
            "year_number"
        ]
    )

    latest_dataframe = (
        dataframe
        .groupby(
            "company_id",
            as_index=False
        )
        .tail(1)
        .copy()
    )

    latest_dataframe = (
        latest_dataframe
        .drop(
            columns=["year_number"]
        )
        .reset_index(
            drop=True
        )
    )

    return latest_dataframe


# ============================================================
# LOAD DATA
# ============================================================

try:

    peer_percentiles = (
        load_peer_percentiles()
    )

    latest_data = (
        load_latest_financial_data()
    )

except Exception as error:

    st.error(
        f"Unable to load database data: {error}"
    )

    st.stop()


# ============================================================
# CHECK PEER DATA
# ============================================================

if peer_percentiles.empty:

    st.warning(
        """
The `peer_percentiles` table exists,
but it does not contain any data.
"""
    )

    st.stop()


# ============================================================
# CHECK REQUIRED COLUMN
# ============================================================

if (
    "peer_group"
    not in peer_percentiles.columns
):

    st.error(
        """
The `peer_percentiles` table does not contain
the `peer_group` column.
"""
    )

    st.write(
        "Available columns:"
    )

    st.write(
        peer_percentiles.columns.tolist()
    )

    st.stop()


# ============================================================
# GET PEER GROUPS
# ============================================================

peer_groups = sorted(

    peer_percentiles[
        "peer_group"
    ]
    .dropna()
    .astype(str)
    .unique()
    .tolist()

)


# ============================================================
# PEER GROUP DROPDOWN
# ============================================================

selected_group = st.selectbox(

    "Select Peer Group",

    peer_groups

)


# ============================================================
# FILTER SELECTED PEER GROUP
# ============================================================

selected_peer_data = (

    peer_percentiles[

        peer_percentiles[
            "peer_group"
        ]
        .astype(str)
        == selected_group

    ]
    .copy()

)


# ============================================================
# CHECK COMPANY COLUMN
# ============================================================

if (
    "company_id"
    not in selected_peer_data.columns
):

    st.error(
        """
The peer data does not contain
the `company_id` column.
"""
    )

    st.stop()


# ============================================================
# GET COMPANIES
# ============================================================

peer_companies = sorted(

    selected_peer_data[
        "company_id"
    ]
    .dropna()
    .astype(str)
    .unique()
    .tolist()

)


if not peer_companies:

    st.warning(
        "No companies are available in this peer group."
    )

    st.stop()


# ============================================================
# COMPANY DROPDOWN
# ============================================================

selected_company = st.selectbox(

    "Select Company",

    peer_companies

)


# ============================================================
# SELECT COMPANY DATA
# ============================================================

company_peer_data = (

    selected_peer_data[

        selected_peer_data[
            "company_id"
        ]
        .astype(str)
        == selected_company

    ]
    .copy()

)


# ============================================================
# AVAILABLE METRICS
# ============================================================

metric_column = None

for possible_column in [

    "metric",
    "metric_name"

]:

    if (
        possible_column
        in company_peer_data.columns
    ):

        metric_column = (
            possible_column
        )

        break


# ============================================================
# PERCENTILE COLUMN
# ============================================================

percentile_column = None

for possible_column in [

    "percentile_rank",
    "percentile"

]:

    if (
        possible_column
        in company_peer_data.columns
    ):

        percentile_column = (
            possible_column
        )

        break


# ============================================================
# RADAR CHART
# ============================================================

st.subheader(
    "📊 Company vs Peer Group"
)


if (
    metric_column is not None
    and percentile_column is not None
):

    # --------------------------------------------------------
    # Convert percentile values to numeric
    # --------------------------------------------------------

    company_peer_data[
        percentile_column
    ] = pd.to_numeric(

        company_peer_data[
            percentile_column
        ],

        errors="coerce"

    )


    # --------------------------------------------------------
    # Get company percentile values
    # --------------------------------------------------------

    radar_data = (

        company_peer_data[

            [
                metric_column,
                percentile_column
            ]

        ]

        .dropna()

        .drop_duplicates(
            subset=[
                metric_column
            ]
        )

    )


    if not radar_data.empty:

        metrics = (

            radar_data[
                metric_column
            ]
            .astype(str)
            .tolist()

        )


        company_values = (

            radar_data[
                percentile_column
            ]
            .fillna(0)
            .tolist()

        )


        # ----------------------------------------------------
        # Convert 0–1 percentile to 0–100
        # ----------------------------------------------------

        if (
            max(company_values)
            <= 1
        ):

            company_values = [

                value * 100

                for value
                in company_values

            ]


        # ----------------------------------------------------
        # Close radar polygon
        # ----------------------------------------------------

        metrics_closed = (

            metrics
            + [metrics[0]]

        )


        company_values_closed = (

            company_values
            + [company_values[0]]

        )


        # ----------------------------------------------------
        # Peer average reference
        # ----------------------------------------------------

        peer_average = [50] * len(
            metrics
        )

        peer_average_closed = (

            peer_average
            + [peer_average[0]]

        )


        # ----------------------------------------------------
        # Create radar chart
        # ----------------------------------------------------

        figure = go.Figure()


        figure.add_trace(

            go.Scatterpolar(

                r=company_values_closed,

                theta=metrics_closed,

                fill="toself",

                name=selected_company

            )

        )


        figure.add_trace(

            go.Scatterpolar(

                r=peer_average_closed,

                theta=metrics_closed,

                mode="lines",

                name="Peer Average"

            )

        )


        figure.update_layout(

            polar={

                "radialaxis": {

                    "visible": True,

                    "range": [
                        0,
                        100
                    ]

                }

            },

            showlegend=True,

            height=550,

            margin={

                "l": 40,

                "r": 40,

                "t": 40,

                "b": 40

            }

        )


        st.plotly_chart(

            figure,

            use_container_width=True

        )


    else:

        st.info(
            """
No valid percentile values are available
for the selected company.
"""
        )


else:

    st.info(
        """
Metric and percentile columns were not found.

Available columns are shown below.
"""
    )

    st.write(
        selected_peer_data.columns.tolist()
    )


# ============================================================
# PEER COMPANY TABLE
# ============================================================

st.divider()

st.subheader(
    f"🏢 Companies in {selected_group}"
)


# ============================================================
# CREATE WIDE PEER TABLE
# ============================================================

if (

    metric_column is not None

    and percentile_column is not None

):

    peer_table = (

        selected_peer_data

        .pivot_table(

            index="company_id",

            columns=metric_column,

            values=percentile_column,

            aggfunc="first"

        )

        .reset_index()

    )


    peer_table.columns.name = None


    # --------------------------------------------------------
    # Convert percentiles to percentages
    # --------------------------------------------------------

    metric_columns = [

        column

        for column

        in peer_table.columns

        if column != "company_id"

    ]


    for column in metric_columns:

        peer_table[column] = pd.to_numeric(

            peer_table[column],

            errors="coerce"

        )


        if (

            peer_table[
                column
            ]
            .dropna()
            .max()

            <= 1

        ):

            peer_table[
                column
            ] = (

                peer_table[
                    column
                ]
                * 100

            )


        peer_table[
            column
        ] = (

            peer_table[
                column
            ]
            .round(2)

        )


    # --------------------------------------------------------
    # Highlight selected company
    # --------------------------------------------------------

    def highlight_selected_company(row):

        if (

            str(
                row["company_id"]
            )

            == str(
                selected_company
            )

        ):

            return [

                "background-color: #FFD966"

            ] * len(
                row
            )


        return [

            ""

        ] * len(
            row
        )


    styled_table = (

        peer_table

        .style

        .apply(

            highlight_selected_company,

            axis=1

        )

    )


    st.dataframe(

        styled_table,

        use_container_width=True,

        hide_index=True

    )


else:

    st.dataframe(

        selected_peer_data,

        use_container_width=True,

        hide_index=True

    )


# ============================================================
# PAGE FOOTER
# ============================================================

st.caption(

    f"Peer group: {selected_group} | "

    f"Companies: {len(peer_companies)}"

)