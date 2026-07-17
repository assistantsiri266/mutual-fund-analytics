import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data" / "raw"

financial_ratios = pd.read_csv(
    OUTPUT_DIR / "profitability_ratios.csv"
)

companies = pd.read_excel(
    DATA_DIR / "companies.xlsx",
    header=1
)

# print(financial_ratios.columns.tolist())
# print(companies.columns.tolist())

financial_ratios["roce_difference"] = abs(
    financial_ratios["roce_calculated"] -
    financial_ratios["roce_percentage"]
)

financial_ratios["roe_difference"] = abs(
    financial_ratios["roe_calculated"] -
    financial_ratios["roe_percentage"]
)

roce_errors = financial_ratios[
    financial_ratios["roce_difference"] > 5
]

print("Total ROCE Errors:", len(roce_errors))

roe_errors = financial_ratios[
    financial_ratios["roe_difference"] > 5
]

print("Total ROE Errors:", len(roe_errors))

OUTPUT_DIR.mkdir(exist_ok=True)

log_file = OUTPUT_DIR / "ratio_edge_cases.log"

with open(log_file, "w") as f:
    f.write("Ratio Edge Case Log\n")
    f.write("=" * 60 + "\n\n")

print("Log file created successfully.")

with open(log_file, "a") as f:

    f.write("ROCE DIFFERENCES\n")
    f.write("-" * 40 + "\n")

    for _, row in roce_errors.iterrows():

        f.write(f"Company ID : {row['company_id']}\n")
        f.write(f"Calculated ROCE : {row['roce_calculated']:.2f}\n")
        f.write(f"Source ROCE : {row['roce_percentage']:.2f}\n")
        f.write(f"Difference : {row['roce_difference']:.2f}\n")
        f.write("\n")

with open(log_file, "a") as f:

    f.write("\nROE DIFFERENCES\n")
    f.write("-" * 40 + "\n")

    for _, row in roe_errors.iterrows():

        f.write(f"Company ID : {row['company_id']}\n")
        f.write(f"Calculated ROE : {row['roe_calculated']:.2f}\n")
        f.write(f"Source ROE : {row['roe_percentage']:.2f}\n")
        f.write(f"Difference : {row['roe_difference']:.2f}\n")
        f.write("\n")

def classify_issue(diff):

    if diff < 10:
        return "Version Difference"

    elif diff < 30:
        return "Formula Difference"

    else:
        return "Data Source Issue"

financial_ratios["roce_issue"] = financial_ratios[
    "roce_difference"
].apply(classify_issue)

financial_ratios["roe_issue"] = financial_ratios[
    "roe_difference"
].apply(classify_issue)

financial_ratios.to_csv(
    OUTPUT_DIR / "edge_case_report.csv",
    index=False
)

print("Edge Case Report Saved Successfully!")