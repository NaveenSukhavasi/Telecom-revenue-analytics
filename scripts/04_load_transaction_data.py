from pathlib import Path
import os

import psycopg
from dotenv import load_dotenv


SCRIPT_DIRECTORY = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIRECTORY.parent
RAW_DATA_DIRECTORY = PROJECT_ROOT / "data" / "raw"

load_dotenv(PROJECT_ROOT / ".env")


TABLES = [
    (
        '"usage"',
        "usage.csv",
        [
            "usage_id",
            "subscription_id",
            "usage_month",
            "data_usage_gb",
            "call_minutes",
            "sms_count",
            "roaming_charge",
        ],
    ),
    (
        "invoices",
        "invoices.csv",
        [
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
        ],
    ),
    (
        "payments",
        "payments.csv",
        [
            "payment_id",
            "invoice_id",
            "payment_attempt_at",
            "payment_method",
            "payment_amount",
            "payment_status",
            "failure_reason",
        ],
    ),
    (
        "adjustments",
        "adjustments.csv",
        [
            "adjustment_id",
            "invoice_id",
            "adjustment_date",
            "adjustment_type",
            "adjustment_reason",
            "adjustment_amount",
        ],
    ),
]


def database_configuration():
    names = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]
    missing = [name for name in names if not os.getenv(name)]

    if missing:
        raise ValueError(
            "Missing environment variables: " + ", ".join(missing)
        )

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT")),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }


def validate_source_files():
    missing = []

    for _, filename, _ in TABLES:
        path = RAW_DATA_DIRECTORY / filename
        if not path.exists() or path.stat().st_size == 0:
            missing.append(str(path))

    if missing:
        raise FileNotFoundError(
            "Missing or empty transaction files:\n" + "\n".join(missing)
        )


def copy_csv(cursor, table_name, filename, columns):
    csv_path = RAW_DATA_DIRECTORY / filename
    column_list = ", ".join(columns)
    copy_sql = (
        f"COPY {table_name} ({column_list}) "
        "FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')"
    )

    print(f"Loading {filename} into {table_name}...")

    with cursor.copy(copy_sql) as copy:
        with csv_path.open("r", encoding="utf-8", newline="") as file:
            while chunk := file.read(1024 * 1024):
                copy.write(chunk)


def verify_counts(cursor):
    expected = {
        '"usage"': 510595,
        "invoices": 510595,
        "payments": 545321,
        "adjustments": 28565,
    }

    print("\nDatabase row counts:")

    for table_name, expected_count in expected.items():
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        actual_count = cursor.fetchone()[0]
        display_name = table_name.replace('"', "")

        if actual_count != expected_count:
            raise ValueError(
                f"{display_name}: expected {expected_count:,}, "
                f"found {actual_count:,}"
            )

        print(f"{display_name}: {actual_count:,}")


def main():
    validate_source_files()
    configuration = database_configuration()

    print(f"Reading CSV files from: {RAW_DATA_DIRECTORY}")
    print(f"Loading into database: {configuration['dbname']}")

    with psycopg.connect(**configuration) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE
                    adjustments,
                    payments,
                    invoices,
                    "usage"
                RESTART IDENTITY
                """
            )

            for table_name, filename, columns in TABLES:
                copy_csv(cursor, table_name, filename, columns)

            verify_counts(cursor)

    print("\nTransaction data loaded and validated successfully.")


if __name__ == "__main__":
    main()