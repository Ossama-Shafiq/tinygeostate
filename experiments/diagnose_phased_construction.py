import argparse
import json
from pathlib import Path
from typing import Any

from tinygeo.agent import GEOMETRY_TOOLS
from tinygeo.models.ollama_client import OllamaClient
from tinygeo.session import (
    EMPTY_STATE,
    PersistentGeometrySession,
    StatelessGeometrySession,
)


CONSTRUCTION_TOOL_NAMES = {
    "create_point",
    "create_line",
    "create_midpoint",
    "create_intersection",
}


def select_tools(
    names: set[str],
) -> list[dict[str, Any]]:
    selected = []

    for tool in GEOMETRY_TOOLS:
        name = tool[
            "function"
        ][
            "name"
        ]

        if name in names:
            selected.append(tool)

    return selected


CONSTRUCTION_TOOLS = select_tools(
    CONSTRUCTION_TOOL_NAMES
)


def format_number(
    value,
):
    value = float(value)

    if value.is_integer():
        return str(int(value))

    return (
        f"{value:.6f}"
        .rstrip("0")
        .rstrip(".")
    )


def describe_initial_point(
    name: str,
    coordinates,
) -> str:

    x, y = coordinates

    return (
        f"Create point {name} at coordinates "
        f"({format_number(x)}, {format_number(y)})."
    )


def describe_operation(
    operation: dict[str, Any],
) -> str:

    op = operation["op"]

    if op == "midpoint":
        return (
            f"Create point {operation['name']} "
            f"as the midpoint of points "
            f"{operation['a']} and {operation['b']}."
        )

    if op == "line":
        return (
            f"Create line {operation['name']} "
            f"through points "
            f"{operation['p1']} and "
            f"{operation['p2']}."
        )

    if op == "intersection":
        return (
            f"Create point {operation['name']} "
            f"as the intersection of lines "
            f"{operation['line1']} and "
            f"{operation['line2']}."
        )

    raise ValueError(
        f"Unsupported operation: {op}"
    )


def load_problem(
    benchmark_path: Path,
    problem_id: str,
):
    with benchmark_path.open(
        "r",
        encoding="utf-8",
    ) as f:

        for line in f:
            problem = json.loads(line)

            if (
                problem["id"]
                == problem_id
            ):
                return problem

    raise ValueError(
        f"Problem not found: {problem_id}"
    )


def extract_one_tool_call(
    response,
):
    if not response.tool_calls:
        return None, None

    if len(response.tool_calls) != 1:
        raise ValueError(
            "Expected exactly one tool call, "
            f"got {len(response.tool_calls)}."
        )

    function = response.tool_calls[0].get(
        "function",
        {},
    )

    name = function.get(
        "name"
    )

    arguments = function.get(
        "arguments",
        {},
    )

    if isinstance(
        arguments,
        str,
    ):
        arguments = json.loads(
            arguments
        )

    return (
        name,
        arguments,
    )


def make_messages(
    instruction: str,
    condition: str,
    serialized_state,
):
    system_prompt = """
You execute exactly one explicit geometric construction instruction.

Use exactly one supplied geometry tool.

Do not solve the overall geometry problem.
Do not reason about future constructions.
Do not answer yes or no.
Do not perform extra operations.

Translate only the current instruction into the appropriate tool call.
""".strip()

    if condition == "persistent_state":

        user_content = (
            "CURRENT INSTRUCTION:\n"
            f"{instruction}"
        )

    elif condition == "serialized_state":

        state_text = json.dumps(
            serialized_state,
            separators=(",", ":"),
        )

        user_content = (
            "CURRENT GEOMETRIC STATE:\n"
            f"{state_text}\n\n"
            "CURRENT INSTRUCTION:\n"
            f"{instruction}"
        )

    else:
        raise ValueError(
            f"Unknown condition: {condition}"
        )

    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]


def run():
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
        "--only-id",
        default="m01a_original",
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
        "--step-token-cap",
        type=int,
        default=2048,
    )

    args = parser.parse_args()

    problem = load_problem(
        Path(args.benchmark),
        args.only_id,
    )

    client = OllamaClient(
        model=args.model,
        think=True,
        num_predict=args.step_token_cap,
    )

    if (
        args.condition
        == "persistent_state"
    ):
        session = (
            PersistentGeometrySession()
        )

        serialized_state = None

    else:
        session = (
            StatelessGeometrySession()
        )

        serialized_state = (
            EMPTY_STATE
        )

    instructions = []

    # Initial given points.
    for (
        name,
        coordinates,
    ) in problem[
        "initial_points"
    ].items():

        instructions.append(
            describe_initial_point(
                name,
                coordinates,
            )
        )

    # Explicit derived constructions.
    for operation in problem[
        "operations"
    ]:
        instructions.append(
            describe_operation(
                operation
            )
        )

    print(
        f"Problem: {args.only_id}"
    )

    print(
        f"Condition: {args.condition}"
    )

    print(
        f"Construction steps: "
        f"{len(instructions)}"
    )

    print("=" * 70)

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_thinking_chars = 0

    state_chars_sent = 0

    for step_number, instruction in enumerate(
        instructions,
        start=1,
    ):
        print()
        print(
            f"STEP {step_number}"
        )

        print(
            f"Instruction: {instruction}"
        )

        if (
            args.condition
            == "serialized_state"
        ):
            state_text = json.dumps(
                serialized_state,
                separators=(",", ":"),
            )

            state_chars_sent += len(
                state_text
            )

            print(
                "State chars entering model:",
                len(state_text),
            )

        messages = make_messages(
            instruction=instruction,
            condition=args.condition,
            serialized_state=serialized_state,
        )

        response = client.chat(
            messages=messages,
            tools=CONSTRUCTION_TOOLS,
            num_predict=args.step_token_cap,
        )

        total_prompt_tokens += (
            response.prompt_tokens or 0
        )

        total_completion_tokens += (
            response.completion_tokens or 0
        )

        total_thinking_chars += len(
            response.thinking or ""
        )

        print(
            "done_reason:",
            response.done_reason,
        )

        print(
            "completion_tokens:",
            response.completion_tokens,
        )

        print(
            "thinking_chars:",
            len(
                response.thinking or ""
            ),
        )

        print(
            "tool_calls:",
            response.tool_calls,
        )

        if (
            response.done_reason
            == "length"
            and not response.tool_calls
        ):
            print()
            print(
                "FAILED: model exhausted "
                "the step token cap before "
                "making a tool call."
            )

            return

        try:
            (
                tool_name,
                arguments,
            ) = extract_one_tool_call(
                response
            )

        except ValueError as exc:
            print()
            print(
                f"FAILED: {exc}"
            )
            return

        if tool_name is None:
            print()
            print(
                "FAILED: no tool call."
            )
            return

        if (
            tool_name
            not in CONSTRUCTION_TOOL_NAMES
        ):
            print()
            print(
                "FAILED: unexpected tool:",
                tool_name,
            )
            return

        action = {
            "op": tool_name,
            **arguments,
        }

        print(
            "Action:",
            action,
        )

        if (
            args.condition
            == "persistent_state"
        ):
            result = session.execute(
                action
            )

        else:
            result = session.execute(
                action,
                state=serialized_state,
            )

            serialized_state = (
                result["state"]
            )

        print(
            "Tool result:",
            result,
        )

        if not result.get(
            "ok",
            False,
        ):
            print()
            print(
                "FAILED: geometry tool "
                "returned an error."
            )
            return

    print()
    print("=" * 70)
    print("CONSTRUCTION COMPLETE")
    print("=" * 70)

    if (
        args.condition
        == "persistent_state"
    ):
        final_state = (
            session.snapshot()
        )

    else:
        final_state = (
            serialized_state
        )

    print()
    print(
        "Final state:"
    )

    print(
        json.dumps(
            final_state,
            indent=2,
        )
    )

    print()
    print(
        "Total prompt tokens:",
        total_prompt_tokens,
    )

    print(
        "Total completion tokens:",
        total_completion_tokens,
    )

    print(
        "Total thinking chars:",
        total_thinking_chars,
    )

    print(
        "Total serialized state chars "
        "sent to model:",
        state_chars_sent,
    )

    expected_state = problem[
        "final_state"
    ]

    matches_ground_truth = (
        states_equivalen(
            final_state,
            expected_state
        )
    )

    print()
    print(
        "Matches benchmark final state:",
        matches_ground_truth,
    )


if __name__ == "__main__":
    run()