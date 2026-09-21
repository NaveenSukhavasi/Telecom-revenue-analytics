from __future__ import annotations

import csv
import math
import random
from calendar import monthrange
from datetime import date, datetime, timedelta
from pathlib import Path


SEED = 42
PERIOD_START = date(2024, 1, 1)
PERIOD_END = date(2025, 12, 1)
AS_OF_DATE = date(2025, 12, 31)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIRECTORY = PROJECT_ROOT / "data" / "raw"

PAYMENT_METHODS = [
    "Direct Debit",
    "Credit Card",
    "Debit Card",
    "BPAY",
    "Bank Transfer",
]

FAILURE_REASONS = [
    "Insufficient funds",
    "Expired card",
    "Bank declined transaction",
    "Invalid account details",
    "Payment gateway timeout",
]


def parse_date(value: str) -> date | None:
    value = value.strip()
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def optional_float(value: str) -> float | None:
    value = value.strip()
    return float(value) if value else None


def optional_int(value: str) -> int | None:
    value = value.strip()
    return int(float(value)) if value else None


def month_starts(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current = (
            date(current.year + 1, 1, 1)
            if current.month == 12
            else date(current.year, current.month + 1, 1)
        )


def month_end(month_start: date) -> date:
    return date(
        month_start.year,
        month_start.month,
        monthrange(month_start.year, month_start.month)[1],
    )


def money(value: float) -> str:
    return f"{max(value, 0):.2f}"


def signed_money(value: float) -> str:
    return f"{value:.2f}"


def weighted_choice(options: list[tuple[str, float]]) -> str:
    values, weights = zip(*options)
    return random.choices(values, weights=weights, k=1)[0]


def read_master_data():
    with (RAW_DATA_DIRECTORY / "customers.csv").open(
        newline="", encoding="utf-8-sig"
    ) as file:
        customer_segments = {
            row["customer_id"]: row["customer_segment"]
            for row in csv.DictReader(file)
        }

    with (RAW_DATA_DIRECTORY / "plans.csv").open(
        newline="", encoding="utf-8-sig"
    ) as file:
        plans = {}
        for row in csv.DictReader(file):
            plans[row["plan_id"]] = {
                "product_type": row["product_type"],
                "monthly_fee": float(row["monthly_fee"]),
                "included_data_gb": optional_float(row["included_data_gb"]),
                "included_minutes": optional_int(row["included_minutes"]),
            }

    with (RAW_DATA_DIRECTORY / "subscriptions.csv").open(
        newline="", encoding="utf-8-sig"
    ) as file:
        subscriptions = []
        for row in csv.DictReader(file):
            subscriptions.append(
                {
                    "subscription_id": row["subscription_id"],
                    "customer_id": row["customer_id"],
                    "plan_id": row["plan_id"],
                    "start_date": parse_date(row["start_date"]),
                    "end_date": parse_date(row["end_date"]),
                    "subscription_status": row["subscription_status"],
                    "billing_cycle_day": int(row["billing_cycle_day"]),
                }
            )

    return customer_segments, plans, subscriptions


def calculate_usage(plan: dict, active_fraction: float, status: str):
    included_data = plan["included_data_gb"] or 0
    included_minutes = plan["included_minutes"] or 0
    product_type = plan["product_type"]

    status_factor = 0.45 if status == "Suspended" else 1.0
    activity_factor = active_fraction * status_factor

    if product_type == "Mobile":
        data_usage = max(
            0,
            random.gauss(included_data * 0.72, max(included_data * 0.32, 1)),
        )
        call_minutes = max(
            0,
            int(random.gauss(included_minutes * 0.68, max(included_minutes * 0.28, 25))),
        )
        sms_count = max(0, int(random.gauss(85, 45)))

        if random.random() < 0.055:
            data_usage *= random.uniform(1.7, 3.1)

        roaming_charge = (
            round(random.uniform(6, 140), 2)
            if random.random() < 0.035
            else 0.0
        )
    else:
        data_usage = max(
            0,
            random.gauss(included_data * 0.70, max(included_data * 0.24, 8)),
        )
        call_minutes = 0
        sms_count = 0

        if random.random() < 0.045:
            data_usage *= random.uniform(1.5, 2.6)

        roaming_charge = 0.0

    return {
        "data_usage_gb": round(data_usage * activity_factor, 2),
        "call_minutes": int(call_minutes * activity_factor),
        "sms_count": int(sms_count * activity_factor),
        "roaming_charge": round(roaming_charge * active_fraction, 2),
    }


def calculate_expected_usage_charge(plan: dict, usage: dict) -> float:
    included_data = plan["included_data_gb"] or 0
    included_minutes = plan["included_minutes"] or 0

    excess_data = max(usage["data_usage_gb"] - included_data, 0)
    excess_minutes = max(usage["call_minutes"] - included_minutes, 0)

    if plan["product_type"] == "Mobile":
        data_charge = math.ceil(excess_data / 5) * 10 if excess_data else 0
        minute_charge = excess_minutes * 0.25
    else:
        data_charge = math.ceil(excess_data / 10) * 5 if excess_data else 0
        minute_charge = 0

    return round(data_charge + minute_charge + usage["roaming_charge"], 2)


def calculate_discount(base_charge: float, customer_segment: str) -> float:
    if customer_segment == "Enterprise" and random.random() < 0.58:
        return round(base_charge * random.choice([0.10, 0.15]), 2)

    if customer_segment == "Small Business" and random.random() < 0.28:
        return round(base_charge * random.choice([0.05, 0.10]), 2)

    if customer_segment == "Residential" and random.random() < 0.10:
        return round(base_charge * 0.05, 2)

    return 0.0


def choose_invoice_status(invoice_date: date, due_date: date) -> str:
    if due_date > AS_OF_DATE:
        return weighted_choice(
            [
                ("Issued", 0.68),
                ("Paid", 0.25),
                ("Partially Paid", 0.05),
                ("Cancelled", 0.02),
            ]
        )

    return weighted_choice(
        [
            ("Paid", 0.82),
            ("Overdue", 0.10),
            ("Partially Paid", 0.05),
            ("Cancelled", 0.03),
        ]
    )


def timestamp_after(start_date: date, minimum_days: int, maximum_days: int) -> str:
    attempt_date = start_date + timedelta(
        days=random.randint(minimum_days, maximum_days)
    )
    attempt_time = datetime.combine(
        attempt_date,
        datetime.min.time(),
    ).replace(
        hour=random.randint(7, 21),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
    )
    return attempt_time.strftime("%Y-%m-%d %H:%M:%S")


def write_payment(
    writer,
    payment_counter: int,
    invoice_id: str,
    attempt_at: str,
    payment_method: str,
    payment_amount: float,
    payment_status: str,
    failure_reason: str = "",
) -> int:
    payment_counter += 1
    writer.writerow(
        {
            "payment_id": f"PAY{payment_counter:015d}",
            "invoice_id": invoice_id,
            "payment_attempt_at": attempt_at,
            "payment_method": payment_method,
            "payment_amount": money(payment_amount),
            "payment_status": payment_status,
            "failure_reason": failure_reason,
        }
    )
    return payment_counter


def generate_payment_rows(
    writer,
    payment_counter: int,
    invoice_id: str,
    invoice_date: date,
    due_date: date,
    total_amount: float,
    invoice_status: str,
) -> int:
    method = random.choice(PAYMENT_METHODS)

    if invoice_status == "Paid":
        if random.random() < 0.12:
            payment_counter = write_payment(
                writer,
                payment_counter,
                invoice_id,
                timestamp_after(invoice_date, 1, 5),
                method,
                total_amount,
                "Failed",
                random.choice(FAILURE_REASONS),
            )

        payment_counter = write_payment(
            writer,
            payment_counter,
            invoice_id,
            timestamp_after(invoice_date, 3, 25),
            method,
            total_amount,
            "Successful",
        )

    elif invoice_status == "Partially Paid":
        partial_amount = round(total_amount * random.uniform(0.25, 0.80), 2)
        payment_counter = write_payment(
            writer,
            payment_counter,
            invoice_id,
            timestamp_after(invoice_date, 3, 30),
            method,
            partial_amount,
            "Successful",
        )

        if random.random() < 0.55:
            payment_counter = write_payment(
                writer,
                payment_counter,
                invoice_id,
                timestamp_after(due_date, 1, 15),
                method,
                total_amount - partial_amount,
                "Failed",
                random.choice(FAILURE_REASONS),
            )

    elif invoice_status == "Overdue":
        if random.random() < 0.08:
            successful_at = timestamp_after(invoice_date, 2, 14)
            payment_counter = write_payment(
                writer,
                payment_counter,
                invoice_id,
                successful_at,
                method,
                total_amount,
                "Successful",
            )
            payment_counter = write_payment(
                writer,
                payment_counter,
                invoice_id,
                timestamp_after(due_date, 1, 20),
                method,
                total_amount,
                "Reversed",
            )
        elif random.random() < 0.72:
            payment_counter = write_payment(
                writer,
                payment_counter,
                invoice_id,
                timestamp_after(invoice_date, 2, 24),
                method,
                total_amount,
                "Failed",
                random.choice(FAILURE_REASONS),
            )

    elif invoice_status == "Issued" and random.random() < 0.42:
        payment_counter = write_payment(
            writer,
            payment_counter,
            invoice_id,
            timestamp_after(invoice_date, 1, 8),
            method,
            total_amount,
            "Pending",
        )

    return payment_counter


def generate_adjustment(
    writer,
    adjustment_counter: int,
    invoice_id: str,
    invoice_date: date,
    total_amount: float,
) -> int:
    if random.random() >= 0.055:
        return adjustment_counter

    adjustment_type = weighted_choice(
        [
            ("Credit", 0.43),
            ("Refund", 0.20),
            ("Debit", 0.17),
            ("Correction", 0.20),
        ]
    )

    reasons = {
        "Credit": [
            "Service outage credit",
            "Customer retention credit",
            "Incorrect usage charge",
        ],
        "Refund": [
            "Duplicate payment refund",
            "Cancelled service refund",
            "Billing dispute resolved",
        ],
        "Debit": [
            "Unbilled equipment charge",
            "Previous undercharge recovered",
            "Late usage charge",
        ],
        "Correction": [
            "Billing system correction",
            "Plan migration correction",
            "Tax calculation correction",
        ],
    }

    amount = round(max(total_amount * random.uniform(0.02, 0.20), 1), 2)

    if adjustment_type in {"Credit", "Refund"}:
        amount *= -1
    elif adjustment_type == "Correction" and random.random() < 0.65:
        amount *= -1

    adjustment_counter += 1
    writer.writerow(
        {
            "adjustment_id": f"ADJ{adjustment_counter:015d}",
            "invoice_id": invoice_id,
            "adjustment_date": (
                invoice_date + timedelta(days=random.randint(2, 45))
            ).isoformat(),
            "adjustment_type": adjustment_type,
            "adjustment_reason": random.choice(reasons[adjustment_type]),
            "adjustment_amount": signed_money(amount),
        }
    )

    return adjustment_counter


def generate_transaction_data(customer_segments, plans, subscriptions):
    usage_path = RAW_DATA_DIRECTORY / "usage.csv"
    invoice_path = RAW_DATA_DIRECTORY / "invoices.csv"
    payment_path = RAW_DATA_DIRECTORY / "payments.csv"
    adjustment_path = RAW_DATA_DIRECTORY / "adjustments.csv"

    usage_fields = [
        "usage_id",
        "subscription_id",
        "usage_month",
        "data_usage_gb",
        "call_minutes",
        "sms_count",
        "roaming_charge",
    ]
    invoice_fields = [
        "invoice_id",
        "subscription_id",
        "invoice_date",
        "due_date",
        "billing_period_start",
        "billing_period_end",
        "base_charge",
        "usage_charge",
        "other_charge",
        "discount_amount",
        "tax_amount",
        "total_amount",
        "invoice_status",
    ]
    payment_fields = [
        "payment_id",
        "invoice_id",
        "payment_attempt_at",
        "payment_method",
        "payment_amount",
        "payment_status",
        "failure_reason",
    ]
    adjustment_fields = [
        "adjustment_id",
        "invoice_id",
        "adjustment_date",
        "adjustment_type",
        "adjustment_reason",
        "adjustment_amount",
    ]

    counters = {
        "usage": 0,
        "invoices": 0,
        "payments": 0,
        "adjustments": 0,
        "base_charge_leakage": 0,
        "usage_charge_leakage": 0,
    }

    with (
        usage_path.open("w", newline="", encoding="utf-8") as usage_file,
        invoice_path.open("w", newline="", encoding="utf-8") as invoice_file,
        payment_path.open("w", newline="", encoding="utf-8") as payment_file,
        adjustment_path.open("w", newline="", encoding="utf-8") as adjustment_file,
    ):
        usage_writer = csv.DictWriter(usage_file, fieldnames=usage_fields)
        invoice_writer = csv.DictWriter(invoice_file, fieldnames=invoice_fields)
        payment_writer = csv.DictWriter(payment_file, fieldnames=payment_fields)
        adjustment_writer = csv.DictWriter(
            adjustment_file,
            fieldnames=adjustment_fields,
        )

        usage_writer.writeheader()
        invoice_writer.writeheader()
        payment_writer.writeheader()
        adjustment_writer.writeheader()

        for subscription in subscriptions:
            plan = plans[subscription["plan_id"]]
            customer_segment = customer_segments[subscription["customer_id"]]

            for usage_month in month_starts(PERIOD_START, PERIOD_END):
                period_end = month_end(usage_month)

                if subscription["start_date"] > period_end:
                    continue

                if (
                    subscription["end_date"] is not None
                    and subscription["end_date"] < usage_month
                ):
                    continue

                active_start = max(subscription["start_date"], usage_month)
                active_end = min(
                    subscription["end_date"] or period_end,
                    period_end,
                )
                active_days = (active_end - active_start).days + 1
                active_fraction = active_days / period_end.day

                usage = calculate_usage(
                    plan,
                    active_fraction,
                    subscription["subscription_status"],
                )

                counters["usage"] += 1
                usage_writer.writerow(
                    {
                        "usage_id": f"USG{counters['usage']:015d}",
                        "subscription_id": subscription["subscription_id"],
                        "usage_month": usage_month.isoformat(),
                        "data_usage_gb": f"{usage['data_usage_gb']:.2f}",
                        "call_minutes": usage["call_minutes"],
                        "sms_count": usage["sms_count"],
                        "roaming_charge": money(usage["roaming_charge"]),
                    }
                )

                expected_base_charge = round(
                    plan["monthly_fee"] * active_fraction,
                    2,
                )
                base_charge = expected_base_charge

                # Intentional revenue-leakage scenario: understated recurring fee.
                if random.random() < 0.015:
                    base_charge = round(
                        expected_base_charge * random.uniform(0.50, 0.90),
                        2,
                    )
                    counters["base_charge_leakage"] += 1

                expected_usage_charge = calculate_expected_usage_charge(plan, usage)
                usage_charge = expected_usage_charge

                # Intentional revenue-leakage scenario: excess usage not fully billed.
                if expected_usage_charge > 0 and random.random() < 0.03:
                    usage_charge = round(
                        expected_usage_charge * random.uniform(0.00, 0.50),
                        2,
                    )
                    counters["usage_charge_leakage"] += 1

                other_charge = (
                    round(random.choice([5, 10, 15, 25, 40]), 2)
                    if random.random() < 0.035
                    else 0.0
                )
                discount_amount = calculate_discount(
                    base_charge,
                    customer_segment,
                )
                taxable_amount = max(
                    base_charge
                    + usage_charge
                    + other_charge
                    - discount_amount,
                    0,
                )
                tax_amount = round(taxable_amount * 0.10, 2)
                total_amount = round(taxable_amount + tax_amount, 2)

                billing_day = min(
                    subscription["billing_cycle_day"],
                    period_end.day,
                )
                invoice_date = date(
                    usage_month.year,
                    usage_month.month,
                    billing_day,
                )
                due_date = invoice_date + timedelta(days=14)
                invoice_status = choose_invoice_status(invoice_date, due_date)

                counters["invoices"] += 1
                invoice_id = f"INV{counters['invoices']:015d}"
                invoice_writer.writerow(
                    {
                        "invoice_id": invoice_id,
                        "subscription_id": subscription["subscription_id"],
                        "invoice_date": invoice_date.isoformat(),
                        "due_date": due_date.isoformat(),
                        "billing_period_start": usage_month.isoformat(),
                        "billing_period_end": period_end.isoformat(),
                        "base_charge": money(base_charge),
                        "usage_charge": money(usage_charge),
                        "other_charge": money(other_charge),
                        "discount_amount": money(discount_amount),
                        "tax_amount": money(tax_amount),
                        "total_amount": money(total_amount),
                        "invoice_status": invoice_status,
                    }
                )

                counters["payments"] = generate_payment_rows(
                    payment_writer,
                    counters["payments"],
                    invoice_id,
                    invoice_date,
                    due_date,
                    total_amount,
                    invoice_status,
                )
                counters["adjustments"] = generate_adjustment(
                    adjustment_writer,
                    counters["adjustments"],
                    invoice_id,
                    invoice_date,
                    total_amount,
                )

    return counters


def main():
    random.seed(SEED)
    RAW_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)

    customer_segments, plans, subscriptions = read_master_data()
    counters = generate_transaction_data(
        customer_segments,
        plans,
        subscriptions,
    )

    print("\nTransaction data generated successfully.")
    print(f"Usage rows: {counters['usage']:,}")
    print(f"Invoice rows: {counters['invoices']:,}")
    print(f"Payment rows: {counters['payments']:,}")
    print(f"Adjustment rows: {counters['adjustments']:,}")
    print(
        "Intentional base-charge leakage cases: "
        f"{counters['base_charge_leakage']:,}"
    )
    print(
        "Intentional usage-charge leakage cases: "
        f"{counters['usage_charge_leakage']:,}"
    )
    print(f"Files saved to: {RAW_DATA_DIRECTORY}")


if __name__ == "__main__":
    main()