import csv

from ins_agent.db.seed import FIELDNAMES, generate_policies, write_csv


def test_generation_is_deterministic():
    first = generate_policies()
    second = generate_policies()
    assert first == second


def test_generates_expected_count_and_unique_ids():
    policies = generate_policies(n=40)
    assert len(policies) == 40
    assert len({p["policy_id"] for p in policies}) == 40


def test_write_csv_round_trips(tmp_path):
    policies = generate_policies(n=5)
    csv_path = tmp_path / "policies.csv"
    write_csv(policies, csv_path)

    with csv_path.open() as f:
        rows = list(csv.DictReader(f))

    assert [row["policy_id"] for row in rows] == [p["policy_id"] for p in policies]
    assert list(rows[0].keys()) == FIELDNAMES
