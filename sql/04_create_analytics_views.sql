-- Telecom Billing and Revenue Assurance Analytics
-- Business-ready analytical views for SQL, Python and Power BI


-- 1. One row per invoice with customer, product, payment and balance measures
CREATE OR REPLACE VIEW vw_invoice_financials AS
WITH payment_summary AS (
    SELECT
        invoice_id,
        SUM(payment_amount) FILTER (
            WHERE payment_status = 'Successful'
        ) AS successful_payment,
        SUM(payment_amount) FILTER (
            WHERE payment_status = 'Reversed'
        ) AS reversed_payment,
        COUNT(*) FILTER (
            WHERE payment_status = 'Failed'
        ) AS failed_payment_attempts,
        MAX(payment_attempt_at) FILTER (
            WHERE payment_status = 'Successful'
        ) AS last_successful_payment_at
    FROM payments
    GROUP BY invoice_id
),
adjustment_summary AS (
    SELECT
        invoice_id,
        SUM(adjustment_amount) AS net_adjustment,
        COUNT(*) AS adjustment_count
    FROM adjustments
    GROUP BY invoice_id
)
SELECT
    i.invoice_id,
    i.subscription_id,
    s.customer_id,
    c.customer_name,
    c.customer_segment,
    c.state_code,
    c.city,
    p.plan_id,
    p.plan_name,
    p.product_type,
    p.monthly_fee,
    i.invoice_date,
    i.due_date,
    i.billing_period_start,
    i.billing_period_end,
    i.base_charge,
    i.usage_charge,
    i.other_charge,
    i.discount_amount,
    i.tax_amount,
    i.total_amount,
    i.invoice_status,
    COALESCE(ps.successful_payment, 0) AS successful_payment,
    COALESCE(ps.reversed_payment, 0) AS reversed_payment,
    COALESCE(ps.successful_payment, 0)
        - COALESCE(ps.reversed_payment, 0) AS net_payment,
    COALESCE(ps.failed_payment_attempts, 0) AS failed_payment_attempts,
    ps.last_successful_payment_at,
    COALESCE(a.net_adjustment, 0) AS net_adjustment,
    COALESCE(a.adjustment_count, 0) AS adjustment_count,
    i.total_amount + COALESCE(a.net_adjustment, 0)
        AS adjusted_invoice_amount,
    CASE
        WHEN i.invoice_status = 'Cancelled' THEN 0
        ELSE GREATEST(
            i.total_amount
            + COALESCE(a.net_adjustment, 0)
            - COALESCE(ps.successful_payment, 0)
            + COALESCE(ps.reversed_payment, 0),
            0
        )
    END AS outstanding_balance,
    CASE
        WHEN ps.last_successful_payment_at IS NULL THEN NULL
        ELSE ps.last_successful_payment_at::date - i.invoice_date
    END AS days_to_payment
FROM invoices i
JOIN subscriptions s
    ON i.subscription_id = s.subscription_id
JOIN customers c
    ON s.customer_id = c.customer_id
JOIN plans p
    ON s.plan_id = p.plan_id
LEFT JOIN payment_summary ps
    ON i.invoice_id = ps.invoice_id
LEFT JOIN adjustment_summary a
    ON i.invoice_id = a.invoice_id;


-- 2. Monthly KPI view by customer segment and product type
CREATE OR REPLACE VIEW vw_monthly_kpis AS
SELECT
    DATE_TRUNC('month', invoice_date)::date AS revenue_month,
    customer_segment,
    product_type,
    COUNT(*) AS invoice_count,
    COUNT(*) FILTER (
        WHERE invoice_status = 'Paid'
    ) AS paid_invoice_count,
    COUNT(*) FILTER (
        WHERE invoice_status = 'Overdue'
    ) AS overdue_invoice_count,
    COUNT(*) FILTER (
        WHERE invoice_status = 'Partially Paid'
    ) AS partially_paid_invoice_count,
    ROUND(SUM(total_amount), 2) AS total_billed,
    ROUND(SUM(net_payment), 2) AS net_collected,
    ROUND(SUM(discount_amount), 2) AS total_discounts,
    ROUND(SUM(net_adjustment), 2) AS net_adjustments,
    ROUND(SUM(outstanding_balance), 2) AS outstanding_balance,
    ROUND(AVG(total_amount), 2) AS average_invoice_value,
    ROUND(
        100.0 * SUM(net_payment)
        / NULLIF(SUM(adjusted_invoice_amount), 0),
        2
    ) AS collection_rate_pct
FROM vw_invoice_financials
GROUP BY
    DATE_TRUNC('month', invoice_date)::date,
    customer_segment,
    product_type;


-- 3. Expected-versus-billed revenue leakage by invoice
CREATE OR REPLACE VIEW vw_revenue_leakage AS
WITH expected_values AS (
    SELECT
        i.invoice_id,
        i.subscription_id,
        s.customer_id,
        c.customer_segment,
        c.state_code,
        p.plan_name,
        p.product_type,
        i.invoice_date,
        i.billing_period_start,
        i.billing_period_end,
        i.base_charge AS billed_base_charge,
        i.usage_charge AS billed_usage_charge,
        ROUND(
            p.monthly_fee
            * (
                LEAST(
                    COALESCE(s.end_date, i.billing_period_end),
                    i.billing_period_end
                )
                - GREATEST(s.start_date, i.billing_period_start)
                + 1
            )::numeric
            / NULLIF(
                i.billing_period_end - i.billing_period_start + 1,
                0
            ),
            2
        ) AS expected_base_charge,
        ROUND(
            CASE
                WHEN p.product_type = 'Mobile' THEN
                    CEIL(
                        GREATEST(
                            u.data_usage_gb
                            - COALESCE(p.included_data_gb, 0),
                            0
                        ) / 5
                    ) * 10
                    + GREATEST(
                        u.call_minutes
                        - COALESCE(p.included_minutes, 0),
                        0
                    ) * 0.25
                    + u.roaming_charge
                ELSE
                    CEIL(
                        GREATEST(
                            u.data_usage_gb
                            - COALESCE(p.included_data_gb, 0),
                            0
                        ) / 10
                    ) * 5
                    + u.roaming_charge
            END,
            2
        ) AS expected_usage_charge
    FROM invoices i
    JOIN subscriptions s
        ON i.subscription_id = s.subscription_id
    JOIN customers c
        ON s.customer_id = c.customer_id
    JOIN plans p
        ON s.plan_id = p.plan_id
    JOIN usage u
        ON i.subscription_id = u.subscription_id
       AND i.billing_period_start = u.usage_month
),
calculated_leakage AS (
    SELECT
        *,
        GREATEST(expected_base_charge - billed_base_charge, 0)
            AS base_charge_leakage,
        GREATEST(expected_usage_charge - billed_usage_charge, 0)
            AS usage_charge_leakage
    FROM expected_values
)
SELECT
    *,
    base_charge_leakage + usage_charge_leakage
        AS total_estimated_leakage,
    CASE
        WHEN base_charge_leakage > 0.01
         AND usage_charge_leakage > 0.01
            THEN 'Base and Usage Underbilling'
        WHEN base_charge_leakage > 0.01
            THEN 'Base Charge Underbilling'
        WHEN usage_charge_leakage > 0.01
            THEN 'Usage Charge Underbilling'
        ELSE 'No Leakage'
    END AS leakage_type
FROM calculated_leakage
WHERE base_charge_leakage > 0.01
   OR usage_charge_leakage > 0.01;


-- 4. Customer-level collections and credit-risk profile
CREATE OR REPLACE VIEW vw_customer_risk AS
SELECT
    customer_id,
    customer_name,
    customer_segment,
    state_code,
    COUNT(*) AS invoice_count,
    COUNT(*) FILTER (
        WHERE invoice_status = 'Overdue'
    ) AS overdue_invoice_count,
    COUNT(*) FILTER (
        WHERE invoice_status = 'Partially Paid'
    ) AS partially_paid_invoice_count,
    SUM(failed_payment_attempts) AS failed_payment_attempts,
    ROUND(SUM(total_amount), 2) AS total_billed,
    ROUND(SUM(net_payment), 2) AS total_collected,
    ROUND(SUM(outstanding_balance), 2) AS outstanding_balance,
    ROUND(AVG(days_to_payment), 2) AS average_days_to_payment,
    CASE
        WHEN SUM(outstanding_balance) >= 1000
          OR COUNT(*) FILTER (
                WHERE invoice_status = 'Overdue'
             ) >= 5
          OR SUM(failed_payment_attempts) >= 5
            THEN 'High'
        WHEN SUM(outstanding_balance) >= 300
          OR COUNT(*) FILTER (
                WHERE invoice_status = 'Overdue'
             ) >= 2
          OR SUM(failed_payment_attempts) >= 2
            THEN 'Medium'
        ELSE 'Low'
    END AS risk_level
FROM vw_invoice_financials
GROUP BY
    customer_id,
    customer_name,
    customer_segment,
    state_code;


-- Verification
SELECT 'vw_invoice_financials' AS view_name, COUNT(*) AS row_count
FROM vw_invoice_financials
UNION ALL
SELECT 'vw_monthly_kpis', COUNT(*) FROM vw_monthly_kpis
UNION ALL
SELECT 'vw_revenue_leakage', COUNT(*) FROM vw_revenue_leakage
UNION ALL
SELECT 'vw_customer_risk', COUNT(*) FROM vw_customer_risk;