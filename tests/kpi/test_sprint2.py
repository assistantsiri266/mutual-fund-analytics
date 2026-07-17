import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage,
    asset_turnover
)

from src.analytics.cagr import calculate_cagr

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality,
    capex_intensity,
    fcf_conversion,
    capital_pattern
)

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage,
    net_debt,
    asset_turnover
)

from src.analytics.cagr import calculate_cagr

from src.analytics.cashflow_kpis import (
    free_cash_flow,
    cfo_quality,
    capex_intensity,
    fcf_conversion,
    capital_pattern
)

print("=" * 60)
print("SPRINT 2 KPI TESTS")
print("=" * 60)

# Profitability
assert net_profit_margin(100, 400) == 25
assert operating_profit_margin(200, 400) == 50
assert return_on_equity(100, 500, 500) == 10
assert return_on_capital_employed(200, 500, 500, 250) == 16
assert return_on_assets(100, 1000) == 10

# Leverage
assert debt_to_equity(0, 100, 100) == 0
assert interest_coverage(100, 50, 10) == 15
assert net_debt(100, 20) == 80
assert asset_turnover(500, 250) == 2

# CAGR
value, flag = calculate_cagr(100, 200, 5)
assert flag == "OK"

# Cash Flow
assert free_cash_flow(100, -40) == 60
assert cfo_quality(200, 100) == "High Quality"
assert capex_intensity(-40, 1000)[1] == "Moderate"
assert fcf_conversion(100, 200) == 50

pattern = capital_pattern(100, -20, -10)
assert pattern[3] == "Reinvestor"

print("✅ ALL KPI TESTS PASSED")