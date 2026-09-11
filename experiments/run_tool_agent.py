import argparse
import json
from pathlib import Path

from tinygeo.agent import (
    run_geometry_agent,
)

from tinygeo.evaluation import (
    score_prediction,
)

from tinygeo.models.ollama_client import (
    OllamaClient,
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
            "compositional_v2.jsonl"
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
        "--only-id",
        default=None,
    )

    parser.add_argument(
        "--token-budget",
        type=int,
        default=8192,
    )

    parser.add_argument(
        "--step-token-cap",
        type=int,
        default=4096,
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=40,
    )

    args = parser.parse_args()

    benchmark = load_jsonl(
        Path(args.benchmark)
    )

    if args.only_id is not None:
        benchmark = [
            row
            for row in benchmark
            if row["id"] == args.only_id
        ]

        if not benchmark:
            raise ValueError(
                f"Unknown ID: {args.only_id}"
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
            print(
                f"[{index}/{len(benchmark)}] "
                f"{problem['id']} "
                f"condition={args.condition}"
            )

            result = run_geometry_agent(
                client=client,
                problem_prompt=problem[
                    "prompt"
                ],
                condition=args.condition,
                token_budget=args.token_budget,
                step_token_cap=args.step_token_cap,
                max_steps=args.max_steps,
            )

            prediction = result[
                "prediction"
            ]

            correct = (
                prediction is not None
                and score_prediction(
                    prediction,
                    problem["answer"],
                )
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
                "condition": args.condition,
                "prediction": prediction,
                "expected": problem[
                    "answer"
                ],
                "correct": correct,
                **result,
            }

            output_file.write(
                json.dumps(record)
                + "\n"
            )

            output_file.flush()

            print(
                f"    prediction="
                f"{prediction!r} "
                f"correct={correct}"
            )

            print(
                f"    status="
                f"{result['status']} "
                f"steps={result['steps']} "
                f"tools="
                f"{result['tool_calls']}"
            )

            print(
                f"    completion_tokens="
                f"{result['total_completion_tokens']} "
                f"prompt_tokens="
                f"{result['total_prompt_tokens']}"
            )

            print(
                f"    state_chars_sent="
                f"{result['state_chars_sent']}"
            )


if __name__ == "__main__":
    main()