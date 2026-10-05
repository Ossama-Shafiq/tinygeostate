import json
from copy import deepcopy
from typing import Any

from tinygeo.agent import GEOMETRY_TOOLS
from tinygeo.session import (
    EMPTY_STATE,
    PersistentGeometrySession,
    StatelessGeometrySession,
)
from tinygeo.state_utils import states_equivalent


CONSTRUCTION_TOOL_NAMES = {
    "create_point",
    "create_line",
    "create_midpoint",
    "create_intersection",
}


QUERY_TOOL_NAMES = {
    "distance_equal",
    "distance_less_than",
    "orientation",
    "collinear",
    "point_on_line",
    "parallel",
    "perpendicular",
}


def compact_json(
    value: Any,
) -> str:
    return json.dumps(
        value,
        separators=(",", ":"),
    )


def select_tools(
    allowed_names: set[str],
) -> list[dict[str, Any]]:
    return [
        tool
        for tool in GEOMETRY_TOOLS
        if tool["function"]["name"]
        in allowed_names
    ]


CONSTRUCTION_TOOLS = select_tools(
    CONSTRUCTION_TOOL_NAMES
)

QUERY_TOOLS = select_tools(
    QUERY_TOOL_NAMES
)

REQUIRED_ARGUMENTS_BY_TOOL = {
    tool["function"]["name"]: set(
        tool["function"]
        ["parameters"]
        .get("required", [])
    )
    for tool in GEOMETRY_TOOLS
}


def missing_required_arguments(
    tool_name: str,
    arguments: dict[str, Any],
) -> list[str]:
    required = (
        REQUIRED_ARGUMENTS_BY_TOOL
        .get(
            tool_name,
            set(),
        )
    )

    supplied = set(
        arguments
    )

    return sorted(
        required - supplied
    )


def format_number(
    value,
) -> str:
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
            f"{operation['a']} and "
            f"{operation['b']}."
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


def describe_predicate(
    predicate: dict[str, Any],
) -> str:
    kind = predicate["kind"]

    points = predicate.get(
        "points",
        [],
    )

    lines = predicate.get(
        "lines",
        [],
    )

    if kind == "line_parallel":
        return (
            f"line {lines[0]} is parallel "
            f"to line {lines[1]}"
        )

    if kind == "line_perpendicular":
        return (
            f"line {lines[0]} is perpendicular "
            f"to line {lines[1]}"
        )

    if kind == "point_on_line":
        return (
            f"point {points[0]} lies "
            f"on line {lines[0]}"
        )

    if kind == "collinear":
        return (
            f"points {points[0]}, {points[1]}, "
            f"and {points[2]} are collinear"
        )

    if kind == "orientation":
        return (
            f"point {points[2]} is "
            f"{predicate['expected']} relative "
            f"to the directed line from "
            f"{points[0]} to {points[1]}"
        )

    if kind == "distance_eq":
        return (
            f"the distance between points "
            f"{points[0]} and {points[1]} "
            f"equals the distance between points "
            f"{points[2]} and {points[3]}"
        )

    if kind == "distance_lt":
        return (
            f"the distance between points "
            f"{points[0]} and {points[1]} "
            f"is less than the distance between points "
            f"{points[2]} and {points[3]}"
        )

    raise ValueError(
        f"Unknown predicate: {kind}"
    )


def expected_query_tool(
    predicate: dict[str, Any],
) -> str:
    mapping = {
        "line_parallel": "parallel",
        "line_perpendicular": "perpendicular",
        "point_on_line": "point_on_line",
        "collinear": "collinear",
        "orientation": "orientation",
        "distance_eq": "distance_equal",
        "distance_lt": "distance_less_than",
    }

    return mapping[
        predicate["kind"]
    ]


def build_construction_steps(
    problem: dict[str, Any],
):
    steps = []

    for (
        name,
        coordinates,
    ) in problem["initial_points"].items():

        steps.append(
            {
                "instruction": (
                    describe_initial_point(
                        name,
                        coordinates,
                    )
                ),
                "expected_tool": "create_point",
            }
        )

    for operation in problem["operations"]:
        op = operation["op"]

        expected_tool = {
            "midpoint": "create_midpoint",
            "line": "create_line",
            "intersection": (
                "create_intersection"
            ),
        }[op]

        steps.append(
            {
                "instruction": (
                    describe_operation(
                        operation
                    )
                ),
                "expected_tool": expected_tool,
            }
        )

    return steps


def extract_one_tool_call(
    response,
):
    calls = response.tool_calls or []

    if len(calls) == 0:
        return None, None, "no_tool_call"

    if len(calls) != 1:
        return (
            None,
            None,
            "multiple_tool_calls",
        )

    function = calls[0].get(
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
        try:
            arguments = json.loads(
                arguments
            )

        except json.JSONDecodeError:
            return (
                None,
                None,
                "invalid_arguments_json",
            )

    if not isinstance(
        arguments,
        dict,
    ):
        return (
            None,
            None,
            "invalid_arguments",
        )

    return (
        name,
        arguments,
        "ok",
    )


def make_construction_messages(
    instruction: str,
    condition: str,
    serialized_state,
):
    system_prompt = """
You execute exactly one explicit geometric construction instruction.

Use exactly one supplied geometry construction tool.

Do not solve the overall geometry problem.
Do not reason about future constructions.
Do not perform extra operations.
Do not answer in prose.

Translate only the current instruction into the correct tool call.
""".strip()

    if condition == "persistent_state":
        user_content = (
            "CURRENT INSTRUCTION:\n"
            f"{instruction}"
        )

    elif condition == "serialized_state":
        user_content = (
            "CURRENT GEOMETRIC STATE:\n"
            f"{compact_json(serialized_state)}"
            "\n\nCURRENT INSTRUCTION:\n"
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


def make_query_messages(
    statement: str,
    condition: str,
    serialized_state,
):
    system_prompt = """
You are verifying exactly one atomic geometric statement.

A geometric world has already been constructed.

Use exactly one supplied primitive geometry query tool that
directly tests the statement.

Do not reconstruct geometry.
Do not create new objects.
Do not answer in prose.
Do not plan future operations.

Make exactly one geometry query tool call.
""".strip()

    if condition == "persistent_state":
        user_content = (
            "STATEMENT TO VERIFY:\n"
            f"{statement}"
        )

    elif condition == "serialized_state":
        user_content = (
            "CURRENT GEOMETRIC STATE:\n"
            f"{compact_json(serialized_state)}"
            "\n\nSTATEMENT TO VERIFY:\n"
            f"{statement}"
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


def run_construction(
    client,
    problem: dict[str, Any],
    condition: str,
    step_token_cap: int,
):
    if condition == "persistent_state":
        session = PersistentGeometrySession()
        serialized_state = None

    elif condition == "serialized_state":
        session = StatelessGeometrySession()
        serialized_state = deepcopy(
            EMPTY_STATE
        )

    else:
        raise ValueError(
            f"Unknown condition: {condition}"
        )

    prompt_tokens = 0
    completion_tokens = 0
    thinking_chars = 0

    state_chars_sent = 0
    peak_state_chars = 0

    tool_errors = 0
    successful_steps = 0

    details = []

    steps = build_construction_steps(
        problem
    )

    status = "ok"

    for step_number, step in enumerate(
        steps,
        start=1,
    ):
        instruction = step[
            "instruction"
        ]

        expected_tool = step[
            "expected_tool"
        ]

        current_state_chars = 0

        if condition == "serialized_state":
            current_state_chars = len(
                compact_json(
                    serialized_state
                )
            )

            state_chars_sent += (
                current_state_chars
            )

            peak_state_chars = max(
                peak_state_chars,
                current_state_chars,
            )

        messages = (
            make_construction_messages(
                instruction=instruction,
                condition=condition,
                serialized_state=(
                    serialized_state
                ),
            )
        )

        response = client.chat(
            messages=messages,
            tools=CONSTRUCTION_TOOLS,
            num_predict=step_token_cap,
        )

        prompt_tokens += (
            response.prompt_tokens or 0
        )

        completion_tokens += (
            response.completion_tokens or 0
        )

        thinking_chars += len(
            response.thinking or ""
        )

        (
            tool_name,
            arguments,
            parse_status,
        ) = extract_one_tool_call(
            response
        )

        detail = {
            "step": step_number,
            "instruction": instruction,
            "expected_tool": expected_tool,
            "selected_tool": tool_name,
            "arguments": arguments,
            "prompt_tokens": (
                response.prompt_tokens or 0
            ),
            "completion_tokens": (
                response.completion_tokens
                or 0
            ),
            "thinking_chars": len(
                response.thinking or ""
            ),
            "done_reason": (
                response.done_reason
            ),
            "state_chars": (
                current_state_chars
            ),
        }

        if parse_status != "ok":
            if (
                response.done_reason
                == "length"
            ):
                status = "truncated"

            else:
                status = parse_status

            detail["status"] = status
            details.append(detail)
            break

        if (
            tool_name
            not in CONSTRUCTION_TOOL_NAMES
        ):
            status = "unexpected_tool"
            detail["status"] = status
            details.append(detail)
            break

        if tool_name != expected_tool:
            status = "wrong_tool_selection"
            detail["status"] = status
            details.append(detail)
            break

        missing_arguments = (
            missing_required_arguments(
                tool_name,
                arguments,
            )
        )

        if missing_arguments:
            status = (
                "missing_required_argument"
            )

            detail[
                "missing_arguments"
            ] = missing_arguments

            detail["status"] = status
            details.append(detail)
            break

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

        detail["tool_result"] = (
            tool_result
        )

        if not tool_result.get(
            "ok",
            False,
        ):
            tool_errors += 1
            status = "tool_error"
            detail["status"] = status
            details.append(detail)
            break

        successful_steps += 1

        detail["status"] = "ok"
        details.append(detail)

    if condition == "persistent_state":
        final_state = (
            session.snapshot()
        )

    else:
        final_state = serialized_state

    construction_correct = (
        status == "ok"
        and successful_steps
        == len(steps)
        and states_equivalent(
            final_state,
            problem["final_state"],
        )
    )

    if (
        status == "ok"
        and not construction_correct
    ):
        status = "state_mismatch"

    return {
        "status": status,
        "correct": construction_correct,
        "steps_total": len(steps),
        "steps_successful": (
            successful_steps
        ),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": (
            completion_tokens
        ),
        "thinking_chars": thinking_chars,
        "state_chars_sent": (
            state_chars_sent
        ),
        "peak_state_chars": (
            peak_state_chars
        ),
        "tool_errors": tool_errors,
        "details": details,
        "session": session,
        "serialized_state": (
            serialized_state
        ),
        "final_state": final_state,
    }


def run_predicate(
    client,
    predicate: dict[str, Any],
    expected_truth: bool,
    condition: str,
    session,
    serialized_state,
    step_token_cap: int,
):
    statement = describe_predicate(
        predicate
    )

    expected_tool = (
        expected_query_tool(
            predicate
        )
    )

    state_chars_sent = 0

    if condition == "serialized_state":
        state_chars_sent = len(
            compact_json(
                serialized_state
            )
        )

    messages = make_query_messages(
        statement=statement,
        condition=condition,
        serialized_state=serialized_state,
    )

    response = client.chat(
        messages=messages,
        tools=QUERY_TOOLS,
        num_predict=step_token_cap,
    )

    (
        tool_name,
        arguments,
        parse_status,
    ) = extract_one_tool_call(
        response
    )

    result = {
        "statement": statement,
        "predicate_kind": (
            predicate["kind"]
        ),
        "expected_truth": (
            expected_truth
        ),
        "predicted_truth": None,
        "correct": False,
        "expected_tool": expected_tool,
        "selected_tool": tool_name,
        "arguments": arguments,
        "status": parse_status,
        "prompt_tokens": (
            response.prompt_tokens or 0
        ),
        "completion_tokens": (
            response.completion_tokens or 0
        ),
        "thinking_chars": len(
            response.thinking or ""
        ),
        "done_reason": (
            response.done_reason
        ),
        "state_chars_sent": (
            state_chars_sent
        ),
        "tool_error": False,
    }

    if parse_status != "ok":
        if (
            response.done_reason
            == "length"
        ):
            result["status"] = (
                "truncated"
            )

        return (
            result,
            serialized_state,
        )

    if tool_name not in QUERY_TOOL_NAMES:
        result["status"] = (
            "unexpected_tool"
        )

        return (
            result,
            serialized_state,
        )

    if tool_name != expected_tool:
        result["status"] = (
            "wrong_tool_selection"
        )

        return (
            result,
            serialized_state,
        )

    missing_arguments = (
        missing_required_arguments(
            tool_name,
            arguments,
        )
    )

    if missing_arguments:
        result["status"] = (
            "missing_required_argument"
        )

        result[
            "missing_arguments"
        ] = missing_arguments

        return (
            result,
            serialized_state,
        )

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

    result["tool_result"] = (
        tool_result
    )

    if not tool_result.get(
        "ok",
        False,
    ):
        result["status"] = "tool_error"
        result["tool_error"] = True

        return (
            result,
            serialized_state,
        )

    value = tool_result[
        "result"
    ]

    if isinstance(
        value,
        bool,
    ):
        predicted_truth = value

    elif (
        predicate["kind"]
        == "orientation"
        and isinstance(
            value,
            str,
        )
    ):
        predicted_truth = (
            value
            == predicate["expected"]
        )

    else:
        result["status"] = (
            "non_boolean_result"
        )

        return (
            result,
            serialized_state,
        )

    result["predicted_truth"] = (
        predicted_truth
    )

    result["correct"] = (
        predicted_truth
        == expected_truth
    )

    result["status"] = "ok"

    return (
        result,
        serialized_state,
    )


def run_phased_problem(
    client,
    problem: dict[str, Any],
    condition: str,
    step_token_cap: int = 2048,
):
    construction = run_construction(
        client=client,
        problem=problem,
        condition=condition,
        step_token_cap=step_token_cap,
    )

    predicate_details = []

    query_prompt_tokens = 0
    query_completion_tokens = 0
    query_thinking_chars = 0
    query_state_chars = 0

    query_tool_errors = 0

    serialized_state = construction[
        "serialized_state"
    ]

    if construction["correct"]:
        for (
            predicate,
            expected_truth,
        ) in zip(
            problem["predicates"],
            problem["predicate_results"],
        ):
            (
                predicate_result,
                serialized_state,
            ) = run_predicate(
                client=client,
                predicate=predicate,
                expected_truth=(
                    expected_truth
                ),
                condition=condition,
                session=construction[
                    "session"
                ],
                serialized_state=(
                    serialized_state
                ),
                step_token_cap=(
                    step_token_cap
                ),
            )

            predicate_details.append(
                predicate_result
            )

            query_prompt_tokens += (
                predicate_result[
                    "prompt_tokens"
                ]
            )

            query_completion_tokens += (
                predicate_result[
                    "completion_tokens"
                ]
            )

            query_thinking_chars += (
                predicate_result[
                    "thinking_chars"
                ]
            )

            query_state_chars += (
                predicate_result[
                    "state_chars_sent"
                ]
            )

            query_tool_errors += int(
                predicate_result[
                    "tool_error"
                ]
            )

    predicate_total = len(
        problem["predicates"]
    )

    predicate_valid = sum(
        result["predicted_truth"]
        is not None
        for result in predicate_details
    )

    predicate_correct = sum(
        result["correct"]
        for result in predicate_details
    )

    all_predicates_valid = (
        len(predicate_details)
        == predicate_total
        and predicate_valid
        == predicate_total
    )

    all_predicates_correct = (
        len(predicate_details)
        == predicate_total
        and predicate_correct
        == predicate_total
    )

    if (
        construction["correct"]
        and all_predicates_valid
    ):
        prediction = (
            "yes"
            if all(
                result[
                    "predicted_truth"
                ]
                for result
                in predicate_details
            )
            else "no"
        )

    else:
        prediction = None

    correct = (
        prediction
        == problem["answer"]
    )

    total_prompt_tokens = (
        construction["prompt_tokens"]
        + query_prompt_tokens
    )

    total_completion_tokens = (
        construction[
            "completion_tokens"
        ]
        + query_completion_tokens
    )

    total_thinking_chars = (
        construction["thinking_chars"]
        + query_thinking_chars
    )

    total_state_chars = (
        construction[
            "state_chars_sent"
        ]
        + query_state_chars
    )

    return {
        "prediction": prediction,
        "expected": problem["answer"],
        "correct": correct,

        "construction_status": (
            construction["status"]
        ),
        "construction_correct": (
            construction["correct"]
        ),
        "construction_steps_total": (
            construction["steps_total"]
        ),
        "construction_steps_successful": (
            construction[
                "steps_successful"
            ]
        ),

        "predicate_total": (
            predicate_total
        ),
        "predicate_valid": (
            predicate_valid
        ),
        "predicate_correct": (
            predicate_correct
        ),
        "all_predicates_valid": (
            all_predicates_valid
        ),
        "all_predicates_correct": (
            all_predicates_correct
        ),

        "construction_prompt_tokens": (
            construction[
                "prompt_tokens"
            ]
        ),
        "construction_completion_tokens": (
            construction[
                "completion_tokens"
            ]
        ),
        "construction_thinking_chars": (
            construction[
                "thinking_chars"
            ]
        ),
        "construction_state_chars": (
            construction[
                "state_chars_sent"
            ]
        ),
        "construction_peak_state_chars": (
            construction[
                "peak_state_chars"
            ]
        ),

        "query_prompt_tokens": (
            query_prompt_tokens
        ),
        "query_completion_tokens": (
            query_completion_tokens
        ),
        "query_thinking_chars": (
            query_thinking_chars
        ),
        "query_state_chars": (
            query_state_chars
        ),

        "total_prompt_tokens": (
            total_prompt_tokens
        ),
        "total_completion_tokens": (
            total_completion_tokens
        ),
        "total_thinking_chars": (
            total_thinking_chars
        ),
        "total_state_chars": (
            total_state_chars
        ),

        "tool_errors": (
            construction["tool_errors"]
            + query_tool_errors
        ),

        "construction_details": (
            construction["details"]
        ),

        "predicate_details": (
            predicate_details
        ),
    }