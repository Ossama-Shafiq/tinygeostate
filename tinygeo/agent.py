import json
from typing import Any

from tinygeo.session import (
    EMPTY_STATE,
    PersistentGeometrySession,
    StatelessGeometrySession,
)


def make_tool(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: list[str],
):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


STRING = {"type": "string"}
NUMBER = {"type": "number"}


GEOMETRY_TOOLS = [
    make_tool(
        "create_point",
        "Create a named point with explicit x and y coordinates.",
        {
            "name": STRING,
            "x": NUMBER,
            "y": NUMBER,
        },
        ["name", "x", "y"],
    ),

    make_tool(
        "create_line",
        "Create a named infinite line through two existing points.",
        {
            "name": STRING,
            "p1": STRING,
            "p2": STRING,
        },
        ["name", "p1", "p2"],
    ),

    make_tool(
        "create_midpoint",
        "Create a named point at the midpoint of two existing points.",
        {
            "name": STRING,
            "a": STRING,
            "b": STRING,
        },
        ["name", "a", "b"],
    ),

    make_tool(
        "create_intersection",
        "Create a named point at the intersection of two existing lines.",
        {
            "name": STRING,
            "line1": STRING,
            "line2": STRING,
        },
        ["name", "line1", "line2"],
    ),

    make_tool(
        "distance",
        "Return the distance between two existing points.",
        {
            "a": STRING,
            "b": STRING,
        },
        ["a", "b"],
    ),

    make_tool(
        "distance_equal",
        (
            "Return whether distance AB equals "
            "distance CD."
        ),
        {
            "a": STRING,
            "b": STRING,
            "c": STRING,
            "d": STRING,
        },
        ["a", "b", "c", "d"],
    ),

    make_tool(
        "distance_less_than",
        (
            "Return whether distance AB is less "
            "than distance CD."
        ),
        {
            "a": STRING,
            "b": STRING,
            "c": STRING,
            "d": STRING,
        },
        ["a", "b", "c", "d"],
    ),

    make_tool(
        "angle",
        "Return angle ABC in degrees. B is the vertex.",
        {
            "a": STRING,
            "b": STRING,
            "c": STRING,
        },
        ["a", "b", "c"],
    ),

    make_tool(
        "orientation",
        (
            "Return whether point C is clockwise, "
            "counterclockwise, or collinear relative "
            "to directed line A to B."
        ),
        {
            "a": STRING,
            "b": STRING,
            "c": STRING,
        },
        ["a", "b", "c"],
    ),

    make_tool(
        "collinear",
        "Return whether three existing points are collinear.",
        {
            "a": STRING,
            "b": STRING,
            "c": STRING,
        },
        ["a", "b", "c"],
    ),

    make_tool(
        "point_on_line",
        "Return whether an existing point lies on an existing line.",
        {
            "point": STRING,
            "line": STRING,
        },
        ["point", "line"],
    ),

    make_tool(
        "parallel",
        "Return whether two existing lines are parallel.",
        {
            "line1": STRING,
            "line2": STRING,
        },
        ["line1", "line2"],
    ),

    make_tool(
        "perpendicular",
        "Return whether two existing lines are perpendicular.",
        {
            "line1": STRING,
            "line2": STRING,
        },
        ["line1", "line2"],
    ),

    make_tool(
        "submit_answer",
        (
            "Submit the final yes/no answer. "
            "Only call this when you have finished solving."
        ),
        {
            "answer": {
                "type": "string",
                "enum": ["yes", "no"],
            }
        },
        ["answer"],
    ),
]


GEOMETRY_OPERATION_NAMES = {
    "create_point",
    "create_line",
    "create_midpoint",
    "create_intersection",
    "distance",
    "angle",
    "orientation",
    "collinear",
    "parallel",
    "perpendicular",
    "point_on_line",
    "distance_equal",
    "distance_less_than",
}


def build_system_prompt(
    condition: str,
) -> str:

    common = """
You are in a multi-turn geometry agent loop.

Use the supplied geometry tools to solve the problem.

IMPORTANT:
- Do not calculate derived geometric coordinates yourself
  when an appropriate geometry tool exists.
- Create the explicitly given starting points first.
- Follow the requested constructions using the tools.
- Use primitive geometry queries to verify the final statements.
- The tools do not prove the theorem or decide the answer for you.
- When you know whether ALL requested statements are true,
  call submit_answer with "yes" or "no".
- Do not answer in ordinary prose.
- You may make multiple tool calls while solving.
- Do not spend a long reasoning trace before obvious object-creation calls.
""".strip()

    if condition == "persistent_state":
        specific = """
The geometry engine has persistent state.

Once you create a point, line, midpoint, or intersection,
it remains available in later tool calls by name.

Tool results are compact because the geometric world lives
outside your language context.
""".strip()

    elif condition == "serialized_state":
        specific = """
The geometry engine is reconstructed between interactions.

The complete serialized geometry state is returned with
geometry tool results and is therefore carried through the
conversation rather than living in a persistent external
geometry world.
""".strip()

    else:
        raise ValueError(
            f"Unknown condition: {condition}"
        )

    return (
        common
        + "\n\n"
        + specific
    )


def extract_tool_call(
    call: dict[str, Any],
):
    function = call.get(
        "function",
        {}
    )

    name = function.get(
        "name"
    )

    arguments = function.get(
        "arguments",
        {}
    )

    # Defensive handling in case arguments arrive
    # as encoded JSON rather than as a dictionary.
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


def result_record(
    *,
    prediction,
    status,
    steps,
    tool_calls,
    tool_errors,
    total_prompt_tokens,
    total_completion_tokens,
    total_thinking_chars,
    truncated_steps,
    state_chars_sent,
    peak_state_chars,
):
    return {
        "prediction": prediction,
        "status": status,
        "steps": steps,
        "tool_calls": tool_calls,
        "tool_errors": tool_errors,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_thinking_chars": total_thinking_chars,
        "truncated_steps": truncated_steps,
        "state_chars_sent": state_chars_sent,
        "peak_state_chars": peak_state_chars,
    }


def run_geometry_agent(
    client,
    problem_prompt: str,
    condition: str,
    token_budget: int = 8192,
    step_token_cap: int = 4096,
    max_steps: int = 30,
) -> dict[str, Any]:

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

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(
                condition
            ),
        },
        {
            "role": "user",
            "content": problem_prompt,
        },
    ]

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_thinking_chars = 0

    tool_calls = 0
    tool_errors = 0
    truncated_steps = 0

    state_chars_sent = 0
    peak_state_chars = 0

    for step in range(
        1,
        max_steps + 1,
    ):
        remaining = (
            token_budget
            - total_completion_tokens
        )

        if remaining <= 0:
            return result_record(
                prediction=None,
                status="token_budget_exhausted",
                steps=step - 1,
                tool_calls=tool_calls,
                tool_errors=tool_errors,
                total_prompt_tokens=total_prompt_tokens,
                total_completion_tokens=total_completion_tokens,
                total_thinking_chars=total_thinking_chars,
                truncated_steps=truncated_steps,
                state_chars_sent=state_chars_sent,
                peak_state_chars=peak_state_chars,
            )

        this_step_limit = min(
            remaining,
            step_token_cap,
        )

        response = client.chat(
            messages=messages,
            tools=GEOMETRY_TOOLS,
            num_predict=this_step_limit,
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

        if response.done_reason == "length":
            truncated_steps += 1

        assistant_message = {
            "role": "assistant",
            "content": response.text or "",
        }

        if response.tool_calls:
            assistant_message[
                "tool_calls"
            ] = response.tool_calls

        messages.append(
            assistant_message
        )

        # If no native tool call appeared, the agent
        # has failed to follow our interface.
        if not response.tool_calls:
            return result_record(
                prediction=None,
                status=(
                    "step_truncated"
                    if response.done_reason == "length"
                    else "no_tool_call"
                ),
                steps=step,
                tool_calls=tool_calls,
                tool_errors=tool_errors,
                total_prompt_tokens=total_prompt_tokens,
                total_completion_tokens=total_completion_tokens,
                total_thinking_chars=total_thinking_chars,
                truncated_steps=truncated_steps,
                state_chars_sent=state_chars_sent,
                peak_state_chars=peak_state_chars,
            )

        for call in response.tool_calls:

            try:
                (
                    tool_name,
                    arguments,
                ) = extract_tool_call(
                    call
                )

            except (
                ValueError,
                json.JSONDecodeError,
            ):
                return result_record(
                    prediction=None,
                    status="invalid_tool_call",
                    steps=step,
                    tool_calls=tool_calls,
                    tool_errors=tool_errors,
                    total_prompt_tokens=total_prompt_tokens,
                    total_completion_tokens=total_completion_tokens,
                    total_thinking_chars=total_thinking_chars,
                    truncated_steps=truncated_steps,
                    state_chars_sent=state_chars_sent,
                    peak_state_chars=peak_state_chars,
                )

            # ------------------------------------------
            # Final-answer pseudo-tool
            # ------------------------------------------

            if tool_name == "submit_answer":

                answer = arguments.get(
                    "answer"
                )

                if answer not in {
                    "yes",
                    "no",
                }:
                    return result_record(
                        prediction=None,
                        status="invalid_final",
                        steps=step,
                        tool_calls=tool_calls,
                        tool_errors=tool_errors,
                        total_prompt_tokens=total_prompt_tokens,
                        total_completion_tokens=total_completion_tokens,
                        total_thinking_chars=total_thinking_chars,
                        truncated_steps=truncated_steps,
                        state_chars_sent=state_chars_sent,
                        peak_state_chars=peak_state_chars,
                    )

                return result_record(
                    prediction=answer,
                    status="ok",
                    steps=step,
                    tool_calls=tool_calls,
                    tool_errors=tool_errors,
                    total_prompt_tokens=total_prompt_tokens,
                    total_completion_tokens=total_completion_tokens,
                    total_thinking_chars=total_thinking_chars,
                    truncated_steps=truncated_steps,
                    state_chars_sent=state_chars_sent,
                    peak_state_chars=peak_state_chars,
                )

            if (
                tool_name
                not in GEOMETRY_OPERATION_NAMES
            ):
                return result_record(
                    prediction=None,
                    status="unknown_tool",
                    steps=step,
                    tool_calls=tool_calls,
                    tool_errors=tool_errors,
                    total_prompt_tokens=total_prompt_tokens,
                    total_completion_tokens=total_completion_tokens,
                    total_thinking_chars=total_thinking_chars,
                    truncated_steps=truncated_steps,
                    state_chars_sent=state_chars_sent,
                    peak_state_chars=peak_state_chars,
                )

            action = {
                "op": tool_name,
                **arguments,
            }

            tool_calls += 1

            # ------------------------------------------
            # Persistent condition
            # ------------------------------------------

            if condition == "persistent_state":

                tool_result = session.execute(
                    action
                )

                tool_content = (
                    tool_result
                )

            # ------------------------------------------
            # Serialized condition
            # ------------------------------------------

            else:

                tool_result = session.execute(
                    action,
                    state=serialized_state,
                )

                serialized_state = (
                    tool_result["state"]
                )

                state_text = json.dumps(
                    serialized_state,
                    separators=(",", ":"),
                )

                state_length = len(
                    state_text
                )

                state_chars_sent += (
                    state_length
                )

                peak_state_chars = max(
                    peak_state_chars,
                    state_length,
                )

                tool_content = (
                    tool_result
                )

            if not tool_result.get(
                "ok",
                False,
            ):
                tool_errors += 1

            messages.append(
                {
                    "role": "tool",
                    "tool_name": tool_name,
                    "content": json.dumps(
                        tool_content,
                        separators=(",", ":"),
                    ),
                }
            )

    return result_record(
        prediction=None,
        status="max_steps",
        steps=max_steps,
        tool_calls=tool_calls,
        tool_errors=tool_errors,
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        total_thinking_chars=total_thinking_chars,
        truncated_steps=truncated_steps,
        state_chars_sent=state_chars_sent,
        peak_state_chars=peak_state_chars,
    )