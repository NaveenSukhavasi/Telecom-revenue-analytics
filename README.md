# Telecom Billing & Revenue Assurance Analytics

An end-to-end data analytics project that examines telecom billing, payments, outstanding balances and potential revenue leakage using Python, PostgreSQL, SQL and Power BI.

## Business Problem

A fictional Australian telecommunications provider needs better visibility into its billing and collection performance. Management wants to understand revenue trends, late payments, failed payment attempts, outstanding balances, customer behaviour and possible revenue leakage.

The project uses entirely synthetic data and does not contain confidential employer, customer or production information.

## Project Objectives

- Analyse billed and collected revenue over time.
- Measure collection rates and outstanding balances.
- Identify overdue invoices and late-payment patterns.
- Investigate payment failures by method and reason.
- Compare revenue across plans, products, segments and states.
- Analyse adjustments, refunds and credits.
- Detect potential revenue-leakage indicators.
- Present findings and recommendations through Power BI.

## Technology Stack

- Python
- Pandas and NumPy
- PostgreSQL
- SQL
- SQLAlchemy and Psycopg
- Jupyter Notebook
- Power BI
- Power Query and DAX
- Git and GitHub

## Planned Data Model

- Customers
- Plans
- Subscriptions
- Invoices
- Payments
- Adjustments
- Usage

## Key KPIs

- Billed revenue
- Collected revenue
- Collection rate
- Outstanding balance
- Overdue invoice rate
- Payment success rate
- Adjustment rate
- Average revenue per customer
- Month-over-month revenue growth
- Potential revenue leakage

## Repository Structure

```text
Telecom Revenue Analytics/
├── data/
├── documentation/
├── images/
├── notebooks/
├── power bi/
├── sql/
├── .gitignore
├── README.md
└── requirements.txt