import argparse
import json
import statistics
from collections import Counter
from pathlib import Path


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


def safe_mean(
    values,
):
    if not values:
        return 0.0

    return statistics.mean(
        values
    )


def safe_median(
    values,
):
    if not values:
        return 0.0

    return statistics.median(
        values
    )


def percentage(
    numerator,
    denominator,
):
    if denominator == 0:
        return 0.0

    return (
        100.0
        * numerator
        / denominator
    )


def summarize(
    rows,
):
    total = len(rows)

    correct = sum(
        bool(row.get("correct"))
        for row in rows
    )

    valid_final = sum(
        row.get("prediction")
        is not None
        for row in rows
    )

    construction_correct = sum(
        bool(
            row.get(
                "construction_correct"
            )
        )
        for row in rows
    )

    predicate_total = sum(
        row.get(
            "predicate_total",
            0,
        )
        for row in rows
    )

    predicate_valid = sum(
        row.get(
            "predicate_valid",
            0,
        )
        for row in rows
    )

    predicate_correct = sum(
        row.get(
            "predicate_correct",
            0,
        )
        for row in rows
    )

    prompt_tokens = [
        row["total_prompt_tokens"]
        for row in rows
        if row.get(
            "total_prompt_tokens"
        )
        is not None
    ]

    completion_tokens = [
        row[
            "total_completion_tokens"
        ]
        for row in rows
        if row.get(
            "total_completion_tokens"
        )
        is not None
    ]

    thinking_chars = [
        row["total_thinking_chars"]
        for row in rows
        if row.get(
            "total_thinking_chars"
        )
        is not None
    ]

    state_chars = [
        row["total_state_chars"]
        for row in rows
        if row.get(
            "total_state_chars"
        )
        is not None
    ]

    peak_state_chars = [
        row[
            "construction_peak_state_chars"
        ]
        for row in rows
        if row.get(
            "construction_peak_state_chars"
        )
        is not None
    ]

    tool_errors = sum(
        row.get(
            "tool_errors",
            0,
        )
        for row in rows
    )

    construction_statuses = Counter(
        row.get(
            "construction_status",
            (
                "fatal_error"
                if "fatal_error" in row
                else "unknown"
            ),
        )
        for row in rows
    )

    predicate_statuses = Counter()

    for row in rows:
        for predicate in row.get(
            "predicate_details",
            [],
        ):
            predicate_statuses[
                predicate.get(
                    "status",
                    "unknown",
                )
            ] += 1

    return {
        "problems": total,

        "correct": correct,
        "accuracy": percentage(
            correct,
            total,
        ),

        "valid_final": valid_final,
        "valid_final_rate": (
            percentage(
                valid_final,
                total,
            )
        ),

        "construction_correct": (
            construction_correct
        ),
        "construction_rate": (
            percentage(
                construction_correct,
                total,
            )
        ),

        "predicate_total": (
            predicate_total
        ),
        "predicate_valid": (
            predicate_valid
        ),
        "predicate_valid_rate": (
            percentage(
                predicate_valid,
                predicate_total,
            )
        ),
        "predicate_correct": (
            predicate_correct
        ),
        "predicate_accuracy": (
            percentage(
                predicate_correct,
                predicate_total,
            )
        ),

        "mean_prompt_tokens": (
            safe_mean(
                prompt_tokens
            )
        ),
        "median_prompt_tokens": (
            safe_median(
                prompt_tokens
            )
        ),

        "mean_completion_tokens": (
            safe_mean(
                completion_tokens
            )
        ),
        "median_completion_tokens": (
            safe_median(
                completion_tokens
            )
        ),

        "mean_thinking_chars": (
            safe_mean(
                thinking_chars
            )
        ),
        "median_thinking_chars": (
            safe_median(
                thinking_chars
            )
        ),

        "mean_state_chars": (
            safe_mean(
                state_chars
            )
        ),
        "median_state_chars": (
            safe_median(
                state_chars
            )
        ),

        "mean_peak_state_chars": (
            safe_mean(
                peak_state_chars
            )
        ),

        "tool_errors": (
            tool_errors
        ),

        "construction_statuses": (
            construction_statuses
        ),

        "predicate_statuses": (
            predicate_statuses
        ),
    }


def print_summary(
    name,
    summary,
):
    print()
    print(name)
    print("=" * 70)

    print(
        "Problems:",
        summary["problems"],
    )

    print(
        "Final accuracy:",
        (
            f"{summary['correct']}/"
            f"{summary['problems']} "
            f"({summary['accuracy']:.1f}%)"
        ),
    )

    print(
        "Valid final answers:",
        (
            f"{summary['valid_final']}/"
            f"{summary['problems']} "
            f"({summary['valid_final_rate']:.1f}%)"
        ),
    )

    print(
        "Construction success:",
        (
            f"{summary['construction_correct']}/"
            f"{summary['problems']} "
            f"({summary['construction_rate']:.1f}%)"
        ),
    )

    print(
        "Predicate validity:",
        (
            f"{summary['predicate_valid']}/"
            f"{summary['predicate_total']} "
            f"({summary['predicate_valid_rate']:.1f}%)"
        ),
    )

    print(
        "Predicate accuracy:",
        (
            f"{summary['predicate_correct']}/"
            f"{summary['predicate_total']} "
            f"({summary['predicate_accuracy']:.1f}%)"
        ),
    )

    print()
    print(
        "Mean prompt tokens:",
        f"{summary['mean_prompt_tokens']:.1f}",
    )

    print(
        "Median prompt tokens:",
        f"{summary['median_prompt_tokens']:.1f}",
    )

    print(
        "Mean completion tokens:",
        f"{summary['mean_completion_tokens']:.1f}",
    )

    print(
        "Median completion tokens:",
        f"{summary['median_completion_tokens']:.1f}",
    )

    print(
        "Mean thinking chars:",
        f"{summary['mean_thinking_chars']:.1f}",
    )

    print(
        "Median thinking chars:",
        f"{summary['median_thinking_chars']:.1f}",
    )

    print(
        "Mean serialized state chars:",
        f"{summary['mean_state_chars']:.1f}",
    )

    print(
        "Median serialized state chars:",
        f"{summary['median_state_chars']:.1f}",
    )

    print(
        "Mean peak state chars:",
        f"{summary['mean_peak_state_chars']:.1f}",
    )

    print(
        "Tool errors:",
        summary["tool_errors"],
    )

    print(
        "Construction statuses:",
        dict(
            summary[
                "construction_statuses"
            ]
        ),
    )

    print(
        "Predicate statuses:",
        dict(
            summary[
                "predicate_statuses"
            ]
        ),
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--persistent",
        required=True,
    )

    parser.add_argument(
        "--serialized",
        required=True,
    )

    args = parser.parse_args()

    persistent_rows = load_jsonl(
        Path(args.persistent)
    )

    serialized_rows = load_jsonl(
        Path(args.serialized)
    )

    persistent_by_id = {
        row["id"]: row
        for row in persistent_rows
    }

    serialized_by_id = {
        row["id"]: row
        for row in serialized_rows
    }

    persistent_ids = set(
        persistent_by_id
    )

    serialized_ids = set(
        serialized_by_id
    )

    if persistent_ids != serialized_ids:
        missing_persistent = (
            serialized_ids
            - persistent_ids
        )

        missing_serialized = (
            persistent_ids
            - serialized_ids
        )

        raise ValueError(
            "Result IDs do not match.\n"
            f"Missing persistent: "
            f"{sorted(missing_persistent)}\n"
            f"Missing serialized: "
            f"{sorted(missing_serialized)}"
        )

    persistent_summary = summarize(
        persistent_rows
    )

    serialized_summary = summarize(
        serialized_rows
    )

    print_summary(
        "PERSISTENT STATE",
        persistent_summary,
    )

    print_summary(
        "SERIALIZED STATE",
        serialized_summary,
    )

    print()
    print("PAIRED COMPARISON")
    print("=" * 70)

    ids = sorted(
        persistent_ids
    )

    prompt_deltas = []
    completion_deltas = []
    thinking_deltas = []
    state_deltas = []

    persistent_wins = 0
    serialized_wins = 0
    same_correctness = 0

    for problem_id in ids:
        persistent = (
            persistent_by_id[
                problem_id
            ]
        )

        serialized = (
            serialized_by_id[
                problem_id
            ]
        )

        if (
            persistent.get(
                "total_prompt_tokens"
            )
            is not None
            and serialized.get(
                "total_prompt_tokens"
            )
            is not None
        ):
            prompt_deltas.append(
                serialized[
                    "total_prompt_tokens"
                ]
                - persistent[
                    "total_prompt_tokens"
                ]
            )

        if (
            persistent.get(
                "total_completion_tokens"
            )
            is not None
            and serialized.get(
                "total_completion_tokens"
            )
            is not None
        ):
            completion_deltas.append(
                serialized[
                    "total_completion_tokens"
                ]
                - persistent[
                    "total_completion_tokens"
                ]
            )

        if (
            persistent.get(
                "total_thinking_chars"
            )
            is not None
            and serialized.get(
                "total_thinking_chars"
            )
            is not None
        ):
            thinking_deltas.append(
                serialized[
                    "total_thinking_chars"
                ]
                - persistent[
                    "total_thinking_chars"
                ]
            )

        if (
            persistent.get(
                "total_state_chars"
            )
            is not None
            and serialized.get(
                "total_state_chars"
            )
            is not None
        ):
            state_deltas.append(
                serialized[
                    "total_state_chars"
                ]
                - persistent[
                    "total_state_chars"
                ]
            )

        persistent_correct = bool(
            persistent.get(
                "correct"
            )
        )

        serialized_correct = bool(
            serialized.get(
                "correct"
            )
        )

        if (
            persistent_correct
            and not serialized_correct
        ):
            persistent_wins += 1

        elif (
            serialized_correct
            and not persistent_correct
        ):
            serialized_wins += 1

        else:
            same_correctness += 1

    print(
        "Persistent-only correct:",
        persistent_wins,
    )

    print(
        "Serialized-only correct:",
        serialized_wins,
    )

    print(
        "Same correctness outcome:",
        same_correctness,
    )

    print()
    print(
        "Mean serialized - persistent "
        "prompt tokens:",
        f"{safe_mean(prompt_deltas):.1f}",
    )

    print(
        "Median serialized - persistent "
        "prompt tokens:",
        f"{safe_median(prompt_deltas):.1f}",
    )

    print(
        "Mean serialized - persistent "
        "completion tokens:",
        f"{safe_mean(completion_deltas):.1f}",
    )

    print(
        "Median serialized - persistent "
        "completion tokens:",
        f"{safe_median(completion_deltas):.1f}",
    )

    print(
        "Mean serialized - persistent "
        "thinking chars:",
        f"{safe_mean(thinking_deltas):.1f}",
    )

    print(
        "Mean serialized - persistent "
        "state chars:",
        f"{safe_mean(state_deltas):.1f}",
    )

    if (
        persistent_summary[
            "mean_prompt_tokens"
        ]
        > 0
    ):
        prompt_overhead = (
            serialized_summary[
                "mean_prompt_tokens"
            ]
            / persistent_summary[
                "mean_prompt_tokens"
            ]
            - 1.0
        ) * 100.0

        print()
        print(
            "Serialized mean prompt-token "
            "overhead:",
            f"{prompt_overhead:.1f}%",
        )


if __name__ == "__main__":
    main()