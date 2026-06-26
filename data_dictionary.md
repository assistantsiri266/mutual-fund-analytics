# Data Dictionary

## nav_history.csv

| Column | Data Type | Description |
|---------|----------|-------------|
| amfi_code | Integer | Unique AMFI code of the fund |
| date | Date | NAV date |
| nav | Float | Net Asset Value |

---

## investor_transactions.csv

| Column | Data Type | Description |
|---------|----------|-------------|
| investor_id | Integer | Investor ID |
| transaction_type | Text | SIP, Lumpsum or Redemption |
| amount | Float | Transaction amount |
| date | Date | Transaction date |
| kyc_status | Text | KYC verification status |

---

## scheme_performance.csv

| Column | Data Type | Description |
|---------|----------|-------------|
| amfi_code | Integer | Fund code |
| one_year_return | Float | 1-year return (%) |
| three_year_return | Float | 3-year return (%) |
| five_year_return | Float | 5-year return (%) |
| expense_ratio | Float | Expense ratio (%) |