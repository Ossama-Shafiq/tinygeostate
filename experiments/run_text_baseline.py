import argparse
import json
from pathlib import Path

from tinygeo.evaluation import score_prediction
from tinygeo.models.ollama_client import OllamaClient
from tinygeo.parsing import extract_final_answer


BENCHMARK_PATH = Path("benchmarks/basic.jsonl")


SYSTEM_PROMPT = """
You are being evaluated on elementary geometry.

Solve the problem yourself.

You do not have access to calculators, geometry tools,
external programs, or persistent geometric state.

At the end of your response, output exactly:

FINAL: <answer>

Examples:

FINAL: yes
FINAL: right
FINAL: 90

Do not put anything after the FINAL line.
""".strip()


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
        "--output",
        default="results/text_baseline.jsonl",
    )

    args = parser.parse_args()

    benchmark = load_jsonl(BENCHMARK_PATH)

    client = OllamaClient(args.model)

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
            )

            prediction = extract_final_answer(
                response.text
            )

            correct = False

            if prediction is not None:
                correct = score_prediction(
                    prediction,
                    problem["answer"],
                )

            record = {
                "id": problem["id"],
                "model": client.name,
                "condition": "text",
                "prediction": prediction,
                "expected": problem["answer"],
                "correct": correct,
                "raw_response": response.text,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": (
                    response.completion_tokens
                ),
                "tool_calls": 0,
            }

            output_file.write(
                json.dumps(record) + "\n"
            )

            output_file.flush()

            print(
                f"    prediction={prediction!r} "
                f"correct={correct}"
            )


if __name__ == "__main__":
    main()
