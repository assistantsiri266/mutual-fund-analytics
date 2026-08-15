from pathlib import Path
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException, Query

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
DATABASE = BASE_DIR / "database" / "financial_data.db"

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    description="FastAPI server for company financial analysis, screening, clustering and reports.",
    version="1.0.0",
)


# ============================================================
# DATABASE HELPER
# ============================================================

def get_connection():
    if not DATABASE.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Database not found: {DATABASE}"
        )

    return sqlite3.connect(DATABASE)


def fetch_all(query: str, params=()):
    con = get_connection()

    try:
        con.row_factory = sqlite3.Row
        rows = con.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def fetch_one(query: str, params=()):
    rows = fetch_all(query, params)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No matching record found"
        )

    return rows[0]


# ============================================================
# 1. HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "database": DATABASE.exists(),
        "database_path": str(DATABASE),
    }


# ============================================================
# 2. COMPANIES
# ============================================================

@app.get("/companies")
def companies():
    rows = fetch_all(
        """
        SELECT DISTINCT company_id
        FROM financial_ratios
        ORDER BY company_id
        """
    )

    return {
        "count": len(rows),
        "companies": [row["company_id"] for row in rows],
    }


# ============================================================
# 3. COMPANY PROFILE
# ============================================================

@app.get("/companies/{company_id}")
def company_profile(company_id: str):
    company_id = company_id.strip().upper()

    rows = fetch_all(
        """
        SELECT *
        FROM financial_ratios
        WHERE UPPER(TRIM(company_id)) = ?
        ORDER BY year
        """,
        (company_id,),
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Company not found: {company_id}"
        )

    return {
        "company_id": company_id,
        "years": len(rows),
        "data": rows,
    }


# ============================================================
# 4. FINANCIAL RATIOS
# ============================================================

@app.get("/companies/{company_id}/ratios")
def company_ratios(company_id: str):
    company_id = company_id.strip().upper()

    return {
        "company_id": company_id,
        "data": fetch_all(
            """
            SELECT
                company_id,
                year,
                roe_calculated,
                roce_calculated,
                roa_calculated,
                debt_to_equity,
                interest_coverage,
                asset_turnover,
                net_profit_margin_pct,
                operating_profit_margin_pct
            FROM financial_ratios
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY year
            """,
            (company_id,),
        ),
    }


# ============================================================
# 5. LATEST FINANCIAL DATA
# ============================================================

@app.get("/companies/{company_id}/latest")
def company_latest(company_id: str):
    company_id = company_id.strip().upper()

    return fetch_one(
        """
        SELECT *
        FROM financial_ratios
        WHERE UPPER(TRIM(company_id)) = ?
        ORDER BY year DESC
        LIMIT 1
        """,
        (company_id,),
    )


# ============================================================
# 6. PROFITABILITY
# ============================================================

@app.get("/companies/{company_id}/profitability")
def profitability(company_id: str):
    company_id = company_id.strip().upper()

    return {
        "company_id": company_id,
        "data": fetch_all(
            """
            SELECT
                company_id,
                year,
                sales,
                operating_profit,
                net_profit,
                roe_calculated,
                roce_calculated,
                roa_calculated,
                net_profit_margin_pct,
                operating_profit_margin_pct
            FROM financial_ratios
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY year
            """,
            (company_id,),
        ),
    }


# ============================================================
# 7. LEVERAGE
# ============================================================

@app.get("/companies/{company_id}/leverage")
def leverage(company_id: str):
    company_id = company_id.strip().upper()

    return {
        "company_id": company_id,
        "data": fetch_all(
            """
            SELECT
                company_id,
                year,
                borrowings,
                debt_to_equity,
                interest_coverage,
                net_debt,
                high_leverage_flag
            FROM financial_ratios
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY year
            """,
            (company_id,),
        ),
    }


# ============================================================
# 8. GROWTH
# ============================================================

@app.get("/companies/{company_id}/growth")
def growth(company_id: str):
    company_id = company_id.strip().upper()

    return {
        "company_id": company_id,
        "data": fetch_all(
            """
            SELECT
                company_id,
                year,
                sales,
                net_profit,
                eps,
                revenue_cagr_5yr,
                pat_cagr_5yr,
                eps_cagr_5yr
            FROM financial_ratios
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY year
            """,
            (company_id,),
        ),
    }


# ============================================================
# 9. CASH FLOW
# ============================================================

@app.get("/companies/{company_id}/cashflow")
def cashflow(company_id: str):
    company_id = company_id.strip().upper()

    return {
        "company_id": company_id,
        "data": fetch_all(
            """
            SELECT
                company_id,
                year,
                free_cash_flow,
                cfo_quality,
                capex_pct,
                capex_label,
                fcf_conversion
            FROM financial_ratios
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY year
            """,
            (company_id,),
        ),
    }


# ============================================================
# 10. CAPITAL ALLOCATION
# ============================================================

@app.get("/companies/{company_id}/capital-allocation")
def capital_allocation(company_id: str):
    company_id = company_id.strip().upper()

    return {
        "company_id": company_id,
        "data": fetch_all(
            """
            SELECT
                company_id,
                year,
                pattern_label
            FROM financial_ratios
            WHERE UPPER(TRIM(company_id)) = ?
            ORDER BY year
            """,
            (company_id,),
        ),
    }


# ============================================================
# 11. CLUSTER
# ============================================================

@app.get("/companies/{company_id}/cluster")
def company_cluster(company_id: str):
    company_id = company_id.strip().upper()

    cluster_file = BASE_DIR / "output" / "cluster_labels.csv"

    if not cluster_file.exists():
        raise HTTPException(
            status_code=404,
            detail="cluster_labels.csv not found"
        )

    import pandas as pd

    cluster_df = pd.read_csv(cluster_file)

    cluster_df["company_id"] = (
        cluster_df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    result = cluster_df[
        cluster_df["company_id"] == company_id
    ]

    if result.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Cluster not found for {company_id}"
        )

    return result.to_dict(orient="records")[0]


# ============================================================
# 12. SCREENING
# ============================================================

@app.get("/screen")
def screen(
    min_roe: Optional[float] = Query(None),
    max_de: Optional[float] = Query(None),
    min_roce: Optional[float] = Query(None),
):
    query = """
        SELECT
            company_id,
            year,
            roe_calculated,
            roce_calculated,
            debt_to_equity,
            net_profit_margin_pct
        FROM financial_ratios
        WHERE year = (
            SELECT MAX(year)
            FROM financial_ratios
        )
    """

    conditions = []
    params = []

    if min_roe is not None:
        conditions.append("roe_calculated >= ?")
        params.append(min_roe)

    if max_de is not None:
        conditions.append("debt_to_equity <= ?")
        params.append(max_de)

    if min_roce is not None:
        conditions.append("roce_calculated >= ?")
        params.append(min_roce)

    if conditions:
        query += " AND " + " AND ".join(conditions)

    query += " ORDER BY roe_calculated DESC"

    rows = fetch_all(query, params)

    return {
        "count": len(rows),
        "results": rows,
    }


# ============================================================
# 13. SECTOR SUMMARY
# ============================================================

@app.get("/sectors")
def sectors():
    return {
        "data": fetch_all(
            """
            SELECT
                broad_sector AS sector,
                COUNT(DISTINCT company_id) AS companies
            FROM financial_ratios
            WHERE broad_sector IS NOT NULL
            GROUP BY broad_sector
            ORDER BY companies DESC
            """
        )
    }


# ============================================================
# 14. SECTOR COMPANIES
# ============================================================

@app.get("/sectors/{sector}/companies")
def sector_companies(sector: str):
    return {
        "sector": sector,
        "companies": fetch_all(
            """
            SELECT DISTINCT company_id
            FROM financial_ratios
            WHERE LOWER(TRIM(broad_sector)) = LOWER(TRIM(?))
            ORDER BY company_id
            """,
            (sector,),
        ),
    }


# ============================================================
# 15. PEER COMPARISON
# ============================================================

@app.get("/peers/{company_id}")
def peers(
    company_id: str,
    limit: int = Query(10, ge=1, le=50),
):
    company_id = company_id.strip().upper()

    row = fetch_one(
        """
        SELECT broad_sector
        FROM financial_ratios
        WHERE UPPER(TRIM(company_id)) = ?
        ORDER BY year DESC
        LIMIT 1
        """,
        (company_id,),
    )

    sector = row["broad_sector"]

    rows = fetch_all(
        """
        SELECT
            company_id,
            broad_sector,
            roe_calculated,
            roce_calculated,
            debt_to_equity,
            net_profit_margin_pct
        FROM financial_ratios
        WHERE LOWER(TRIM(broad_sector)) = LOWER(TRIM(?))
          AND UPPER(TRIM(company_id)) != ?
          AND year = (
              SELECT MAX(year)
              FROM financial_ratios
          )
        ORDER BY roe_calculated DESC
        LIMIT ?
        """,
        (sector, company_id, limit),
    )

    return {
        "company_id": company_id,
        "sector": sector,
        "peers": rows,
    }


# ============================================================
# 16. DASHBOARD / SUMMARY
# ============================================================

@app.get("/summary")
def summary():
    companies_count = fetch_one(
        """
        SELECT COUNT(DISTINCT company_id) AS count
        FROM financial_ratios
        """
    )

    rows_count = fetch_one(
        """
        SELECT COUNT(*) AS count
        FROM financial_ratios
        """
    )

    sectors_count = fetch_one(
        """
        SELECT COUNT(DISTINCT broad_sector) AS count
        FROM financial_ratios
        WHERE broad_sector IS NOT NULL
        """
    )

    return {
        "project": "Nifty 100 Financial Intelligence",
        "companies": companies_count["count"],
        "financial_ratio_rows": rows_count["count"],
        "sectors": sectors_count["count"],
        "database": str(DATABASE),
    }