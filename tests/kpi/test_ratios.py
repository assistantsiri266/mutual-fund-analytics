import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets
)

print("=" * 50)
print("RUNNING KPI TESTS")
print("=" * 50)

# Net Profit Margin
assert net_profit_margin(100, 1000) == 10
assert net_profit_margin(50, 500) == 10
assert net_profit_margin(10, 0) is None
print("✅ Net Profit Margin Test Passed")

# Operating Profit Margin
assert operating_profit_margin(200, 1000) == 20
assert operating_profit_margin(0, 1000) == 0
assert operating_profit_margin(10, 0) is None
print("✅ Operating Profit Margin Test Passed")

# ROE
assert return_on_equity(100, 200, 300) == 20
assert return_on_equity(100, -100, 0) is None
print("✅ ROE Test Passed")

# ROCE
assert return_on_capital_employed(200, 100, 200, 200) == 40
assert return_on_capital_employed(100, 0, 0, 0) is None
print("✅ ROCE Test Passed")

# ROA
assert return_on_assets(100, 1000) == 10
assert return_on_assets(100, 0) is None
print("✅ ROA Test Passed")

print("=" * 50)
print("🎉 ALL TESTS PASSED")
print("=" * 50)