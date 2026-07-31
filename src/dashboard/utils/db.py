import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


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
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a connection to the SQLite database.
    """

    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database file not found:\n{DB_PATH}"
        )

    return sqlite3.connect(DB_PATH)


# ============================================================
# GENERAL DATABASE QUERY
# ============================================================

@st.cache_data(ttl=600)
def run_query(query, params=None):
    """
    Run an SQL query and return the result
    as a pandas DataFrame.

    Cache duration:
    600 seconds = 10 minutes
    """

    connection = get_connection()

    try:
        dataframe = pd.read_sql_query(
            query,
            connection,
            params=params
        )

    finally:
        connection.close()

    return dataframe


# ============================================================
# GET ALL COMPANIES
# ============================================================

@st.cache_data(ttl=600)
def get_companies():
    """
    Return all unique company IDs available
    in the financial_ratios table.
    """

    query = """
        SELECT DISTINCT
            company_id
        FROM financial_ratios
        WHERE company_id IS NOT NULL
        ORDER BY company_id
    """

    return run_query(query)


# ============================================================
# GET ALL FINANCIAL RATIOS
# ============================================================

@st.cache_data(ttl=600)
def get_all_ratios():
    """
    Return all records from the
    financial_ratios table.
    """

    query = """
        SELECT *
        FROM financial_ratios
    """

    return run_query(query)


# ============================================================
# GET COMPANY RATIOS
# ============================================================

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Return financial ratios for a company.

    If year is provided:
        Return data only for that year.

    If year is None:
        Return all available years.
    """

    if year is None:

        query = """
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year
        """

        return run_query(
            query,
            params=(ticker,)
        )

    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
        AND year = ?
    """

    return run_query(
        query,
        params=(ticker, year)
    )


# ============================================================
# GET PROFIT AND LOSS DATA
# ============================================================

@st.cache_data(ttl=600)
def get_pl(ticker):
    """
    Return Profit and Loss information
    for the selected company.
    """

    query = """
        SELECT
            company_id,
            year,
            sales,
            expenses,
            operating_profit,
            other_income,
            interest,
            depreciation,
            profit_before_tax,
            net_profit,
            eps,
            dividend_payout
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year
    """

    return run_query(
        query,
        params=(ticker,)
    )


# ============================================================
# GET BALANCE SHEET DATA
# ============================================================

@st.cache_data(ttl=600)
def get_bs(ticker):
    """
    Return Balance Sheet information
    for the selected company.
    """

    query = """
        SELECT
            company_id,
            year,
            equity_capital,
            reserves,
            borrowings,
            other_liabilities,
            total_liabilities,
            fixed_assets,
            cwip,
            investments,
            other_asset,
            total_assets
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year
    """

    return run_query(
        query,
        params=(ticker,)
    )


# ============================================================
# GET CASH FLOW DATA
# ============================================================

@st.cache_data(ttl=600)
def get_cf(ticker):
    """
    Return Cash Flow KPI information
    for the selected company.
    """

    query = """
        SELECT
            company_id,
            year,
            free_cash_flow,
            cfo_quality,
            capex_pct,
            capex_label,
            fcf_conversion,
            pattern_label
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year
    """

    return run_query(
        query,
        params=(ticker,)
    )


# ============================================================
# GET AVAILABLE YEARS
# ============================================================

@st.cache_data(ttl=600)
def get_years():
    """
    Return all available financial years.
    """

    query = """
        SELECT DISTINCT
            year
        FROM financial_ratios
        WHERE year IS NOT NULL
        ORDER BY year
    """

    return run_query(query)


# ============================================================
# GET LATEST FINANCIAL DATA
# ============================================================

@st.cache_data(ttl=600)
def get_latest_ratios():
    """
    Return the latest available financial record
    for every company.

    The latest year is selected separately
    for each company.
    """

    dataframe = get_all_ratios().copy()

    if dataframe.empty:
        return dataframe

    # Convert year to text
    dataframe["year"] = (
        dataframe["year"]
        .astype(str)
        .str.strip()
    )

    # Extract the 4-digit year from values such as:
    # Dec 2012, Mar 2024, or 2024
    dataframe["year_number"] = (
        dataframe["year"]
        .str.extract(
            r"(\d{4})"
        )[0]
    )

    # Convert extracted year to numeric
    dataframe["year_number"] = pd.to_numeric(
        dataframe["year_number"],
        errors="coerce"
    )

    # Remove rows with invalid years
    dataframe = dataframe.dropna(
        subset=["year_number"]
    )

    # Sort each company from oldest to newest
    dataframe = dataframe.sort_values(
        by=[
            "company_id",
            "year_number"
        ]
    )

    # Keep only the latest row for every company
    latest_dataframe = (
        dataframe
        .groupby(
            "company_id",
            as_index=False
        )
        .tail(1)
        .copy()
    )

    # Remove temporary column
    latest_dataframe.drop(
        columns=["year_number"],
        inplace=True
    )

    # Reset row numbers
    latest_dataframe.reset_index(
        drop=True,
        inplace=True
    )

    return latest_dataframe


# ============================================================
# GET SECTORS
# ============================================================

@st.cache_data(ttl=600)
def get_sectors():
    """
    Return available broad sectors.

    If broad_sector is not available
    in the database, return an empty DataFrame.
    """

    dataframe = get_all_ratios()

    if "broad_sector" not in dataframe.columns:

        return pd.DataFrame(
            columns=["broad_sector"]
        )

    sectors = (
        dataframe[
            ["broad_sector"]
        ]
        .dropna()
        .drop_duplicates()
        .sort_values(
            by="broad_sector"
        )
        .reset_index(
            drop=True
        )
    )

    return sectors


# ============================================================
# GET PEER GROUP DATA
# ============================================================

@st.cache_data(ttl=600)
def get_peers(group_name):
    """
    Return peer group data from the
    peer_percentiles table.

    If the table does not exist,
    return an empty DataFrame.
    """

    connection = get_connection()

    try:

        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """,
            connection
        )

        if (
            "peer_percentiles"
            not in tables["name"].tolist()
        ):

            return pd.DataFrame()

        query = """
            SELECT *
            FROM peer_percentiles
            WHERE peer_group_name = ?
        """

        dataframe = pd.read_sql_query(
            query,
            connection,
            params=(group_name,)
        )

    finally:

        connection.close()

    return dataframe


# ============================================================
# GET VALUATION DATA
# ============================================================

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Return valuation data for a company.

    If the valuation table does not exist,
    return an empty DataFrame.
    """

    connection = get_connection()

    try:

        tables = pd.read_sql_query(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """,
            connection
        )

        if (
            "valuation"
            not in tables["name"].tolist()
        ):

            return pd.DataFrame()

        query = """
            SELECT *
            FROM valuation
            WHERE company_id = ?
        """

        dataframe = pd.read_sql_query(
            query,
            connection,
            params=(ticker,)
        )

    finally:

        connection.close()

    return dataframe


# ============================================================
# TEST THE DATABASE UTILITY
# ============================================================

if __name__ == "__main__":

    print("=" * 60)

    print("DATABASE PATH")

    print(DB_PATH)

    print()

    print(
        "DATABASE EXISTS:",
        DB_PATH.exists()
    )

    print("=" * 60)

    # Test company data
    companies = get_companies()

    print("\nTOTAL COMPANIES:")

    print(
        companies.shape[0]
    )

    print("\nFIRST 10 COMPANIES:")

    print(
        companies.head(10)
    )

    # Test all financial ratios
    all_ratios = get_all_ratios()

    print("\nTOTAL FINANCIAL RATIO ROWS:")

    print(
        all_ratios.shape[0]
    )

    # Test latest company records
    latest_ratios = get_latest_ratios()

    print("\nLATEST COMPANY RECORDS:")

    print(
        latest_ratios.shape[0]
    )

    print("\nLATEST DATA PREVIEW:")

    print(
        latest_ratios[
            [
                "company_id",
                "year"
            ]
        ].head(10)
    )

    print(
        "\nDATABASE UTILITY TEST COMPLETED!"
    )