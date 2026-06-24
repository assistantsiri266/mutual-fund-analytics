import pandas as pd
import os

folder = "data/raw"

for file in os.listdir(folder):
    if file.endswith(".csv"):
        path = os.path.join(folder, file)

        print("\n" + "="*50)
        print("FILE:", file)
        print("="*50)

        df = pd.read_csv(path)

        print("\nShape:")
        print(df.shape)

        print("\nData Types:")
        print(df.dtypes)

        print("\nFirst 5 Rows:")
        print(df.head())

        print("\nMissing Values:")
        print(df.isnull().sum())

        print("\nDuplicate Rows:")
        print(df.duplicated().sum())

        fund_master = pd.read_csv("data/raw/01_fund_master.csv")

        print("\nUNIQUE FUND HOUSES")
        print(fund_master["fund_house"].unique())

        print("\nUNIQUE CATEGORIES")
        print(fund_master["category"].unique())

        print("\nUNIQUE SUB-CATEGORIES")
        print(fund_master["sub_category"].unique())

        print("\nUNIQUE RISK GRADES")
        print(fund_master["risk_category"].unique())

        fund_master = pd.read_csv("data/raw/01_fund_master.csv")
        nav_history = pd.read_csv("data/raw/02_nav_history.csv")

        fund_codes = set(fund_master["amfi_code"])
        nav_codes = set(nav_history["amfi_code"])

        missing_codes = fund_codes - nav_codes

        print("Missing Codes:", missing_codes)
        print("Count:", len(missing_codes))