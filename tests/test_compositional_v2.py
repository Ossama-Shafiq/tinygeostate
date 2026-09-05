from collections import defaultdict

from benchmarks.generate_compositional_v2 import (
    generate_records,
)


def test_v2_is_balanced():
    records = generate_records()

    assert len(records) == 56

    yes_count = sum(
        row["answer"] == "yes"
        for row in records
    )

    no_count = sum(
        row["answer"] == "no"
        for row in records
    )

    assert yes_count == 28
    assert no_count == 28


def test_v2_variants_preserve_truth():
    records = generate_records()

    grouped = defaultdict(list)

    for row in records:
        grouped[
            row["base_id"]
        ].append(
            row
        )

    assert len(grouped) == 8

    for group in grouped.values():

        answers = {
            row["answer"]
            for row in group
        }

        assert len(group) == 7

        # Every transformed version of one
        # geometry must retain the same answer.
        assert len(answers) == 1
