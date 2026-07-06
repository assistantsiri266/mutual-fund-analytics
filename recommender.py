import pandas as pd
performance = pd.read_csv("data/raw/07_scheme_performance.csv")
print(performance.head())
risk = input("Enter Risk Appetite (Low / Moderate / High): ")
filtered = performance[
    performance['risk_grade'].str.lower() == risk.lower()
]
filtered = filtered.sort_values(
    by='sharpe_ratio',
    ascending=False
)
top3 = filtered.head(3)
print("\nTop 3 Recommended Funds\n")

print(
    top3[
        [
            'scheme_name',
            'fund_house',
            'risk_grade',
            'sharpe_ratio'
        ]
    ]
)
performance = pd.read_csv("data/raw/07_scheme_performance.csv")

risk = input("Enter Risk Appetite (Low / Moderate / High): ")

filtered = performance[
    performance['risk_grade'].str.lower() == risk.lower()
]

filtered = filtered.sort_values(
    by='sharpe_ratio',
    ascending=False
)

top3 = filtered.head(3)

print("\nTop 3 Recommended Funds\n")

print(
    top3[
        [
            'scheme_name',
            'fund_house',
            'risk_grade',
            'sharpe_ratio'
        ]
    ]
)