"""Generates and loads the fixed-seed fake Policy dataset.

`Faker.seed(42)` makes policy generation fully reproducible: re-running this
module from a fresh clone always produces the same ~40 Policies, so the demo
behaves identically everywhere.

Run as `just seed` (regenerates `data/seed/policies.csv`, then loads it into
Postgres), or `python -m ins_agent.db.seed` directly.
"""

import csv
import random
from pathlib import Path

from faker import Faker

from ins_agent.db.connection import get_connection
from ins_agent.paths import REPO_ROOT

SEED = 42
NUM_POLICIES = 40

SCHEMA_PATH = REPO_ROOT / "db" / "schema.sql"
SEED_CSV_PATH = REPO_ROOT / "data" / "seed" / "policies.csv"

PRODUCT_TYPES = [
    "Auto - Liability",
    "Auto - Collision",
    "Auto - Comprehensive",
    "Auto - Full Coverage",
]
STATUSES = ["active", "expired", "cancelled"]
COVERAGE_LIMITS = [25000, 50000, 100000, 250000, 500000]

FIELDNAMES = [
    "policy_id",
    "holder_name",
    "phone",
    "address",
    "dob",
    "product_type",
    "coverage_start",
    "coverage_end",
    "coverage_limit",
    "status",
]


def generate_policies(n: int = NUM_POLICIES, seed: int = SEED) -> list[dict]:
    Faker.seed(seed)
    fake = Faker()
    rng = random.Random(seed)

    policies = []
    for i in range(1, n + 1):
        coverage_start = fake.date_between(start_date="-3y", end_date="-1y")
        coverage_end = fake.date_between(start_date=coverage_start, end_date="+1y")
        policies.append(
            {
                "policy_id": f"POL-{i:05d}",
                "holder_name": fake.name(),
                "phone": fake.numerify("###-###-####"),
                "address": fake.address().replace("\n", ", "),
                "dob": fake.date_of_birth(minimum_age=18, maximum_age=85).isoformat(),
                "product_type": rng.choice(PRODUCT_TYPES),
                "coverage_start": coverage_start.isoformat(),
                "coverage_end": coverage_end.isoformat(),
                "coverage_limit": rng.choice(COVERAGE_LIMITS),
                "status": rng.choice(STATUSES),
            }
        )
    return policies


def write_csv(policies: list[dict], path: Path = SEED_CSV_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(policies)


def load_into_postgres(csv_path: Path = SEED_CSV_PATH) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_PATH.read_text())
            cur.execute("TRUNCATE TABLE claim, policy")
            with csv_path.open() as f:
                reader = csv.DictReader(f)
                rows = [tuple(row[field] for field in FIELDNAMES) for row in reader]
            cur.executemany(
                f"INSERT INTO policy ({', '.join(FIELDNAMES)}) "
                f"VALUES ({', '.join(['%s'] * len(FIELDNAMES))})",
                rows,
            )
        conn.commit()


def main() -> None:
    policies = generate_policies()
    write_csv(policies)
    load_into_postgres()
    print(f"Seeded {len(policies)} policies into Postgres from {SEED_CSV_PATH}")


if __name__ == "__main__":
    main()
