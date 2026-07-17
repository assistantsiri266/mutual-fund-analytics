import pandas as pd
from pathlib import Path

# ---------------------------------------------------
# Project Paths
# ---------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "data" / "raw"

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------
# Read Data
# ---------------------------------------------------

profit_loss = pd.read_excel(
    DATA_DIR / "profitandloss.xlsx",
    header=1
)

print("Profit & Loss Shape:", profit_loss.shape)

profit_loss = profit_loss.sort_values(
    by=["company_id", "year"]
)

# ---------------------------------------------------
# CAGR Function
# ---------------------------------------------------

def calculate_cagr(start_value, end_value, years):

    if years <= 0:
        return None, "INVALID_PERIOD"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    cagr = ((end_value / start_value) ** (1 / years) - 1) * 100

    return round(cagr, 2), "OK"

# ---------------------------------------------------
# Calculate CAGR
# ---------------------------------------------------

results = []

for company in profit_loss["company_id"].unique():

    company_data = profit_loss[
        profit_loss["company_id"] == company
    ].sort_values("year").reset_index(drop=True)

    if len(company_data) >= 6:

        # Revenue CAGR
        revenue_cagr, revenue_flag = calculate_cagr(
            company_data.iloc[-6]["sales"],
            company_data.iloc[-1]["sales"],
            5
        )

        # PAT CAGR
        pat_cagr, pat_flag = calculate_cagr(
            company_data.iloc[-6]["net_profit"],
            company_data.iloc[-1]["net_profit"],
            5
        )

        # EPS CAGR
        eps_cagr, eps_flag = calculate_cagr(
            company_data.iloc[-6]["eps"],
            company_data.iloc[-1]["eps"],
            5
        )

    else:

        revenue_cagr = None
        revenue_flag = "INSUFFICIENT"

        pat_cagr = None
        pat_flag = "INSUFFICIENT"

        eps_cagr = None
        eps_flag = "INSUFFICIENT"

    results.append({

        "company_id": company,

        "revenue_cagr_5yr": revenue_cagr,
        "revenue_flag": revenue_flag,

        "pat_cagr_5yr": pat_cagr,
        "pat_flag": pat_flag,

        "eps_cagr_5yr": eps_cagr,
        "eps_flag": eps_flag

    })

# ---------------------------------------------------
# Create DataFrame
# ---------------------------------------------------

cagr_df = pd.DataFrame(results)

print("\nFirst 5 Records")
print(cagr_df.head())

print("\nTotal Companies Processed:", len(cagr_df))

# ---------------------------------------------------
# Save CSV
# ---------------------------------------------------

cagr_df.to_csv(
    OUTPUT_DIR / "cagr_results.csv",
    index=False
)

print("\n✅ CAGR results saved successfully!")
print("Location:", OUTPUT_DIR / "cagr_results.csv")