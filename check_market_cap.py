from pathlib import Path

import pandas as pd


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

MARKET_CAP_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "market_cap.csv"
)


# ============================================================
# CHECK FILE
# ============================================================

print("=" * 80)

print("MARKET CAP FILE PATH:")

print(MARKET_CAP_FILE)

print()

print(
    "FILE EXISTS:",
    MARKET_CAP_FILE.exists()
)

print("=" * 80)


# ============================================================
# READ MARKET CAP FILE
# ============================================================

if not MARKET_CAP_FILE.exists():

    print(
        "\nERROR: market_cap.csv was not found."
    )

    print(
        "\nExpected location:"
    )

    print(
        MARKET_CAP_FILE
    )

else:

    dataframe = pd.read_csv(
        MARKET_CAP_FILE
    )

    print(
        "\nCOLUMNS:"
    )

    print(
        dataframe.columns.tolist()
    )

    print(
        "\nSHAPE:"
    )

    print(
        dataframe.shape
    )

    print(
        "\nFIRST 10 ROWS:"
    )

    print(
        dataframe.head(10)
    )

    print(
        "\nDATA TYPES:"
    )

    print(
        dataframe.dtypes
    )

    print(
        "\nTOTAL COMPANIES:"
    )

    print(
        dataframe["company_id"]
        .nunique()
    )

print()

print("=" * 80)