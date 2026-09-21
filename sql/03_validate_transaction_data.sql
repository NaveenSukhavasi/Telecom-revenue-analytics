-- Telecom Billing and Revenue Assurance Analytics
-- Transaction-data validation and control totals

-- 1. Row counts
SELECT 'usage' AS table_name, COUNT(*) AS row_count FROM usage
UNION ALL
SELECT 'invoices', COUNT(*) FROM invoices
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'adjustments', COUNT(*) FROM adjustments;


-- 2. Invoice status and billed value
SELECT
    invoice_status,
    COUNT(*) AS invoice_count,
    ROUND(SUM(total_amount), 2) AS billed_amount
FROM invoices
GROUP BY invoice_status
ORDER BY invoice_count DESC;


-- 3. Payment outcomes
SELECT
    payment_status,
    COUNT(*) AS payment_count,
    ROUND(SUM(payment_amount), 2) AS attempted_amount
FROM payments
GROUP BY payment_status
ORDER BY payment_count DESC;


-- 4. Adjustment profile
SELECT
    adjustment_type,
    COUNT(*) AS adjustment_count,
    ROUND(SUM(adjustment_amount), 2) AS net_adjustment
FROM adjustments
GROUP BY adjustment_type
ORDER BY adjustment_count DESC;


-- 5. Billing, collections and outstanding balance control totals
WITH payment_totals AS (
    SELECT
        invoice_id,
        SUM(
            CASE
                WHEN payment_status = 'Successful' THEN payment_amount
                WHEN payment_status = 'Reversed' THEN -payment_amount
                ELSE 0
            END
        ) AS net_payment
    FROM payments
    GROUP BY invoice_id
),
adjustment_totals AS (
    SELECT
        invoice_id,
        SUM(adjustment_amount) AS net_adjustment
    FROM adjustments
    GROUP BY invoice_id
)
SELECT
    ROUND(SUM(i.total_amount), 2) AS total_billed,
    ROUND(SUM(COALESCE(p.net_payment, 0)), 2) AS net_collected,
    ROUND(SUM(COALESCE(a.net_adjustment, 0)), 2) AS net_adjustments,
    ROUND(
        SUM(
            i.total_amount
            + COALESCE(a.net_adjustment, 0)
            - COALESCE(p.net_payment, 0)
        ),
        2
    ) AS outstanding_balance
FROM invoices i
LEFT JOIN payment_totals p
    ON i.invoice_id = p.invoice_id
LEFT JOIN adjustment_totals a
    ON i.invoice_id = a.invoice_id;


-- 6. Detect understated recurring charges on full-month invoices
SELECT
    COUNT(*) AS suspected_base_charge_leaks,
    ROUND(SUM(p.monthly_fee - i.base_charge), 2) AS estimated_base_leakage
FROM invoices i
JOIN subscriptions s
    ON i.subscription_id = s.subscription_id
JOIN plans p
    ON s.plan_id = p.plan_id
WHERE s.start_date <= i.billing_period_start
  AND (s.end_date IS NULL OR s.end_date >= i.billing_period_end)
  AND i.base_charge < p.monthly_fee * 0.95;


-- 7. Detect unbilled or underbilled excess usage
WITH expected_charges AS (
    SELECT
        i.invoice_id,
        i.usage_charge AS billed_usage_charge,
        CASE
            WHEN p.product_type = 'Mobile' THEN
                CEIL(
                    GREATEST(
                        u.data_usage_gb - COALESCE(p.included_data_gb, 0),
                        0
                    ) / 5
                ) * 10
                + GREATEST(
                    u.call_minutes - COALESCE(p.included_minutes, 0),
                    0
                ) * 0.25
                + u.roaming_charge
            ELSE
                CEIL(
                    GREATEST(
                        u.data_usage_gb - COALESCE(p.included_data_gb, 0),
                        0
                    ) / 10
                ) * 5
                + u.roaming_charge
        END AS expected_usage_charge
    FROM invoices i
    JOIN subscriptions s
        ON i.subscription_id = s.subscription_id
    JOIN plans p
        ON s.plan_id = p.plan_id
    JOIN usage u
        ON i.subscription_id = u.subscription_id
       AND i.billing_period_start = u.usage_month
)
SELECT
    COUNT(*) AS suspected_usage_charge_leaks,
    ROUND(
        SUM(expected_usage_charge - billed_usage_charge),
        2
    ) AS estimated_usage_leakage
FROM expected_charges
WHERE expected_usage_charge > billed_usage_charge + 0.01;