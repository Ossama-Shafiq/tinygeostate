import json
from typing import Any

from tinygeo.session import (
    EMPTY_STATE,
    PersistentGeometrySession,
    StatelessGeometrySession,
)


ALLOWED_OPERATIONS = {
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
}


AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": [
                "tool",
                "final",
            ],
        },

        "op": {
            "type": "string",
            "enum": [
                "",
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
            ],
        },

        "args": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                },
                "x": {
                    "type": "number",
                },
                "y": {
                    "type": "number",
                },
                "p1": {
                    "type": "string",
                },
                "p2": {
                    "type": "string",
                },
                "a": {
                    "type": "string",
                },
                "b": {
                    "type": "string",
                },
                "c": {
                    "type": "string",
                },
                "line1": {
                    "type": "string",
                },
                "line2": {
                    "type": "string",
                },
            },
            "additionalProperties": False,
        },

        "answer": {
            "type": "string",
            "enum": [
                "",
                "yes",
                "no",
            ],
        },
    },

    "required": [
        "type",
        "op",
        "args",
        "answer",
    ],

    "additionalProperties": False,
}


def build_system_prompt(
    condition: str,
) -> str:

    common = """
You are solving an elementary geometry problem using a
small geometry coprocessor.

You MUST use the geometry tools rather than calculating
derived geometry entirely in your head.

Build the geometric world from the problem step by step.

Available operations:

create_point(name, x, y)
create_line(name, p1, p2)
create_midpoint(name, a, b)
create_intersection(name, line1, line2)

distance(a, b)
angle(a, b, c)
orientation(a, b, c)
collinear(a, b, c)
parallel(line1, line2)
perpendicular(line1, line2)

For a statement saying that a point lies on a line,
use the two points defining that line together with
collinear().

You are NOT given a theorem prover.
You must decide which primitive operations to call and
interpret their results yourself.

Every response must have exactly this JSON shape:

For a tool call:

{
  "type": "tool",
  "op": "operation_name",
  "args": {...},
  "answer": ""
}

When you have enough information:

{
  "type": "final",
  "op": "",
  "args": {},
  "answer": "yes"
}

or:

{
  "type": "final",
  "op": "",
  "args": {},
  "answer": "no"
}

Never put prose outside the JSON object.
""".strip()

    if condition == "persistent_state":
        specific = """
The geometry coprocessor has persistent state.

Once an object is created, you may refer to it by name
in later tool calls without resending its coordinates or
definition.

Tool results will therefore remain compact.
""".strip()

    elif condition == "serialized_state":
        specific = """
The geometry coprocessor itself does NOT retain its
geometric world between calls.

After every call you will receive the complete serialized
geometric state. That serialized state is used to rebuild
the geometry engine on the next call.

Pay attention to the returned state because the world is
being carried through the conversation rather than living
inside a persistent geometry session.
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


def parse_decision(
    text: str,
) -> dict[str, Any]:

    try:
        decision = json.loads(
            text
        )

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Model returned invalid JSON."
        ) from exc

    if not isinstance(
        decision,
        dict,
    ):
        raise ValueError(
            "Model decision must be a JSON object."
        )

    return decision


def run_geometry_agent(
    client,
    problem_prompt: str,
    condition: str,
    token_budget: int = 8192,
    step_token_cap: int = 2048,
    max_steps: int = 40,
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

    final_response = None

    for step in range(
        1,
        max_steps + 1,
    ):
        remaining = (
            token_budget
            - total_completion_tokens
        )

        if remaining <= 0:
            return {
                "prediction": None,
                "status": "token_budget_exhausted",
                "steps": step - 1,
                "tool_calls": tool_calls,
                "tool_errors": tool_errors,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_thinking_chars": total_thinking_chars,
                "truncated_steps": truncated_steps,
                "state_chars_sent": state_chars_sent,
                "peak_state_chars": peak_state_chars,
                "final_response": final_response,
            }

        this_step_limit = min(
            remaining,
            step_token_cap,
        )

        response = client.chat(
            messages=messages,
            response_format=AGENT_SCHEMA,
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

        step_truncated = (
            response.done_reason
            == "length"
        )

        if step_truncated:
            truncated_steps += 1

        if not response.text.strip():
            return {
                "prediction": None,
                "status": (
                    "step_truncated"
                    if step_truncated
                    else "empty_response"
                ),
                "steps": step,
                "tool_calls": tool_calls,
                "tool_errors": tool_errors,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_thinking_chars": total_thinking_chars,
                "truncated_steps": truncated_steps,
                "state_chars_sent": state_chars_sent,
                "peak_state_chars": peak_state_chars,
                "final_response": response.text,
            }

        try:
            decision = parse_decision(
                response.text
            )

        except ValueError:
            return {
                "prediction": None,
                "status": "invalid_json",
                "steps": step,
                "tool_calls": tool_calls,
                "tool_errors": tool_errors,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_thinking_chars": total_thinking_chars,
                "truncated_steps": truncated_steps,
                "state_chars_sent": state_chars_sent,
                "peak_state_chars": peak_state_chars,
                "final_response": response.text,
            }

        messages.append(
            {
                "role": "assistant",
                "content": response.text,
            }
        )

        decision_type = decision.get(
            "type"
        )

        if decision_type == "final":
            answer = decision.get(
                "answer"
            )

            if answer not in {
                "yes",
                "no",
            }:
                return {
                    "prediction": None,
                    "status": "invalid_final",
                    "steps": step,
                    "tool_calls": tool_calls,
                    "tool_errors": tool_errors,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_completion_tokens,
                    "total_thinking_chars": total_thinking_chars,
                    "truncated_steps": truncated_steps,
                    "state_chars_sent": state_chars_sent,
                    "peak_state_chars": peak_state_chars,
                    "final_response": response.text,
                }

            return {
                "prediction": answer,
                "status": "ok",
                "steps": step,
                "tool_calls": tool_calls,
                "tool_errors": tool_errors,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_thinking_chars": total_thinking_chars,
                "truncated_steps": truncated_steps,
                "state_chars_sent": state_chars_sent,
                "peak_state_chars": peak_state_chars,
                "final_response": response.text,
            }

        if decision_type != "tool":
            return {
                "prediction": None,
                "status": "invalid_decision_type",
                "steps": step,
                "tool_calls": tool_calls,
                "tool_errors": tool_errors,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_thinking_chars": total_thinking_chars,
                "truncated_steps": truncated_steps,
                "state_chars_sent": state_chars_sent,
                "peak_state_chars": peak_state_chars,
                "final_response": response.text,
            }

        op = decision.get(
            "op"
        )

        args = decision.get(
            "args"
        )

        if (
            op not in ALLOWED_OPERATIONS
            or not isinstance(args, dict)
        ):
            return {
                "prediction": None,
                "status": "invalid_tool_call",
                "steps": step,
                "tool_calls": tool_calls,
                "tool_errors": tool_errors,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_thinking_chars": total_thinking_chars,
                "truncated_steps": truncated_steps,
                "state_chars_sent": state_chars_sent,
                "peak_state_chars": peak_state_chars,
                "final_response": response.text,
            }

        action = {
            "op": op,
            **args,
        }

        tool_calls += 1

        if condition == "persistent_state":

            tool_result = session.execute(
                action
            )

            message_payload = {
                "tool_result": tool_result,
            }

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

            message_payload = {
                "tool_result": tool_result,
            }

        if not tool_result.get(
            "ok",
            False,
        ):
            tool_errors += 1

        messages.append(
            {
                "role": "user",
                "content": (
                    "TOOL_RESULT:\n"
                    + json.dumps(
                        message_payload,
                        separators=(",", ":"),
                    )
                    + "\nContinue solving the same problem."
                ),
            }
        )

    return {
        "prediction": None,
        "status": "max_steps",
        "steps": max_steps,
        "tool_calls": tool_calls,
        "tool_errors": tool_errors,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_thinking_chars": total_thinking_chars,
        "truncated_steps": truncated_steps,
        "state_chars_sent": state_chars_sent,
        "peak_state_chars": peak_state_chars,
        "final_response": final_response,
    }