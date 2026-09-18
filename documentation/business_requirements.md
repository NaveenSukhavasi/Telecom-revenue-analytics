# Business Requirements

## 1. Business Scenario

This project represents a fictional Australian telecommunications provider offering mobile and broadband services to residential, small-business and enterprise customers.

Management currently receives separate billing, payment and usage reports. This makes it difficult to obtain a reliable view of revenue performance, outstanding debt and potential revenue leakage.

The analysis will combine these areas into one analytics solution covering January 2024 to December 2025.

## 2. Project Objective

The objective is to create an analytics solution that helps management:

- Monitor revenue and collection performance.
- Understand unpaid and overdue invoices.
- Investigate payment failures.
- Compare commercial performance across customer groups and plans.
- Monitor adjustments, credits and refunds.
- Identify possible billing and revenue-assurance issues.
- Make evidence-based operational recommendations.

## 3. Dataset Scope

The synthetic dataset will contain approximately:

- 25,000 customers
- 25,000–35,000 subscriptions
- 24 months of billing activity
- Approximately 500,000–700,000 invoices
- Successful and failed payment attempts
- Monthly service-usage records
- Billing adjustments, credits and refunds

The volume is large enough to demonstrate practical SQL, Python and Power BI skills while remaining manageable on a personal computer.

## 4. Source Tables

### Customers

Stores customer profile information including customer segment, location, join date and account status.

### Plans

Stores product type, plan name, monthly fee, allowance and plan status.

### Subscriptions

Links customers to plans and records subscription start date, end date and status.

### Invoices

Stores base charges, usage charges, discounts, tax, total billed amount, due date and invoice status.

### Payments

Stores payment attempts, amounts, methods, dates, payment status and failure reasons.

### Adjustments

Stores credits, refunds, billing corrections and other account adjustments.

### Usage

Stores monthly data, call and messaging usage for each subscription.

## 5. Key Performance Indicators

### Billed Revenue

Total invoice value generated during the selected period.

### Collected Revenue

Total value of successful customer payments.

### Collection Rate

Collected Revenue / Billed Revenue × 100

### Outstanding Balance

Total invoice amount minus successful payments and applicable credits.

### Overdue Invoice Rate

Number of overdue invoices / Number of issued invoices × 100

### Payment Success Rate

Successful payment attempts / Total payment attempts × 100

### Adjustment Rate

Absolute adjustment value / Billed Revenue × 100

### Average Revenue per Customer

Billed Revenue / Number of active customers

### Month-over-Month Revenue Growth

(Current Month Revenue − Previous Month Revenue) / Previous Month Revenue × 100

## 6. Business Questions

1. How are billed and collected revenue changing each month?
2. What percentage of billed revenue is successfully collected?
3. Which customer segments and states have the highest outstanding balances?
4. Which plans and product types generate the most revenue?
5. What proportion of invoices are overdue?
6. Which payment methods have the highest failure rates?
7. What are the most common payment-failure reasons?
8. Which customers repeatedly pay late or have failed payments?
9. Where are adjustments, refunds or credits unusually high?
10. Are active subscriptions missing expected monthly invoices?
11. Are any high-usage subscriptions billed unusually low amounts?
12. What actions could improve collections and reduce revenue leakage?

## 7. Revenue-Leakage Indicators

The analysis will flag situations such as:

- Active subscriptions without an expected monthly invoice.
- High usage combined with unusually low billed charges.
- Repeated or unusually large billing adjustments.
- Successful service usage after a subscription end date.
- Duplicate credits or refunds.
- Payments not correctly matched to invoices.

These flags indicate records requiring investigation. They do not automatically prove that revenue leakage occurred.

## 8. Data Privacy

All records will be synthetically generated. No customer information, employer data or confidential production data will be used.