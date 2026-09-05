import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_jsonl(path: Path):
    rows = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                rows.append(json.loads(line))

    return rows


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--predictions",
        required=True,
    )

    args = parser.parse_args()

    rows = load_jsonl(
        Path(args.predictions)
    )

    grouped = defaultdict(list)

    for row in rows:
        grouped[row["base_id"]].append(row)

    fully_invariant = 0
    fully_correct = 0
    fully_valid = 0

    total_invalid = 0
    total_truncated = 0

    print("Per-base analysis")
    print("=" * 70)

    for base_id, group in sorted(grouped.items()):

        expected_values = {
            row["expected"]
            for row in group
        }

        if len(expected_values) != 1:
            raise ValueError(
                f"{base_id} has inconsistent expected answers."
            )

        expected = next(iter(expected_values))

        predictions = [
            row.get("prediction")
            for row in group
        ]

        all_valid = all(
            prediction is not None
            for prediction in predictions
        )

        valid_predictions = [
            prediction
            for prediction in predictions
            if prediction is not None
        ]

        invariant = (
            all_valid
            and len(set(valid_predictions)) == 1
        )

        all_correct = all(
            row.get("correct", False)
            for row in group
        )

        invalid_count = sum(
            row.get("prediction") is None
            for row in group
        )

        truncated_count = sum(
            row.get("truncated", False)
            for row in group
        )

        total_invalid += invalid_count
        total_truncated += truncated_count

        fully_valid += int(all_valid)
        fully_invariant += int(invariant)
        fully_correct += int(all_correct)

        print()
        print(base_id)
        print(f"  expected:    {expected}")
        print(f"  all valid:   {all_valid}")
        print(f"  invariant:   {invariant}")
        print(f"  all correct: {all_correct}")
        print(f"  invalid:     {invalid_count}")
        print(f"  truncated:   {truncated_count}")

        for row in sorted(
            group,
            key=lambda x: x["variant"],
        ):
            marker = (
                "✓"
                if row.get("correct", False)
                else "✗"
            )

            print(
                f"    {marker} "
                f"{row['variant']:<12} "
                f"prediction={row.get('prediction')!r} "
                f"truncated={row.get('truncated', False)}"
            )

    total_bases = len(grouped)

    print()
    print("=" * 70)

    print(
        "Fully valid bases: "
        f"{fully_valid}/{total_bases} "
        f"({fully_valid / total_bases:.1%})"
    )

    print(
        "Fully invariant bases: "
        f"{fully_invariant}/{total_bases} "
        f"({fully_invariant / total_bases:.1%})"
    )

    print(
        "Perfectly correct bases: "
        f"{fully_correct}/{total_bases} "
        f"({fully_correct / total_bases:.1%})"
    )

    print()
    print(f"Invalid predictions: {total_invalid}")
    print(f"Truncated generations: {total_truncated}")


if __name__ == "__main__":
    main()