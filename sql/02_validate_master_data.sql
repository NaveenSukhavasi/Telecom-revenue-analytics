-- Telecom Billing and Revenue Assurance Analytics
-- Master-data validation

-- 1. Master-table row counts
SELECT 'customers' AS table_name, COUNT(*) AS row_count
FROM customers

UNION ALL

SELECT 'plans', COUNT(*)
FROM plans

UNION ALL

SELECT 'subscriptions', COUNT(*)
FROM subscriptions;


-- 2. Customers and subscriptions by segment
SELECT
    c.customer_segment,
    COUNT(DISTINCT c.customer_id) AS customers,
    COUNT(s.subscription_id) AS subscriptions
FROM customers c
LEFT JOIN subscriptions s
    ON c.customer_id = s.customer_id
GROUP BY c.customer_segment
ORDER BY customers DESC;


-- 3. Active subscriptions and potential monthly revenue by product
SELECT
    p.product_type,
    COUNT(s.subscription_id) AS subscriptions,
    ROUND(SUM(p.monthly_fee), 2) AS potential_monthly_revenue
FROM subscriptions s
JOIN plans p
    ON s.plan_id = p.plan_id
WHERE s.subscription_status = 'Active'
GROUP BY p.product_type
ORDER BY potential_monthly_revenue DESC;


-- 4. Foreign-key integrity checks; both results should be zero
SELECT
    COUNT(*) AS subscriptions_without_customer
FROM subscriptions s
LEFT JOIN customers c
    ON s.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

SELECT
    COUNT(*) AS subscriptions_without_plan
FROM subscriptions s
LEFT JOIN plans p
    ON s.plan_id = p.plan_id
WHERE p.plan_id IS NULL;