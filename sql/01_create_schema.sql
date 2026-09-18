-- Telecom Billing and Revenue Assurance Analytics
-- PostgreSQL database schema

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(12) PRIMARY KEY,
    customer_name VARCHAR(150) NOT NULL,
    customer_segment VARCHAR(30) NOT NULL
        CHECK (customer_segment IN ('Residential', 'Small Business', 'Enterprise')),
    state_code VARCHAR(3) NOT NULL
        CHECK (state_code IN ('ACT', 'NSW', 'NT', 'QLD', 'SA', 'TAS', 'VIC', 'WA')),
    city VARCHAR(80) NOT NULL,
    postcode VARCHAR(4) NOT NULL,
    join_date DATE NOT NULL,
    account_status VARCHAR(20) NOT NULL
        CHECK (account_status IN ('Active', 'Suspended', 'Closed'))
);

CREATE TABLE IF NOT EXISTS plans (
    plan_id VARCHAR(10) PRIMARY KEY,
    product_type VARCHAR(20) NOT NULL
        CHECK (product_type IN ('Mobile', 'Broadband')),
    plan_name VARCHAR(100) NOT NULL UNIQUE,
    monthly_fee NUMERIC(10, 2) NOT NULL
        CHECK (monthly_fee >= 0),
    included_data_gb NUMERIC(10, 2),
    included_minutes INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (included_data_gb IS NULL OR included_data_gb >= 0),
    CHECK (included_minutes IS NULL OR included_minutes >= 0)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id VARCHAR(15) PRIMARY KEY,
    customer_id VARCHAR(12) NOT NULL,
    plan_id VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    subscription_status VARCHAR(20) NOT NULL
        CHECK (subscription_status IN ('Active', 'Suspended', 'Cancelled')),
    billing_cycle_day INTEGER NOT NULL
        CHECK (billing_cycle_day BETWEEN 1 AND 28),

    CONSTRAINT fk_subscription_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT fk_subscription_plan
        FOREIGN KEY (plan_id)
        REFERENCES plans(plan_id),

    CONSTRAINT valid_subscription_dates
        CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id VARCHAR(18) PRIMARY KEY,
    subscription_id VARCHAR(15) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    billing_period_start DATE NOT NULL,
    billing_period_end DATE NOT NULL,
    base_charge NUMERIC(12, 2) NOT NULL
        CHECK (base_charge >= 0),
    usage_charge NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (usage_charge >= 0),
    other_charge NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (other_charge >= 0),
    discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (discount_amount >= 0),
    tax_amount NUMERIC(12, 2) NOT NULL
        CHECK (tax_amount >= 0),
    total_amount NUMERIC(12, 2) NOT NULL
        CHECK (total_amount >= 0),
    invoice_status VARCHAR(20) NOT NULL
        CHECK (
            invoice_status IN (
                'Issued',
                'Paid',
                'Partially Paid',
                'Overdue',
                'Cancelled'
            )
        ),

    CONSTRAINT fk_invoice_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id),

    CONSTRAINT valid_invoice_dates
        CHECK (
            due_date >= invoice_date
            AND billing_period_end >= billing_period_start
        )
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(18) PRIMARY KEY,
    invoice_id VARCHAR(18) NOT NULL,
    payment_attempt_at TIMESTAMP NOT NULL,
    payment_method VARCHAR(30) NOT NULL
        CHECK (
            payment_method IN (
                'Direct Debit',
                'Credit Card',
                'Debit Card',
                'BPAY',
                'Bank Transfer'
            )
        ),
    payment_amount NUMERIC(12, 2) NOT NULL
        CHECK (payment_amount >= 0),
    payment_status VARCHAR(20) NOT NULL
        CHECK (
            payment_status IN (
                'Successful',
                'Failed',
                'Pending',
                'Reversed'
            )
        ),
    failure_reason VARCHAR(100),

    CONSTRAINT fk_payment_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES invoices(invoice_id)
);

CREATE TABLE IF NOT EXISTS adjustments (
    adjustment_id VARCHAR(18) PRIMARY KEY,
    invoice_id VARCHAR(18) NOT NULL,
    adjustment_date DATE NOT NULL,
    adjustment_type VARCHAR(20) NOT NULL
        CHECK (
            adjustment_type IN (
                'Credit',
                'Refund',
                'Debit',
                'Correction'
            )
        ),
    adjustment_reason VARCHAR(150) NOT NULL,
    adjustment_amount NUMERIC(12, 2) NOT NULL
        CHECK (adjustment_amount <> 0),

    CONSTRAINT fk_adjustment_invoice
        FOREIGN KEY (invoice_id)
        REFERENCES invoices(invoice_id)
);

CREATE TABLE IF NOT EXISTS usage (
    usage_id VARCHAR(18) PRIMARY KEY,
    subscription_id VARCHAR(15) NOT NULL,
    usage_month DATE NOT NULL,
    data_usage_gb NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (data_usage_gb >= 0),
    call_minutes INTEGER NOT NULL DEFAULT 0
        CHECK (call_minutes >= 0),
    sms_count INTEGER NOT NULL DEFAULT 0
        CHECK (sms_count >= 0),
    roaming_charge NUMERIC(12, 2) NOT NULL DEFAULT 0
        CHECK (roaming_charge >= 0),

    CONSTRAINT fk_usage_subscription
        FOREIGN KEY (subscription_id)
        REFERENCES subscriptions(subscription_id),

    CONSTRAINT unique_subscription_usage_month
        UNIQUE (subscription_id, usage_month)
);

-- Indexes for common analytical filters and joins

CREATE INDEX IF NOT EXISTS idx_customers_segment
    ON customers(customer_segment);

CREATE INDEX IF NOT EXISTS idx_customers_state
    ON customers(state_code);

CREATE INDEX IF NOT EXISTS idx_subscriptions_customer
    ON subscriptions(customer_id);

CREATE INDEX IF NOT EXISTS idx_subscriptions_plan
    ON subscriptions(plan_id);

CREATE INDEX IF NOT EXISTS idx_invoices_subscription
    ON invoices(subscription_id);

CREATE INDEX IF NOT EXISTS idx_invoices_date
    ON invoices(invoice_date);

CREATE INDEX IF NOT EXISTS idx_invoices_status
    ON invoices(invoice_status);

CREATE INDEX IF NOT EXISTS idx_payments_invoice
    ON payments(invoice_id);

CREATE INDEX IF NOT EXISTS idx_payments_status
    ON payments(payment_status);

CREATE INDEX IF NOT EXISTS idx_adjustments_invoice
    ON adjustments(invoice_id);

CREATE INDEX IF NOT EXISTS idx_usage_subscription
    ON usage(subscription_id);

CREATE INDEX IF NOT EXISTS idx_usage_month
    ON usage(usage_month);

-- Verification query

SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;