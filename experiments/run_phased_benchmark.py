import argparse
import json
from pathlib import Path

from tinygeo.models.ollama_client import (
    OllamaClient,
)
from tinygeo.phased import (
    run_phased_problem,
)


def load_jsonl(
    path: Path,
):
    rows = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:

        for line in f:
            line = line.strip()

            if line:
                rows.append(
                    json.loads(line)
                )

    return rows


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default="qwen3:4b",
    )

    parser.add_argument(
        "--benchmark",
        default=(
            "benchmarks/"
            "compositional_v2_1.jsonl"
        ),
    )

    parser.add_argument(
        "--condition",
        required=True,
        choices=[
            "persistent_state",
            "serialized_state",
        ],
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    parser.add_argument(
        "--step-token-cap",
        type=int,
        default=2048,
    )

    parser.add_argument(
        "--only-id",
        default=None,
    )

    args = parser.parse_args()

    benchmark = load_jsonl(
        Path(args.benchmark)
    )

    if args.only_id is not None:
        benchmark = [
            row
            for row in benchmark
            if row["id"]
            == args.only_id
        ]

        if not benchmark:
            raise ValueError(
                f"Unknown problem ID: "
                f"{args.only_id}"
            )

    client = OllamaClient(
        model=args.model,
        think=True,
        num_predict=args.step_token_cap,
    )

    output_path = Path(
        args.output
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for index, problem in enumerate(
            benchmark,
            start=1,
        ):
            print()
            print(
                f"[{index}/{len(benchmark)}] "
                f"{problem['id']} "
                f"{args.condition}"
            )

            try:
                result = run_phased_problem(
                    client=client,
                    problem=problem,
                    condition=args.condition,
                    step_token_cap=(
                        args.step_token_cap
                    ),
                )

                record = {
                    "id": problem["id"],
                    "base_id": problem.get(
                        "base_id"
                    ),
                    "variant": problem.get(
                        "variant"
                    ),
                    "model": client.name,
                    "condition": (
                        args.condition
                    ),
                    "step_token_cap": (
                        args.step_token_cap
                    ),
                    **result,
                }

            except Exception as exc:
                record = {
                    "id": problem["id"],
                    "base_id": problem.get(
                        "base_id"
                    ),
                    "variant": problem.get(
                        "variant"
                    ),
                    "model": client.name,
                    "condition": (
                        args.condition
                    ),
                    "step_token_cap": (
                        args.step_token_cap
                    ),
                    "prediction": None,
                    "expected": problem[
                        "answer"
                    ],
                    "correct": False,
                    "fatal_error": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                }

            output_file.write(
                json.dumps(record)
                + "\n"
            )

            output_file.flush()

            print(
                "  prediction:",
                record.get(
                    "prediction"
                ),
            )

            print(
                "  expected:",
                record.get(
                    "expected"
                ),
            )

            print(
                "  correct:",
                record.get(
                    "correct"
                ),
            )

            print(
                "  construction:",
                record.get(
                    "construction_correct"
                ),
            )

            print(
                "  predicates:",
                (
                    f"{record.get('predicate_correct', 0)}"
                    f"/"
                    f"{record.get('predicate_total', 0)}"
                ),
            )

            print(
                "  prompt tokens:",
                record.get(
                    "total_prompt_tokens"
                ),
            )

            print(
                "  completion tokens:",
                record.get(
                    "total_completion_tokens"
                ),
            )

            print(
                "  state chars:",
                record.get(
                    "total_state_chars"
                ),
            )

            if "fatal_error" in record:
                print(
                    "  FATAL:",
                    record["fatal_error"],
                )


if __name__ == "__main__":
    main()