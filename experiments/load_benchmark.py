import json
from pathlib import Path


BENCHMARK_PATH = Path("benchmarks/basic.jsonl")


def load_benchmark():
    problems = []

    with BENCHMARK_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            problems.append(json.loads(line))

    return problems


def main():
    problems = load_benchmark()

    print(f"Loaded {len(problems)} problems.\n")

    for problem in problems:
        print(problem["id"])
        print("Prompt:", problem["prompt"])
        print("Answer:", problem["answer"])
        print()


if __name__ == "__main__":
    main()
