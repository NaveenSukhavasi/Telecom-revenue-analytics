from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIRECTORY = PROJECT_ROOT / "data" / "raw"

load_dotenv(PROJECT_ROOT / ".env")


def create_database_engine():
    required_variables = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_variables = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing_variables:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing_variables)}"
        )

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )

    return create_engine(database_url)


def load_csv_files():
    customers = pd.read_csv(
        RAW_DATA_DIRECTORY / "customers.csv",
        parse_dates=["join_date"],
    )

    plans = pd.read_csv(
        RAW_DATA_DIRECTORY / "plans.csv"
    )

    subscriptions = pd.read_csv(
        RAW_DATA_DIRECTORY / "subscriptions.csv",
        parse_dates=["start_date", "end_date"],
    )

    subscriptions["end_date"] = subscriptions["end_date"].where(
        subscriptions["end_date"].notna(),
        None,
    )

    return customers, plans, subscriptions


def validate_source_data(customers, plans, subscriptions):
    expected_columns = {
        "customers": {
            "customer_id",
            "customer_name",
            "customer_segment",
            "state_code",
            "city",
            "postcode",
            "join_date",
            "account_status",
        },
        "plans": {
            "plan_id",
            "product_type",
            "plan_name",
            "monthly_fee",
            "included_data_gb",
            "included_minutes",
            "is_active",
        },
        "subscriptions": {
            "subscription_id",
            "customer_id",
            "plan_id",
            "start_date",
            "end_date",
            "subscription_status",
            "billing_cycle_day",
        },
    }

    datasets = {
        "customers": customers,
        "plans": plans,
        "subscriptions": subscriptions,
    }

    for name, dataframe in datasets.items():
        if set(dataframe.columns) != expected_columns[name]:
            raise ValueError(f"Unexpected columns in {name}.csv")

        if dataframe.empty:
            raise ValueError(f"{name}.csv contains no records")

    if customers["customer_id"].duplicated().any():
        raise ValueError("Duplicate customer IDs detected")

    if plans["plan_id"].duplicated().any():
        raise ValueError("Duplicate plan IDs detected")

    if subscriptions["subscription_id"].duplicated().any():
        raise ValueError("Duplicate subscription IDs detected")

    if not subscriptions["customer_id"].isin(
        customers["customer_id"]
    ).all():
        raise ValueError("Subscriptions contain unknown customer IDs")

    if not subscriptions["plan_id"].isin(plans["plan_id"]).all():
        raise ValueError("Subscriptions contain unknown plan IDs")


def load_master_data(engine, customers, plans, subscriptions):
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                TRUNCATE TABLE
                    adjustments,
                    payments,
                    invoices,
                    "usage",
                    subscriptions,
                    plans,
                    customers
                RESTART IDENTITY CASCADE
                """
            )
        )

        customers.to_sql(
            "customers",
            connection,
            if_exists="append",
            index=False,
            chunksize=2000,
        )

        plans.to_sql(
            "plans",
            connection,
            if_exists="append",
            index=False,
        )

        subscriptions.to_sql(
            "subscriptions",
            connection,
            if_exists="append",
            index=False,
            chunksize=2000,
        )


def verify_database_counts(engine):
    expected_counts = {
        "customers": 25000,
        "plans": 10,
        "subscriptions": 34455,
    }

    with engine.connect() as connection:
        for table_name, expected_count in expected_counts.items():
            actual_count = connection.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            ).scalar_one()

            if actual_count != expected_count:
                raise ValueError(
                    f"{table_name}: expected {expected_count}, "
                    f"found {actual_count}"
                )

            print(f"{table_name}: {actual_count:,} rows loaded")


def main():
    customers, plans, subscriptions = load_csv_files()
    validate_source_data(customers, plans, subscriptions)

    engine = create_database_engine()

    load_master_data(
        engine,
        customers,
        plans,
        subscriptions,
    )

    verify_database_counts(engine)

    print("\nMaster data loaded and validated successfully.")


if __name__ == "__main__":
    main()