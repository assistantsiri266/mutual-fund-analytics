-- 1. Top 5 funds by AUM
SELECT *
FROM fact_aum
ORDER BY aum DESC
LIMIT 5;

-- 2. Average NAV per month
SELECT
    date_id,
    AVG(nav) AS average_nav
FROM fact_nav
GROUP BY date_id;

-- 3. Total SIP amount
SELECT
    SUM(amount) AS total_sip
FROM fact_transactions
WHERE transaction_type = 'SIP';

-- 4. Transactions by state
SELECT
    state,
    COUNT(*) AS total_transactions
FROM fact_transactions
GROUP BY state;

-- 5. Funds with expense ratio less than 1%
SELECT *
FROM fact_performance
WHERE expense_ratio < 1;

-- 6. Total redemption amount
SELECT
    SUM(amount) AS total_redemption
FROM fact_transactions
WHERE transaction_type = 'Redemption';

-- 7. Average expense ratio
SELECT
    AVG(expense_ratio) AS average_expense_ratio
FROM fact_performance;

-- 8. Highest NAV
SELECT
    MAX(nav) AS highest_nav
FROM fact_nav;

-- 9. Lowest NAV
SELECT
    MIN(nav) AS lowest_nav
FROM fact_nav;

-- 10. Number of transactions by type
SELECT
    transaction_type,
    COUNT(*) AS total
FROM fact_transactions
GROUP BY transaction_type;