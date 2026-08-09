import sqlite3
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "database" / "financial_data.db"
TEAR_DIR = BASE_DIR / "reports" / "tearsheets"
SKIPPED = BASE_DIR / "output" / "skipped_tearsheets.csv"
CHART_DIR = BASE_DIR / "output" / "tearsheet_charts"

TEAR_DIR.mkdir(parents=True, exist_ok=True)
SKIPPED.parent.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("DAY 35 — 2-PAGE TEARSHEET GENERATION")
print("=" * 70)

con = sqlite3.connect(DB)
df = pd.read_sql_query("SELECT * FROM financial_ratios", con)
con.close()

df["company_id"] = (
    df["company_id"].astype(str).str.strip().str.upper()
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
    leading=21,
    spaceAfter=6,
)

company_style = ParagraphStyle(
    "CompanyCustom",
    parent=styles["Heading1"],
    fontSize=16,
    leading=19,
    spaceAfter=5,
)

heading_style = ParagraphStyle(
    "HeadingCustom",
    parent=styles["Heading2"],
    fontSize=10,
    leading=12,
    spaceBefore=4,
    spaceAfter=4,
)

normal_style = ParagraphStyle(
    "NormalCustom",
    parent=styles["BodyText"],
    fontSize=8,
    leading=10,
)

small_style = ParagraphStyle(
    "SmallCustom",
    parent=styles["BodyText"],
    fontSize=6.5,
    leading=8,
)

KPI_COLUMNS = [
    ("ROE", "roe_calculated"),
    ("ROCE", "roce_calculated"),
    ("Net Profit Margin", "net_profit_margin_pct"),
    ("Debt / Equity", "debt_to_equity"),
    ("Interest Coverage", "interest_coverage"),
    ("Asset Turnover", "asset_turnover"),
]

HISTORY_COLUMNS = [
    ("Revenue", "sales"),
    ("Operating Profit", "operating_profit"),
    ("Net Profit", "net_profit"),
    ("ROE", "roe_calculated"),
    ("ROCE", "roce_calculated"),
    ("Debt / Equity", "debt_to_equity"),
    ("Interest Coverage", "interest_coverage"),
]


def fmt(value):
    if pd.isna(value):
        return "N/A"
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return str(value)


def trend_arrow(group, column):
    if column not in group.columns:
        return "→"

    values = pd.to_numeric(
        group[column], errors="coerce"
    ).dropna()

    if len(values) < 2:
        return "→"

    previous = values.iloc[-2]
    latest = values.iloc[-1]

    if previous == 0:
        return "→"

    change = abs((latest - previous) / abs(previous))

    if change <= 0.02:
        return "→"

    return "↑" if latest > previous else "↓"


def make_charts(company, company_df):

    safe = (
        company.replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace("&", "and")
    )

    chart1 = CHART_DIR / f"{safe}_profit.png"
    chart2 = CHART_DIR / f"{safe}_ratios.png"

    years = company_df["year"].astype(str).tolist()

    revenue = pd.to_numeric(
        company_df["sales"], errors="coerce"
    )

    profit = pd.to_numeric(
        company_df["net_profit"], errors="coerce"
    )

    # Chart 1
    fig, ax = plt.subplots(figsize=(6.5, 2.25))

    ax.plot(
        years,
        revenue,
        marker="o",
        linewidth=1.5,
        label="Revenue",
    )

    ax.plot(
        years,
        profit,
        marker="o",
        linewidth=1.5,
        label="Net Profit",
    )

    ax.set_title(
        f"{company} — Revenue & Net Profit",
        fontsize=9,
    )
    ax.set_xlabel("Year", fontsize=7)
    ax.set_ylabel("Value", fontsize=7)
    ax.tick_params(axis="both", labelsize=6)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=6)

    fig.tight_layout()
    fig.savefig(
        chart1,
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(fig)

    # Chart 2
    roe = pd.to_numeric(
        company_df["roe_calculated"],
        errors="coerce",
    )

    roce = pd.to_numeric(
        company_df["roce_calculated"],
        errors="coerce",
    )

    fig, ax = plt.subplots(figsize=(6.5, 2.25))

    ax.plot(
        years,
        roe,
        marker="o",
        linewidth=1.5,
        label="ROE",
    )

    ax.plot(
        years,
        roce,
        marker="o",
        linewidth=1.5,
        label="ROCE",
    )

    ax.set_title(
        f"{company} — ROE & ROCE Trend",
        fontsize=9,
    )
    ax.set_xlabel("Year", fontsize=7)
    ax.set_ylabel("Percentage", fontsize=7)
    ax.tick_params(axis="both", labelsize=6)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=6)

    fig.tight_layout()
    fig.savefig(
        chart2,
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(fig)

    return chart1, chart2


def make_company_pdf(company, company_df):

    path = TEAR_DIR / f"{company}_tearsheet.pdf"

    company_df = company_df.sort_values("year").copy()

    latest = company_df.iloc[-1]

    sector = (
        str(latest["broad_sector"])
        if "broad_sector" in company_df.columns
        else "N/A"
    )

    years = company_df["year"].astype(str).tolist()

    chart1, chart2 = make_charts(
        company,
        company_df,
    )

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=25,
        bottomMargin=25,
    )

    story = []

    # ==================================================
    # PAGE 1
    # ==================================================

    story.append(
        Paragraph(
            "INVESTMENT TEARSHEET",
            title_style,
        )
    )

    story.append(
        Paragraph(
            company,
            company_style,
        )
    )

    story.append(
        Paragraph(
            f"<b>Sector:</b> {sector} &nbsp;&nbsp; "
            f"<b>Latest Year:</b> {latest['year']} &nbsp;&nbsp; "
            f"<b>Years:</b> {len(years)}",
            normal_style,
        )
    )

    story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            "Top 6 Key Performance Indicators",
            heading_style,
        )
    )

    kpi_data = [
        ["KPI", "Latest", "Trend"]
    ]

    for label, column in KPI_COLUMNS:

        if column not in company_df.columns:
            value = "N/A"
            arrow = "→"
        else:
            values = pd.to_numeric(
                company_df[column],
                errors="coerce",
            ).dropna()

            if len(values) == 0:
                value = "N/A"
                arrow = "→"
            else:
                value = fmt(values.iloc[-1])
                arrow = trend_arrow(
                    company_df,
                    column,
                )

        kpi_data.append(
            [label, value, arrow]
        )

    kpi_table = Table(
        kpi_data,
        colWidths=[250, 120, 65],
    )

    kpi_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1F4E78"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey,
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7.5,
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER",
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.whitesmoke,
                ],
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4,
            ),
        ])
    )

    story.append(kpi_table)

    story.append(Spacer(1, 7))

    story.append(
        Paragraph(
            "Historical Financial Summary",
            heading_style,
        )
    )

    history_data = [
        ["Year"] +
        [x[0] for x in HISTORY_COLUMNS]
    ]

    for _, row in company_df.iterrows():

        history_data.append(
            [row["year"]] +
            [
                fmt(row[column])
                if column in company_df.columns
                else "N/A"
                for _, column in HISTORY_COLUMNS
            ]
        )

    history_table = Table(
        history_data,
        repeatRows=1,
        colWidths=[48] + [68] * 7,
    )

    history_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1F4E78"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.3,
                colors.grey,
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                6,
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "CENTER",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2,
            ),
        ])
    )

    story.append(history_table)

    story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            "<b>Trend:</b> ↑ Improved &nbsp;&nbsp; "
            "↓ Declined &nbsp;&nbsp; "
            "→ Flat within 2%",
            small_style,
        )
    )

    story.append(Spacer(1, 5))

    story.append(
        Paragraph(
            "Financial data is sourced from the project's "
            "financial_ratios dataset.",
            small_style,
        )
    )

    # FORCE PAGE 2
    story.append(PageBreak())

    # ==================================================
    # PAGE 2
    # ==================================================

    story.append(
        Paragraph(
            f"{company} — Financial Trends",
            company_style,
        )
    )

    story.append(
        Paragraph(
            "Revenue and profitability trend",
            heading_style,
        )
    )

    story.append(
        Image(
            str(chart1),
            width=500,
            height=174,
        )
    )

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "Return efficiency trend",
            heading_style,
        )
    )

    story.append(
        Image(
            str(chart2),
            width=500,
            height=174,
        )
    )

    story.append(Spacer(1, 8))

    # Latest-year snapshot
    story.append(
        Paragraph(
            "Latest-Year Snapshot",
            heading_style,
        )
    )

    snapshot = [
        ["Metric", "Value"]
    ]

    snapshot_columns = [
        ("Revenue", "sales"),
        ("Operating Profit", "operating_profit"),
        ("Net Profit", "net_profit"),
        ("EPS", "eps"),
        ("Free Cash Flow", "free_cash_flow"),
        ("Dividend Payout", "dividend_payout"),
    ]

    for label, column in snapshot_columns:

        if column in company_df.columns:
            snapshot.append(
                [
                    label,
                    fmt(latest[column]),
                ]
            )

    snapshot_table = Table(
        snapshot,
        colWidths=[250, 150],
    )

    snapshot_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1F4E78"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.grey,
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7,
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [
                    colors.white,
                    colors.whitesmoke,
                ],
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3,
            ),
        ])
    )

    story.append(snapshot_table)

    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            f"<b>Latest available financial period:</b> "
            f"{latest['year']}",
            small_style,
        )
    )

    doc.build(story)

    return path


# ==========================================================
# GENERATE
# ==========================================================

companies = sorted(df["company_id"].unique())

generated = []
skipped = []

print("\nGenerating 2-page company tearsheets...")

for company in companies:

    company_df = df[
        df["company_id"] == company
    ].copy()

    if len(company_df) < 3:

        skipped.append({
            "company_id": company,
            "years_available": len(company_df),
            "reason": "Fewer than 3 years of data",
        })

        print(
            f"SKIP: {company} — fewer than 3 years"
        )

        continue

    try:

        make_company_pdf(
            company,
            company_df,
        )

        generated.append(company)

        print("PASS:", company)

    except Exception as e:

        skipped.append({
            "company_id": company,
            "years_available": len(company_df),
            "reason": str(e),
        })

        print(
            "FAIL:",
            company,
            e,
        )


pd.DataFrame(skipped).to_csv(
    SKIPPED,
    index=False,
)

print("\n" + "=" * 70)
print("GENERATION COMPLETE")
print("=" * 70)
print("Generated:", len(generated))
print("Skipped:", len(skipped))
print("Output:", TEAR_DIR)
print("Skipped file:", SKIPPED)