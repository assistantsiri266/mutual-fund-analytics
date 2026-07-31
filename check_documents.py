import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

FILE_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "documents.xlsx"
)


# ============================================================
# FILE CHECK
# ============================================================

print("=" * 80)

print("DOCUMENTS FILE PATH:")

print(FILE_PATH)

print("\nFILE EXISTS:")

print(FILE_PATH.exists())

print("=" * 80)


# ============================================================
# READ ALL SHEETS
# ============================================================

if FILE_PATH.exists():

    excel_file = pd.ExcelFile(
        FILE_PATH
    )

    print("\nSHEET NAMES:")

    print(
        excel_file.sheet_names
    )

    print("\n" + "=" * 80)

    for sheet_name in excel_file.sheet_names:

        print(
            f"\nSHEET NAME: {sheet_name}"
        )

        dataframe = pd.read_excel(
            FILE_PATH,
            sheet_name=sheet_name,
            header=None
        )

        print(
            "\nSHAPE:"
        )

        print(
            dataframe.shape
        )

        print(
            "\nFIRST 15 ROWS:"
        )

        print(
            dataframe.head(15)
        )

        print(
            "\n" + "-" * 80
        )

print("=" * 80)