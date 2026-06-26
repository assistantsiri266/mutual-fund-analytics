import pandas as pd

df = pd.read_csv("data/raw/02_nav_history.csv")

# # Convert date
df["date"] = pd.to_datetime(df["date"])

# # Sort
# df = df.sort_values(["amfi_code", "date"])

# # Forward fill NAV
df["nav"] = df.groupby("amfi_code")["nav"].ffill()

# # Remove duplicates
df = df.drop_duplicates()

# # Keep only NAV > 0
df = df[df["nav"] > 0]

# # Save
df.to_csv("data/processed/nav_history_cleaned.csv", index=False)

print(df.head())

# Read investor_transactions.csv
df = pd.read_csv("data/raw/08_investor_transactions.csv")

# Convert date column to datetime
df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")

# Standardize transaction type
df["transaction_type"] = df["transaction_type"].str.strip().str.upper()

mapping = {
    "SIP": "SIP",
    "LUMPSUM": "Lumpsum",
    "REDEMPTION": "Redemption"
}

df["transaction_type"] = df["transaction_type"].replace(mapping)

# Keep only positive amounts
df = df[df["amount_inr"] > 0]

# Check valid KYC status
valid_kyc = ["Verified", "Pending", "Rejected"]

df = df[df["kyc_status"].isin(valid_kyc)]

# Save cleaned file
df.to_csv("data/processed/investor_transactions_cleaned.csv", index=False)

print("Investor transactions cleaned successfully!")

# Read scheme_performance.csv
df = pd.read_csv("data/raw/07_scheme_performance.csv")

# Convert return columns to numeric
return_columns = [
    "return_1yr_pct",
    "return_3yr_pct",
    "return_5yr_pct"
]

for col in return_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Convert expense_ratio to numeric
df["expense_ratio_pct"] = pd.to_numeric(df["expense_ratio_pct"], errors="coerce")

# Flag rows with invalid expense ratio
anomalies = df[
    (df["expense_ratio_pct"] < 0.1) |
    (df["expense_ratio_pct"] > 2.5)
]

print("Expense Ratio Anomalies:")
print(anomalies)

# Save cleaned file
df.to_csv("data/processed/scheme_performance_cleaned.csv", index=False)

print("Scheme performance cleaned successfully!")