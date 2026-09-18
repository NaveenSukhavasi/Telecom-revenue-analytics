from datetime import date, timedelta
from pathlib import Path
import random

import numpy as np
import pandas as pd
from faker import Faker


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

SEED = 42
NUMBER_OF_CUSTOMERS = 25_000
ANALYSIS_END_DATE = date(2025, 12, 31)

random.seed(SEED)
np.random.seed(SEED)
Faker.seed(SEED)

fake = Faker("en_AU")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIRECTORY = PROJECT_ROOT / "data" / "raw"
RAW_DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------------
# Reference data
# -------------------------------------------------------------------

STATE_WEIGHTS = {
    "NSW": 0.32,
    "VIC": 0.26,
    "QLD": 0.20,
    "WA": 0.10,
    "SA": 0.07,
    "TAS": 0.02,
    "ACT": 0.02,
    "NT": 0.01,
}

STATE_LOCATIONS = {
    "NSW": [
        ("Sydney", "2000"),
        ("Parramatta", "2150"),
        ("Newcastle", "2300"),
        ("Wollongong", "2500"),
    ],
    "VIC": [
        ("Melbourne", "3000"),
        ("Dandenong", "3175"),
        ("Geelong", "3220"),
        ("Ballarat", "3350"),
    ],
    "QLD": [
        ("Brisbane", "4000"),
        ("Gold Coast", "4217"),
        ("Townsville", "4810"),
        ("Cairns", "4870"),
    ],
    "WA": [
        ("Perth", "6000"),
        ("Fremantle", "6160"),
        ("Bunbury", "6230"),
    ],
    "SA": [
        ("Adelaide", "5000"),
        ("Mount Gambier", "5290"),
    ],
    "TAS": [
        ("Hobart", "7000"),
        ("Launceston", "7250"),
    ],
    "ACT": [
        ("Canberra", "2600"),
    ],
    "NT": [
        ("Darwin", "0800"),
        ("Alice Springs", "0870"),
    ],
}

PLANS = [
    {
        "plan_id": "MOB001",
        "product_type": "Mobile",
        "plan_name": "Mobile Starter 20GB",
        "monthly_fee": 29.00,
        "included_data_gb": 20,
        "included_minutes": 500,
        "is_active": True,
    },
    {
        "plan_id": "MOB002",
        "product_type": "Mobile",
        "plan_name": "Mobile Value 50GB",
        "monthly_fee": 39.00,
        "included_data_gb": 50,
        "included_minutes": None,
        "is_active": True,
    },
    {
        "plan_id": "MOB003",
        "product_type": "Mobile",
        "plan_name": "Mobile Plus 150GB",
        "monthly_fee": 59.00,
        "included_data_gb": 150,
        "included_minutes": None,
        "is_active": True,
    },
    {
        "plan_id": "MOB004",
        "product_type": "Mobile",
        "plan_name": "Mobile Unlimited",
        "monthly_fee": 79.00,
        "included_data_gb": None,
        "included_minutes": None,
        "is_active": True,
    },
    {
        "plan_id": "BB001",
        "product_type": "Broadband",
        "plan_name": "NBN 25",
        "monthly_fee": 59.95,
        "included_data_gb": None,
        "included_minutes": None,
        "is_active": True,
    },
    {
        "plan_id": "BB002",
        "product_type": "Broadband",
        "plan_name": "NBN 50",
        "monthly_fee": 74.95,
        "included_data_gb": None,
        "included_minutes": None,
        "is_active": True,
    },
    {
        "plan_id": "BB003",
        "product_type": "Broadband",
        "plan_name": "NBN 100",
        "monthly_fee": 89.95,
        "included_data_gb": None,
        "included_minutes": None,
        "is_active": True,
    },
    {
        "plan_id": "BB004",
        "product_type": "Broadband",
        "plan_name": "NBN 250",
        "monthly_fee": 109.95,
        "included_data_gb": None,
        "included_minutes": None,
        "is_active": True,
    },
    {
        "plan_id": "BIZ001",
        "product_type": "Mobile",
        "plan_name": "Business Mobile Pro",
        "monthly_fee": 69.00,
        "included_data_gb": 200,
        "included_minutes": None,
        "is_active": True,
    },
    {
        "plan_id": "BIZ002",
        "product_type": "Broadband",
        "plan_name": "Business Fibre",
        "monthly_fee": 149.00,
        "included_data_gb": None,
        "included_minutes": None,
        "is_active": True,
    },
]

RESIDENTIAL_PLANS = [
    "MOB001",
    "MOB002",
    "MOB003",
    "MOB004",
    "BB001",
    "BB002",
    "BB003",
    "BB004",
]

SMALL_BUSINESS_PLANS = [
    "MOB002",
    "MOB003",
    "MOB004",
    "BB002",
    "BB003",
    "BIZ001",
    "BIZ002",
]

ENTERPRISE_PLANS = [
    "MOB003",
    "MOB004",
    "BB003",
    "BB004",
    "BIZ001",
    "BIZ002",
]


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------

def random_date(start_date: date, end_date: date) -> date:
    """Return a random date between two inclusive dates."""
    number_of_days = (end_date - start_date).days
    return start_date + timedelta(days=random.randint(0, number_of_days))


def choose_state() -> str:
    """Select an Australian state using approximate population weights."""
    return random.choices(
        population=list(STATE_WEIGHTS.keys()),
        weights=list(STATE_WEIGHTS.values()),
        k=1,
    )[0]


def choose_subscription_count(segment: str) -> int:
    """Return a realistic number of subscriptions for each segment."""
    if segment == "Residential":
        return random.choices([1, 2], weights=[0.82, 0.18], k=1)[0]

    if segment == "Small Business":
        return random.choices([1, 2, 3], weights=[0.20, 0.55, 0.25], k=1)[0]

    return random.choices(
        [2, 3, 4, 5],
        weights=[0.10, 0.35, 0.35, 0.20],
        k=1,
    )[0]


def choose_plan_ids(segment: str, subscription_count: int) -> list[str]:
    """Select plans appropriate for the customer's segment."""
    if segment == "Residential":
        available_plans = RESIDENTIAL_PLANS
    elif segment == "Small Business":
        available_plans = SMALL_BUSINESS_PLANS
    else:
        available_plans = ENTERPRISE_PLANS

    return random.sample(available_plans, k=subscription_count)


def choose_subscription_status(customer_status: str) -> str:
    """Select subscription status based on the customer account status."""
    if customer_status == "Closed":
        return "Cancelled"

    if customer_status == "Suspended":
        return random.choices(
            ["Suspended", "Active", "Cancelled"],
            weights=[0.75, 0.15, 0.10],
            k=1,
        )[0]

    return random.choices(
        ["Active", "Suspended", "Cancelled"],
        weights=[0.93, 0.03, 0.04],
        k=1,
    )[0]


# -------------------------------------------------------------------
# Data generation
# -------------------------------------------------------------------

def generate_customers() -> pd.DataFrame:
    customer_records = []

    for customer_number in range(1, NUMBER_OF_CUSTOMERS + 1):
        customer_segment = random.choices(
            ["Residential", "Small Business", "Enterprise"],
            weights=[0.82, 0.15, 0.03],
            k=1,
        )[0]

        state_code = choose_state()
        city, postcode = random.choice(STATE_LOCATIONS[state_code])

        if customer_segment == "Residential":
            customer_name = fake.name()
        else:
            customer_name = fake.company()

        account_status = random.choices(
            ["Active", "Suspended", "Closed"],
            weights=[0.89, 0.04, 0.07],
            k=1,
        )[0]

        customer_records.append(
            {
                "customer_id": f"CUST{customer_number:06d}",
                "customer_name": customer_name,
                "customer_segment": customer_segment,
                "state_code": state_code,
                "city": city,
                "postcode": postcode,
                "join_date": random_date(
                    date(2019, 1, 1),
                    date(2025, 9, 30),
                ),
                "account_status": account_status,
            }
        )

    return pd.DataFrame(customer_records)


def generate_plans() -> pd.DataFrame:
    return pd.DataFrame(PLANS)


def generate_subscriptions(customers: pd.DataFrame) -> pd.DataFrame:
    subscription_records = []
    subscription_number = 1

    for customer in customers.itertuples(index=False):
        subscription_count = choose_subscription_count(
            customer.customer_segment
        )

        selected_plan_ids = choose_plan_ids(
            customer.customer_segment,
            subscription_count,
        )

        for plan_id in selected_plan_ids:
            start_date = random_date(
                customer.join_date,
                date(2025, 11, 30),
            )

            subscription_status = choose_subscription_status(
                customer.account_status
            )

            end_date = None

            if subscription_status == "Cancelled":
                earliest_end_date = start_date + timedelta(days=30)

                if earliest_end_date <= ANALYSIS_END_DATE:
                    end_date = random_date(
                        earliest_end_date,
                        ANALYSIS_END_DATE,
                    )
                else:
                    end_date = ANALYSIS_END_DATE

            subscription_records.append(
                {
                    "subscription_id": f"SUB{subscription_number:07d}",
                    "customer_id": customer.customer_id,
                    "plan_id": plan_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "subscription_status": subscription_status,
                    "billing_cycle_day": random.randint(1, 28),
                }
            )

            subscription_number += 1

    return pd.DataFrame(subscription_records)


# -------------------------------------------------------------------
# Validation and export
# -------------------------------------------------------------------

def validate_data(
    customers: pd.DataFrame,
    plans: pd.DataFrame,
    subscriptions: pd.DataFrame,
) -> None:
    assert customers["customer_id"].is_unique
    assert plans["plan_id"].is_unique
    assert subscriptions["subscription_id"].is_unique

    assert subscriptions["customer_id"].isin(
        customers["customer_id"]
    ).all()

    assert subscriptions["plan_id"].isin(
        plans["plan_id"]
    ).all()

    assert customers["customer_id"].notna().all()
    assert subscriptions["customer_id"].notna().all()

    print("Validation completed successfully.")


def export_data(
    customers: pd.DataFrame,
    plans: pd.DataFrame,
    subscriptions: pd.DataFrame,
) -> None:
    customers.to_csv(
        RAW_DATA_DIRECTORY / "customers.csv",
        index=False,
    )

    plans.to_csv(
        RAW_DATA_DIRECTORY / "plans.csv",
        index=False,
    )

    subscriptions.to_csv(
        RAW_DATA_DIRECTORY / "subscriptions.csv",
        index=False,
    )


def main() -> None:
    print("Generating customers...")
    customers = generate_customers()

    print("Generating plans...")
    plans = generate_plans()

    print("Generating subscriptions...")
    subscriptions = generate_subscriptions(customers)

    validate_data(customers, plans, subscriptions)
    export_data(customers, plans, subscriptions)

    print("\nGeneration completed.")
    print(f"Customers: {len(customers):,}")
    print(f"Plans: {len(plans):,}")
    print(f"Subscriptions: {len(subscriptions):,}")

    print("\nCustomer segments:")
    print(customers["customer_segment"].value_counts())

    print("\nSubscription statuses:")
    print(subscriptions["subscription_status"].value_counts())

    print(f"\nFiles saved to: {RAW_DATA_DIRECTORY}")


if __name__ == "__main__":
    main()