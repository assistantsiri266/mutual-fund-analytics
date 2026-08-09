import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "raw"

cashflow = pd.read_excel(
    DATA_DIR / "cashflow.xlsx",
    header=1
)

profit_loss = pd.read_excel(
    DATA_DIR / "profitandloss.xlsx",
    header=1
)

df = pd.merge(
    cashflow,
    profit_loss,
    on=["company_id", "year"],
    how="inner"
)

print(df.shape)
print(df.head())

def free_cash_flow(
    operating_activity,
    investing_activity
):

    return operating_activity + investing_activity

df["free_cash_flow"] = df.apply(
    lambda row: free_cash_flow(
        row["operating_activity"],
        row["investing_activity"]
    ),
    axis=1
)

print(
df[
[
"company_id",
"year",
"free_cash_flow"
]
].head()
)

def cfo_quality(
    operating_activity,
    net_profit
):

    if net_profit == 0:
        return None

    ratio = operating_activity / net_profit

    if ratio > 1:
        return "High Quality"

    elif ratio >= 0.5:
        return "Moderate"

    else:
        return "Accrual Risk"
    
df["cfo_quality"] = df.apply(
    lambda row: cfo_quality(
        row["operating_activity"],
        row["net_profit"]
    ),
    axis=1
)
print(
df[
[
"company_id",
"cfo_quality"
]
].head()
)



def capex_intensity(investing_activity, sales):

    # Handle missing or zero sales
    if pd.isna(sales) or sales == 0:
        return (None, None)

    value = abs(investing_activity) / sales * 100

    if value < 3:
        label = "Asset Light"

    elif value <= 8:
        label = "Moderate"

    else:
        label = "Capital Intensive"

    return (value, label)

df["capex_pct"] = df.apply(
    lambda row: capex_intensity(
        row["investing_activity"],
        row["sales"]
    )[0],
    axis=1
)

df["capex_label"] = df.apply(
    lambda row: capex_intensity(
        row["investing_activity"],
        row["sales"]
    )[1],
    axis=1
)

def fcf_conversion(
    fcf,
    operating_profit
):

    if operating_profit == 0:
        return None

    return fcf / operating_profit * 100

df["fcf_conversion"] = df.apply(
    lambda row: fcf_conversion(
        row["free_cash_flow"],
        row["operating_profit"]
    ),
    axis=1
)

def capital_pattern(cfo, cfi, cff):

    cfo_sign = "+" if cfo >= 0 else "-"
    cfi_sign = "+" if cfi >= 0 else "-"
    cff_sign = "+" if cff >= 0 else "-"

    pattern = (cfo_sign, cfi_sign, cff_sign)

    mapping = {
        ("+","-","-"): "Reinvestor",
        ("+","+","-"): "Liquidating Assets",
        ("-","+","+"): "Distress Signal",
        ("-","-","+"): "Growth Funded by Debt",
        ("+","+","+"): "Cash Accumulator",
        ("-","-","-"): "Pre-Revenue",
        ("+","-","+"): "Mixed"
    }

    return (
        cfo_sign,
        cfi_sign,
        cff_sign,
        mapping.get(pattern, "Other")
    )

patterns = df.apply(
    lambda row: capital_pattern(
        row["operating_activity"],
        row["investing_activity"],
        row["financing_activity"]
    ),
    axis=1
)

df["cfo_sign"] = patterns.apply(lambda x: x[0])
df["cfi_sign"] = patterns.apply(lambda x: x[1])
df["cff_sign"] = patterns.apply(lambda x: x[2])
df["pattern_label"] = patterns.apply(lambda x: x[3])

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

df[
[
"company_id",
"year",
"cfo_sign",
"cfi_sign",
"cff_sign",
"pattern_label"
]
].to_csv(
    OUTPUT_DIR / "capital_allocation.csv",
    index=False
)

print("Capital allocation saved successfully!")

df.to_csv(
    OUTPUT_DIR / "cashflow_kpis.csv",
    index=False
)

print("Cash Flow KPI report saved!")