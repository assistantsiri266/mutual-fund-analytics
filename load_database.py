import pandas as pd
from sqlalchemy import create_engine

# Create SQLite database
engine = create_engine("sqlite:///bluestock_mf.db")

# Read cleaned CSV files
nav = pd.read_csv("data/processed/nav_history_cleaned.csv")
transactions = pd.read_csv("data/processed/investor_transactions_cleaned.csv")
performance = pd.read_csv("data/processed/scheme_performance_cleaned.csv")

# Load into SQLite
nav.to_sql("fact_nav", engine, if_exists="replace", index=False)

transactions.to_sql("fact_transactions", engine, if_exists="replace", index=False)

performance.to_sql("fact_performance", engine, if_exists="replace", index=False)

# Verify row counts
print("fact_nav rows:", len(nav))
print("fact_transactions rows:", len(transactions))
print("fact_performance rows:", len(performance))

print("All cleaned datasets loaded successfully!")