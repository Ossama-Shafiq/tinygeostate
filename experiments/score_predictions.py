import argparse
import json
from pathlib import Path

from tinygeo.evaluation import score_prediction


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
        "--benchmark",
        default="benchmarks/basic.jsonl",
    )

    parser.add_argument(
        "--predictions",
        required=True,
    )

    args = parser.parse_args()

    benchmark = load_jsonl(Path(args.benchmark))
    predictions = load_jsonl(Path(args.predictions))

    answers = {
        problem["id"]: problem["answer"]
        for problem in benchmark
    }

    correct = 0
    total = 0

    for row in predictions:
        problem_id = row["id"]

        if problem_id not in answers:
            print(f"WARNING: Unknown problem ID: {problem_id}")
            continue

        expected = answers[problem_id]
        prediction = row["prediction"]

        is_correct = score_prediction(
            prediction,
            expected,
        )

        total += 1
        correct += int(is_correct)

        status = "PASS" if is_correct else "FAIL"

        print(
            f"{problem_id}: {status} "
            f"| predicted={prediction!r} "
            f"| expected={expected!r}"
        )

    print()
    print(f"Correct: {correct}/{total}")

    if total:
        print(f"Accuracy: {correct / total:.1%}")


if __name__ == "__main__":
    main()