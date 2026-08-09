import sqlite3
import pandas as pd
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE = BASE_DIR / "database" / "financial_data.db"
OUTPUT_DIR = BASE_DIR / "reports" / "portfolio"
OUTPUT_FILE = OUTPUT_DIR / "portfolio_summary.pdf"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("DAY 35 — PORTFOLIO SUMMARY")
print("=" * 70)

connection = sqlite3.connect(DATABASE)

df = pd.read_sql_query(
    "SELECT * FROM financial_ratios",
    connection
)

connection.close()

# Normalize
df["company_id"] = (
    df["company_id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df["year"] = df["year"].astype(str).str.strip()

# Remove duplicate company/year records
df = (
    df.sort_values(["company_id", "year"])
      .drop_duplicates(["company_id", "year"], keep="last")
)

companies = sorted(df["company_id"].unique())

print("Companies:", len(companies))


def trend_arrow(group, metric):
    values = pd.to_numeric(group[metric], errors="coerce").dropna()

    if len(values) < 2:
        return "→"

    latest = values.iloc[-1]
    previous = values.iloc[-2]

    if previous == 0:
        return "→"

    change = abs((latest - previous) / abs(previous))

    if change <= 0.02:
        return "→"

    if latest > previous:
        return "↑"

    return "↓"


# Top six KPIs
kpis = [
    ("ROE", "roe_calculated"),
    ("ROCE", "roce_calculated"),
    ("Net Profit Margin", "net_profit_margin_pct"),
    ("Debt to Equity", "debt_to_equity"),
    ("Interest Coverage", "interest_coverage"),
    ("Asset Turnover", "asset_turnover"),
]


styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "PortfolioTitle",
    parent=styles["Title"],
    alignment=TA_CENTER,
    fontSize=20,
    leading=24,
    spaceAfter=15,
)

company_style = ParagraphStyle(
    "Company",
    parent=styles["Heading1"],
    fontSize=18,
    leading=22,
    spaceAfter=8,
)

normal_style = ParagraphStyle(
    "NormalCustom",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
)

doc = SimpleDocTemplate(
    str(OUTPUT_FILE),
    pagesize=A4,
    rightMargin=40,
    leftMargin=40,
    topMargin=40,
    bottomMargin=40,
)

story = []

for index, company in enumerate(companies):

    company_df = df[df["company_id"] == company].copy()

    if company_df.empty:
        continue

    latest = company_df.iloc[-1]

    sector = (
        latest["broad_sector"]
        if "broad_sector" in company_df.columns
        else "N/A"
    )

    story.append(
        Paragraph(
            "Portfolio Company Summary",
            title_style
        )
    )

    story.append(
        Paragraph(
            company,
            company_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Sector:</b> {sector}",
            normal_style
        )
    )

    story.append(Spacer(1, 15))

    data = [
        ["KPI", "Latest Value", "Trend"]
    ]

    for label, column in kpis:

        if column not in company_df.columns:
            value = "N/A"
            arrow = "→"
        else:
            values = pd.to_numeric(
                company_df[column],
                errors="coerce"
            ).dropna()

            if len(values) == 0:
                value = "N/A"
                arrow = "→"
            else:
                latest_value = values.iloc[-1]

                if pd.isna(latest_value):
                    value = "N/A"
                else:
                    value = f"{latest_value:.2f}"

                arrow = trend_arrow(
                    company_df,
                    column
                )

        data.append([
            label,
            value,
            arrow
        ])

    table = Table(
        data,
        colWidths=[220, 120, 80]
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F2F2F2")]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(table)

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "<b>Trend legend:</b> ↑ Improved &nbsp;&nbsp; "
            "↓ Declined &nbsp;&nbsp; → Flat (within 2%)",
            normal_style
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            f"Latest available financial period: {latest['year']}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            "Generated from the project's financial_ratios dataset.",
            normal_style
        )
    )

    if index < len(companies) - 1:
        story.append(PageBreak())


doc.build(story)

print("\nPortfolio summary saved:")
print(OUTPUT_FILE)

print("\nPages expected:", len(companies))
print("DONE.")