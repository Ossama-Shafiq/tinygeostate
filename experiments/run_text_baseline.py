import argparse
import json
from pathlib import Path

from tinygeo.evaluation import score_prediction
from tinygeo.models.ollama_client import OllamaClient


SYSTEM_PROMPT = """
You are being evaluated on elementary geometry.

Solve the geometry problem carefully yourself.

You do not have access to calculators, geometry tools,
external programs, or persistent geometric state.

Return only a JSON object containing your final answer.

The answer must be either "yes" or "no".
""".strip()


ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "enum": ["yes", "no"],
        }
    },
    "required": ["answer"],
    "additionalProperties": False,
}


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
        "--model",
        default="qwen3:4b",
    )

    parser.add_argument(
        "--benchmark",
        default="benchmarks/compositional_v1.jsonl",
    )

    parser.add_argument(
        "--output",
        default="results/text_baseline_structured.jsonl",
    )

    parser.add_argument(
        "--num-predict",
        type=int,
        default=4096,
        help="Maximum generated tokens, including model thinking.",
    )

    parser.add_argument(
        "--only-id",
        default=None,
        help="Run only one benchmark problem ID.",
    )

    args = parser.parse_args()

    benchmark = load_jsonl(
        Path(args.benchmark)
    )

    if args.only_id is not None:
        benchmark = [
            problem
            for problem in benchmark
            if problem["id"] == args.only_id
        ]

        if not benchmark:
            raise ValueError(
                f"Problem ID not found: {args.only_id}"
            )

    client = OllamaClient(
        model=args.model,
        think=True,
        num_predict=args.num_predict,
    )

    output_path = Path(args.output)

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
                f"{problem['id']}"
            )

            response = client.generate(
                prompt=problem["prompt"],
                system_prompt=SYSTEM_PROMPT,
                response_format=ANSWER_SCHEMA,
            )

            try:
                parsed = json.loads(response.text)
                prediction = parsed["answer"]

            except (
                json.JSONDecodeError,
                KeyError,
                TypeError,
            ):
                prediction = None

            hit_token_limit = (
                response.completion_tokens is not None
                and response.completion_tokens >= args.num_predict
            )

            truncated = (
                response.done_reason == "length"
                or (
                    hit_token_limit
                    and not response.text.strip()
                )
            )

            correct = (
                prediction is not None
                and score_prediction(
                    prediction,
                    problem["answer"],
                )
            )

            record = {
                "id": problem["id"],
                "base_id": problem.get("base_id"),
                "variant": problem.get("variant"),
                "model": client.name,
                "condition": "text_structured",
                "prediction": prediction,
                "expected": problem["answer"],
                "correct": correct,
                "raw_response": response.text,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "thinking_chars": len(
                    response.thinking or ""
                ),
                "done_reason": response.done_reason,
                "truncated": truncated,
                "num_predict": args.num_predict,
                "tool_calls": 0,
            }

            output_file.write(
                json.dumps(record) + "\n"
            )

            output_file.flush()

            print(
                f"    prediction={prediction!r} "
                f"correct={correct} "
                f"tokens={response.completion_tokens} "
                f"done_reason={response.done_reason!r} "
                f"truncated={truncated}"
            )


if __name__ == "__main__":
    main()