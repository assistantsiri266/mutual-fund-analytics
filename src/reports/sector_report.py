import sqlite3
import pandas as pd
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

BASE_DIR = Path(__file__).resolve().parents[2]
DB = BASE_DIR / "database" / "financial_data.db"

TEAR_DIR = BASE_DIR / "reports" / "tearsheets"
SECTOR_DIR = BASE_DIR / "reports" / "sector"
SKIPPED = BASE_DIR / "output" / "skipped_tearsheets.csv"

TEAR_DIR.mkdir(parents=True, exist_ok=True)
SECTOR_DIR.mkdir(parents=True, exist_ok=True)
SKIPPED.parent.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("DAY 34 — BATCH REPORT GENERATION")
print("=" * 80)

con = sqlite3.connect(DB)

df = pd.read_sql_query(
    "SELECT * FROM financial_ratios",
    con
)

con.close()

df["company_id"] = (
    df["company_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["year"] = df["year"].astype(str).str.strip()

df = df[
    (df["company_id"] != "")
    & (df["company_id"] != "NAN")
    & (df["year"] != "")
    & (df["year"] != "NAN")
].copy()

df = (
    df.sort_values(["company_id", "year"])
      .drop_duplicates(["company_id", "year"], keep="last")
)

print("Financial-ratio rows:", len(df))
print("Companies:", df["company_id"].nunique())

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleCustom",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=18,
    spaceAfter=12
)

heading_style = ParagraphStyle(
    "HeadingCustom",
    parent=styles["Heading2"],
    fontSize=12,
    spaceBefore=8,
    spaceAfter=6
)

normal_style = styles["BodyText"]

METRICS = [
    ("ROE", "roe_calculated"),
    ("ROCE", "roce_calculated"),
    ("Net Profit Margin", "net_profit_margin_pct"),
    ("Debt / Equity", "debt_to_equity"),
    ("Free Cash Flow", "free_cash_flow"),
    ("PAT CAGR", "pat_cagr_5yr"),
    ("Revenue CAGR", "revenue_cagr_5yr"),
    ("Interest Coverage", "interest_coverage"),
]

def fmt(value):
    if pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.2f}"
    except:
        return str(value)

def make_company_pdf(company, company_df):

    path = TEAR_DIR / f"{company}_tearsheet.pdf"

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    story = []

    story.append(
        Paragraph(
            f"{company} — Investment Tearsheet",
            title_style
        )
    )

    years = sorted(company_df["year"].unique())

    story.append(
        Paragraph(
            f"Available periods: {len(years)} | "
            f"From {years[0]} to {years[-1]}",
            normal_style
        )
    )

    story.append(Spacer(1, 12))

    # Latest record
    latest = company_df.iloc[-1]

    story.append(
        Paragraph("Latest Financial Snapshot", heading_style)
    )

    snapshot = [
        ["Metric", "Latest Value"],
    ]

    for label, col in METRICS:
        if col in company_df.columns:
            snapshot.append(
                [label, fmt(latest[col])]
            )

    table = Table(
        snapshot,
        colWidths=[250, 200],
        repeatRows=1
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f4e78")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1),
             [colors.whitesmoke, colors.lightgrey]),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 6),
        ])
    )

    story.append(table)
    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Historical KPI Data",
            heading_style
        )
    )

    history = [["Year"] + [x[0] for x in METRICS]]

    for _, row in company_df.iterrows():

        values = [row["year"]]

        for _, col in METRICS:
            values.append(
                fmt(row[col]) if col in company_df.columns else "N/A"
            )

        history.append(values)

    history_table = Table(
        history,
        repeatRows=1,
        colWidths=[65] + [55] * 8
    )

    history_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f4e78")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
            ("FONTSIZE", (0,0), (-1,-1), 6.5),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1),
             [colors.white, colors.whitesmoke]),
        ])
    )

    story.append(history_table)

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "Note: This tearsheet is generated from the project's "
            "financial_ratios dataset.",
            styles["Italic"]
        )
    )

    doc.build(story)

    return path


# ============================================================
# COMPANY TEARSHEETS
# ============================================================

companies = sorted(df["company_id"].unique())

skipped = []
generated = []

print("\nGenerating company tearsheets...")

for company in companies:

    company_df = df[df["company_id"] == company].copy()

    if len(company_df) < 3:
        skipped.append({
            "company_id": company,
            "years_available": len(company_df),
            "reason": "Fewer than 3 years of data"
        })
        continue

    try:
        path = make_company_pdf(company, company_df)
        generated.append(company)
        print("PASS:", company)

    except Exception as e:
        skipped.append({
            "company_id": company,
            "years_available": len(company_df),
            "reason": f"Generation error: {e}"
        })
        print("FAIL:", company, e)


pd.DataFrame(skipped).to_csv(
    SKIPPED,
    index=False
)

print("\nCompany tearsheets generated:", len(generated))
print("Skipped:", len(skipped))
print("Skipped file:", SKIPPED)


# ============================================================
# SECTOR REPORTS
# ============================================================

if "broad_sector" not in df.columns:
    print("\nWARNING: broad_sector column not available.")
else:

    print("\nGenerating sector reports...")

    sectors = sorted(
        df["broad_sector"]
        .dropna()
        .astype(str)
        .unique()
    )

    print("Sectors:", len(sectors))

    for sector in sectors:

        sdf = df[df["broad_sector"] == sector].copy()

        sector_name = (
            sector.replace("/", "_")
                  .replace("\\", "_")
                  .replace(" ", "_")
        )

        path = SECTOR_DIR / f"{sector_name}_report.pdf"

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        story = []

        story.append(
            Paragraph(
                f"{sector} — Sector Report",
                title_style
            )
        )

        companies_sector = sorted(
            sdf["company_id"].unique()
        )

        story.append(
            Paragraph(
                f"Companies in sector: {len(companies_sector)}",
                normal_style
            )
        )

        story.append(Spacer(1, 12))

        story.append(
            Paragraph(
                "Sector Median KPIs",
                heading_style
            )
        )

        median_table = [["Metric", "Sector Median"]]

        for label, col in METRICS:

            if col in sdf.columns:

                values = pd.to_numeric(
                    sdf[col],
                    errors="coerce"
                )

                median_table.append(
                    [label, fmt(values.median())]
                )

        mt = Table(
            median_table,
            colWidths=[250, 200],
            repeatRows=1
        )

        mt.setStyle(
            TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f4e78")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
                ("FONTSIZE", (0,0), (-1,-1), 8),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [colors.white, colors.whitesmoke]),
            ])
        )

        story.append(mt)
        story.append(Spacer(1, 15))

        story.append(
            Paragraph(
                "Company KPI Summary",
                heading_style
            )
        )

        company_table = [
            ["Company"] + [x[0] for x in METRICS]
        ]

        for company in companies_sector:

            latest_rows = sdf[
                sdf["company_id"] == company
            ].sort_values("year")

            if latest_rows.empty:
                continue

            row = latest_rows.iloc[-1]

            company_table.append(
                [company] +
                [
                    fmt(row[col]) if col in sdf.columns else "N/A"
                    for _, col in METRICS
                ]
            )

        ct = Table(
            company_table,
            repeatRows=1,
            colWidths=[75] + [52] * 8
        )

        ct.setStyle(
            TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1f4e78")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("GRID", (0,0), (-1,-1), 0.3, colors.grey),
                ("FONTSIZE", (0,0), (-1,-1), 6.5),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [colors.white, colors.whitesmoke]),
            ])
        )

        story.append(ct)

        doc.build(story)

        print("SECTOR PASS:", sector)

print("\n" + "=" * 80)
print("DAY 34 GENERATION COMPLETE")
print("=" * 80)
