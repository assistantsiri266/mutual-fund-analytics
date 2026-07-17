import pandas as pd
import numpy as np

companies = pd.read_excel("data/raw/companies.xlsx", header=1)

profit_loss = pd.read_excel("data/raw/profitandloss.xlsx", header=1)

balance_sheet = pd.read_excel("data/raw/balancesheet.xlsx", header=1)

cash_flow = pd.read_excel("data/raw/cashflow.xlsx", header=1)

analysis = pd.read_excel("data/raw/analysis.xlsx", header=1)

print("Companies:", companies.shape)
print("Profit & Loss:", profit_loss.shape)
print("Balance Sheet:", balance_sheet.shape)
print("Cash Flow:", cash_flow.shape)
print("Analysis:", analysis.shape)

print("\nProfit & Loss Columns")
print(profit_loss.columns.tolist())

print("\nBalance Sheet Columns")
print(balance_sheet.columns.tolist())

print("\nCash Flow Columns")
print(cash_flow.columns.tolist())

print("\nAnalysis Columns")
print(analysis.columns.tolist())

# Net Profit Margin
def net_profit_margin(net_profit, sales):

    if sales == 0:
        return None

    return (net_profit / sales) * 100

print("\nNet Profit Margin Test")
print(net_profit_margin(500, 2000))

# Operating Profit Margin
def operating_profit_margin(operating_profit, sales):

    if sales == 0:
        return None

    return (operating_profit / sales) * 100

print("\nOperating Profit Margin Test")
print(operating_profit_margin(600, 2000))

# Return on Equity
def return_on_equity(net_profit, equity_capital, reserves):

    total_equity = equity_capital + reserves

    if total_equity <= 0:
        return None

    return (net_profit / total_equity) * 100

print("\nROE Test")
print(return_on_equity(400, 1000, 3000))

# Return on Capital Employed
def return_on_capital_employed(operating_profit,
                               equity_capital,
                               reserves,
                               borrowings):

    capital = equity_capital + reserves + borrowings

    if capital <= 0:
        return None

    return (operating_profit / capital) * 100

print("\nROCE Test")
print(return_on_capital_employed(800, 1000, 3000, 1000))

# Return on Assets
def return_on_assets(net_profit, total_assets):

    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100

print("\nROA Test")
print(return_on_assets(500, 5000))

print("\nEdge Case Tests")

print("Net Profit Margin:", net_profit_margin(100, 0))

print("OPM:", operating_profit_margin(100, 0))

print("ROE:", return_on_equity(100, -100, 0))

print("ROCE:", return_on_capital_employed(100, -50, 0, 0))

print("ROA:", return_on_assets(100, 0))

merged_df = pd.merge(
    profit_loss,
    balance_sheet,
    on=["company_id", "year"],
    how="inner"
)

print("Merged Data Shape:", merged_df.shape)
print(merged_df.head())

merged_df["net_profit_margin_pct"] = merged_df.apply(
    lambda row: net_profit_margin(
        row["net_profit"],
        row["sales"]
    ),
    axis=1
)
print(merged_df[["company_id","year","net_profit_margin_pct"]].head())

merged_df["operating_profit_margin_pct"] = merged_df.apply(
    lambda row: operating_profit_margin(
        row["operating_profit"],
        row["sales"]
    ),
    axis=1
)

print(
merged_df[
[
"company_id",
"year",
"operating_profit_margin_pct"
]
].head()
)

merged_df["roe_calculated"] = merged_df.apply(
    lambda row: return_on_equity(
        row["net_profit"],
        row["equity_capital"],
        row["reserves"]
    ),
    axis=1
)
print(
merged_df[
[
"company_id",
"year",
"roe_calculated"
]
].head()
)
merged_df["roce_calculated"] = merged_df.apply(
    lambda row: return_on_capital_employed(
        row["operating_profit"],
        row["equity_capital"],
        row["reserves"],
        row["borrowings"]
    ),
    axis=1
)
print(
merged_df[
[
"company_id",
"year",
"roce_calculated"
]
].head()
)

merged_df["roa_calculated"] = merged_df.apply(
    lambda row: return_on_assets(
        row["net_profit"],
        row["total_assets"]
    ),
    axis=1
)
print(
merged_df[
[
"company_id",
"year",
"roa_calculated"
]
].head()
)
merged_df = pd.merge(
    merged_df,
    companies[["id","roce_percentage","roe_percentage"]],
    left_on="company_id",
    right_on="id",
    how="left"
)
print(
merged_df[
[
"company_id",
"roce_calculated",
"roce_percentage"
]
].head()
)
from pathlib import Path

output_dir = Path("output")
output_dir.mkdir(exist_ok=True)
merged_df.to_csv(
    output_dir / "profitability_ratios.csv",
    index=False
)

print("File saved successfully!")



# Debt-to-Equity Ratio
def debt_to_equity(borrowings, equity_capital, reserves):

    total_equity = equity_capital + reserves

    if borrowings == 0:
        return 0

    if total_equity <= 0:
        return None

    return borrowings / total_equity

merged_df["debt_to_equity"] = merged_df.apply(
    lambda row: debt_to_equity(
        row["borrowings"],
        row["equity_capital"],
        row["reserves"]
    ),
    axis=1
)

print(
merged_df[
[
"company_id",
"year",
"debt_to_equity"
]
].head()
)

merged_df["high_leverage_flag"] = (
    merged_df["debt_to_equity"] > 5
)

print(
merged_df[
[
"company_id",
"debt_to_equity",
"high_leverage_flag"
]
].head()
)

def interest_coverage(
    operating_profit,
    other_income,
    interest
):

    if interest == 0:
        return None

    return (
        operating_profit +
        other_income
    ) / interest

merged_df["interest_coverage"] = merged_df.apply(
    lambda row: interest_coverage(
        row["operating_profit"],
        row["other_income"],
        row["interest"]
    ),
    axis=1
)

print(
merged_df[
[
"company_id",
"interest_coverage"
]
].head()
)

merged_df["icr_label"] = merged_df["interest"].apply(
    lambda x: "Debt Free" if x == 0 else ""
)

print(
merged_df[
[
"company_id",
"interest",
"icr_label"
]
].head()
)

merged_df["icr_warning"] = (
    merged_df["interest_coverage"] < 1.5
)

print(
merged_df[
[
"company_id",
"interest_coverage",
"icr_warning"
]
].head()
)

def net_debt(
    borrowings,
    investments
):

    return borrowings - investments

merged_df["net_debt"] = merged_df.apply(
    lambda row: net_debt(
        row["borrowings"],
        row["investments"]
    ),
    axis=1
)

print(
merged_df[
[
"company_id",
"net_debt"
]
].head()
)

def asset_turnover(
    sales,
    total_assets
):

    if total_assets == 0:
        return None

    return sales / total_assets

merged_df["asset_turnover"] = merged_df.apply(
    lambda row: asset_turnover(
        row["sales"],
        row["total_assets"]
    ),
    axis=1
)

print(
merged_df[
[
"company_id",
"asset_turnover"
]
].head()
)

merged_df.to_csv(
    "output/leverage_efficiency_ratios.csv",
    index=False
)

print("Leverage & Efficiency ratios saved successfully!")