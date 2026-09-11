import argparse
import json
from pathlib import Path
from typing import Any

from tinygeo.state_utils import (
    states_equivalent,
)

from benchmarks.generate_compositional_v2 import (
    describe_predicate,
)

from experiments.diagnose_phased_construction import (
    CONSTRUCTION_TOOLS,
    describe_initial_point,
    describe_operation,
    extract_one_tool_call,
    load_problem,
    make_messages,
)

from tinygeo.agent import (
    GEOMETRY_TOOLS,
)

from tinygeo.models.ollama_client import (
    OllamaClient,
)

from tinygeo.session import (
    EMPTY_STATE,
    PersistentGeometrySession,
    StatelessGeometrySession,
)


QUERY_TOOL_NAMES = {
    "distance_equal",
    "distance_less_than",
    "orientation",
    "collinear",
    "point_on_line",
    "parallel",
    "perpendicular",
}


def select_query_tools():
    return [
        tool
        for tool in GEOMETRY_TOOLS
        if tool["function"]["name"]
        in QUERY_TOOL_NAMES
    ]


QUERY_TOOLS = select_query_tools()


def unpack_tool_call(
    call: dict[str, Any],
):
    function = call.get(
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

    if not isinstance(
        arguments,
        dict,
    ):
        raise ValueError(
            "Tool arguments must be an object."
        )

    return (
        name,
        arguments,
    )


def construct_world(
    client,
    problem,
    condition,
    step_token_cap,
):
    if condition == "persistent_state":
        session = PersistentGeometrySession()
        serialized_state = None

    elif condition == "serialized_state":
        session = StatelessGeometrySession()
        serialized_state = EMPTY_STATE

    else:
        raise ValueError(
            f"Unknown condition: {condition}"
        )

    instructions = []

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

    for operation in problem[
        "operations"
    ]:
        instructions.append(
            describe_operation(
                operation
            )
        )

    total_prompt_tokens = 0
    total_completion_tokens = 0
    state_chars_sent = 0

    for instruction in instructions:

        if condition == "serialized_state":
            state_text = json.dumps(
                serialized_state,
                separators=(",", ":"),
            )

            state_chars_sent += len(
                state_text
            )

        messages = make_messages(
            instruction=instruction,
            condition=condition,
            serialized_state=serialized_state,
        )

        response = client.chat(
            messages=messages,
            tools=CONSTRUCTION_TOOLS,
            num_predict=step_token_cap,
        )

        total_prompt_tokens += (
            response.prompt_tokens or 0
        )

        total_completion_tokens += (
            response.completion_tokens or 0
        )

        if (
            response.done_reason == "length"
            and not response.tool_calls
        ):
            raise RuntimeError(
                "Construction step truncated "
                "before a tool call."
            )

        (
            tool_name,
            arguments,
        ) = extract_one_tool_call(
            response
        )

        if tool_name is None:
            raise RuntimeError(
                "Construction produced no tool call."
            )

        action = {
            "op": tool_name,
            **arguments,
        }

        if condition == "persistent_state":

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

        if not result.get(
            "ok",
            False,
        ):
            raise RuntimeError(
                f"Construction error: {result}"
            )

    return {
        "session": session,
        "serialized_state": serialized_state,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "state_chars_sent": state_chars_sent,
    }


def build_query_messages(
    statement,
    condition,
    serialized_state,
):
    system_prompt = """
You are verifying exactly one atomic geometric statement.

A geometric world has already been constructed.

Use exactly one supplied geometry query tool that directly
tests the statement.

Do not reconstruct geometry.
Do not create objects.
Do not answer in prose.
Do not plan future operations.

Make exactly one geometry tool call.
""".strip()

    if condition == "persistent_state":

        user_content = (
            "STATEMENT TO VERIFY:\n"
            f"{statement}"
        )

    elif condition == "serialized_state":

        state_text = json.dumps(
            serialized_state,
            separators=(",", ":"),
        )

        user_content = (
            "CURRENT GEOMETRIC STATE:\n"
            f"{state_text}\n\n"
            "STATEMENT TO VERIFY:\n"
            f"{statement}"
        )

    else:
        raise ValueError(
            condition
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


def verify_statement(
    client,
    predicate,
    statement,
    condition,
    session,
    serialized_state,
    step_token_cap,
):
    messages = build_query_messages(
        statement=statement,
        condition=condition,
        serialized_state=serialized_state,
    )

    state_chars_sent = 0

    if condition == "serialized_state":
        state_chars_sent = len(
            json.dumps(
                serialized_state,
                separators=(",", ":"),
            )
        )

    response = client.chat(
        messages=messages,
        tools=QUERY_TOOLS,
        num_predict=step_token_cap,
    )

    prompt_tokens = (
        response.prompt_tokens or 0
    )

    completion_tokens = (
        response.completion_tokens or 0
    )

    thinking_chars = len(
        response.thinking or ""
    )

    if not response.tool_calls:
        return {
            "truth": None,
            "status": (
                "truncated"
                if response.done_reason == "length"
                else "no_tool_call"
            ),
            "turns": 1,
            "tool_calls": 0,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "thinking_chars": thinking_chars,
            "state_chars_sent": state_chars_sent,
            "serialized_state": serialized_state,
        }

    if len(response.tool_calls) != 1:
        return {
            "truth": None,
            "status": "multiple_tool_calls",
            "turns": 1,
            "tool_calls": len(
                response.tool_calls
            ),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "thinking_chars": thinking_chars,
            "state_chars_sent": state_chars_sent,
            "serialized_state": serialized_state,
        }

    (
        tool_name,
        arguments,
    ) = unpack_tool_call(
        response.tool_calls[0]
    )

    if tool_name not in QUERY_TOOL_NAMES:
        return {
            "truth": None,
            "status": "unexpected_tool",
            "turns": 1,
            "tool_calls": 1,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "thinking_chars": thinking_chars,
            "state_chars_sent": state_chars_sent,
            "serialized_state": serialized_state,
        }

    action = {
        "op": tool_name,
        **arguments,
    }

    if condition == "persistent_state":

        tool_result = session.execute(
            action
        )

    else:

        tool_result = session.execute(
            action,
            state=serialized_state,
        )

        serialized_state = (
            tool_result["state"]
        )

    if not tool_result.get(
        "ok",
        False,
    ):
        return {
            "truth": None,
            "status": "tool_error",
            "turns": 1,
            "tool_calls": 1,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "thinking_chars": thinking_chars,
            "state_chars_sent": state_chars_sent,
            "serialized_state": serialized_state,
        }

    value = tool_result["result"]

    # Most v2 predicates map directly to Boolean
    # primitive geometry queries.
    if isinstance(
        value,
        bool,
    ):
        truth = value

    # Orientation returns a semantic label rather than
    # a Boolean, so compare it with the asserted label.
    elif (
        predicate["kind"]
        == "orientation"
        and isinstance(value, str)
    ):
        truth = (
            value
            == predicate["expected"]
        )

    else:
        return {
            "truth": None,
            "status": "non_boolean_result",
            "turns": 1,
            "tool_calls": 1,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "thinking_chars": thinking_chars,
            "state_chars_sent": state_chars_sent,
            "serialized_state": serialized_state,
        }

    return {
        "truth": truth,
        "status": "ok",
        "turns": 1,
        "tool_calls": 1,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "thinking_chars": thinking_chars,
        "state_chars_sent": state_chars_sent,
        "serialized_state": serialized_state,
    }


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

    print(
        f"Problem: {args.only_id}"
    )

    print(
        f"Condition: {args.condition}"
    )

    print("=" * 70)

    construction = construct_world(
        client=client,
        problem=problem,
        condition=args.condition,
        step_token_cap=args.step_token_cap,
    )

    session = construction[
        "session"
    ]

    serialized_state = construction[
        "serialized_state"
    ]

    if args.condition == "persistent_state":
        final_state = session.snapshot()
    else:
        final_state = serialized_state

    construction_correct = (
        states_equivalent(
            final_state,
            problem["final_state"],
            )
        )

    print(
        "Construction correct:",
        construction_correct,
    )

    print(
        "Construction prompt tokens:",
        construction["prompt_tokens"],
    )

    print(
        "Construction completion tokens:",
        construction["completion_tokens"],
    )

    print(
        "Construction state chars:",
        construction["state_chars_sent"],
    )

    print()
    print("=" * 70)
    print("PREDICATE VERIFICATION")
    print("=" * 70)

    predicted_truths = []

    total_query_prompt_tokens = 0
    total_query_completion_tokens = 0
    total_query_thinking_chars = 0
    total_query_tool_calls = 0
    total_query_state_chars = 0

    for index, predicate in enumerate(
        problem["predicates"],
        start=1,
    ):
        statement = describe_predicate(
            predicate
        )

        expected_truth = problem[
            "predicate_results"
        ][
            index - 1
        ]

        print()
        print(
            f"Predicate {index}:"
        )

        print(
            statement
        )

        result = verify_statement(
            client=client,
            predicate=predicate,
            statement=statement,
            condition=args.condition,
            session=session,
            serialized_state=serialized_state,
            step_token_cap=args.step_token_cap,
        )

        serialized_state = result[
            "serialized_state"
        ]

        predicted_truth = result[
            "truth"
        ]

        predicted_truths.append(
            predicted_truth
        )

        correct = (
            predicted_truth
            == expected_truth
        )

        print(
            "Predicted:",
            predicted_truth,
        )

        print(
            "Expected:",
            expected_truth,
        )

        print(
            "Correct:",
            correct,
        )

        print(
            "Status:",
            result["status"],
        )

        print(
            "Query tool calls:",
            result["tool_calls"],
        )

        total_query_prompt_tokens += (
            result["prompt_tokens"]
        )

        total_query_completion_tokens += (
            result["completion_tokens"]
        )

        total_query_thinking_chars += (
            result["thinking_chars"]
        )

        total_query_tool_calls += (
            result["tool_calls"]
        )

        total_query_state_chars += (
            result["state_chars_sent"]
        )

    if any(
        value is None
        for value in predicted_truths
    ):
        prediction = None

    else:
        prediction = (
            "yes"
            if all(predicted_truths)
            else "no"
        )

    print()
    print("=" * 70)
    print("FINAL")
    print("=" * 70)

    print(
        "Prediction:",
        prediction,
    )

    print(
        "Expected:",
        problem["answer"],
    )

    print(
        "Correct:",
        (
            prediction
            == problem["answer"]
        ),
    )

    print()
    print(
        "Query prompt tokens:",
        total_query_prompt_tokens,
    )

    print(
        "Query completion tokens:",
        total_query_completion_tokens,
    )

    print(
        "Query thinking chars:",
        total_query_thinking_chars,
    )

    print(
        "Query tool calls:",
        total_query_tool_calls,
    )

    print(
        "Query serialized state chars:",
        total_query_state_chars,
    )

    print()
    print(
        "TOTAL prompt tokens:",
        (
            construction["prompt_tokens"]
            + total_query_prompt_tokens
        ),
    )

    print(
        "TOTAL completion tokens:",
        (
            construction["completion_tokens"]
            + total_query_completion_tokens
        ),
    )

    print(
        "TOTAL serialized state chars:",
        (
            construction["state_chars_sent"]
            + total_query_state_chars
        ),
    )


if __name__ == "__main__":
    main()