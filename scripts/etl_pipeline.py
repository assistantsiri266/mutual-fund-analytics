import pandas as pd
from pathlib import Path
RAW_FOLDER = Path("data/raw")
PROCESSED_FOLDER = Path("data/processed")
PROCESSED_FOLDER.mkdir(parents=True, exist_ok=True)
csv_files = list(RAW_FOLDER.glob("*.csv"))

print("CSV Files Found:")

for file in csv_files:
    print(file.name)
print("\nReading CSV files...\n")

for file in csv_files:
    df = pd.read_csv(file)

    print(f"{file.name} loaded successfully")
    print(f"Shape: {df.shape}")
    print("-" * 40)
for file in csv_files:

    df = pd.read_csv(file)

    before = len(df)

    df = df.drop_duplicates()

    after = len(df)

    print(f"{file.name}")

    print(f"Duplicates Removed: {before - after}")

    print(f"Final Rows: {after}")

    print("-" * 40)
df = df.ffill()
print("Missing Values Remaining:")
print(df.isnull().sum().sum())
for file in csv_files:

    try:

        df = pd.read_csv(file)

        df = df.drop_duplicates()

        df = df.ffill()

        date_columns = [
            "date",
            "month",
            "transaction_date",
            "portfolio_date",
            "launch_date"
        ]

        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")

        output_file = PROCESSED_FOLDER / file.name

        df.to_csv(output_file, index=False)

        print(f"Processed: {file.name}")

    except Exception as e:

        print(f"Error processing {file.name}")

        print(e)