import json

from tinygeo.agent import (
    run_geometry_agent,
)

from tinygeo.models.base import (
    ModelResponse,
)


class ScriptedClient:
    def __init__(
        self,
        decisions,
    ):
        self.decisions = list(
            decisions
        )

        self.name = "scripted-test-model"

    def chat(
        self,
        messages,
        response_format=None,
        num_predict=None,
    ):
        decision = self.decisions.pop(
            0
        )

        return ModelResponse(
            text=json.dumps(
                decision
            ),
            thinking="",
            prompt_tokens=10,
            completion_tokens=5,
            done_reason="stop",
        )


SCRIPT = [
    {
        "type": "tool",
        "op": "create_point",
        "args": {
            "name": "A",
            "x": 0,
            "y": 0,
        },
        "answer": "",
    },

    {
        "type": "tool",
        "op": "create_point",
        "args": {
            "name": "B",
            "x": 3,
            "y": 4,
        },
        "answer": "",
    },

    {
        "type": "tool",
        "op": "distance",
        "args": {
            "a": "A",
            "b": "B",
        },
        "answer": "",
    },

    {
        "type": "final",
        "op": "",
        "args": {},
        "answer": "yes",
    },
]


def test_persistent_agent():
    client = ScriptedClient(
        SCRIPT
    )

    result = run_geometry_agent(
        client=client,
        problem_prompt=(
            "A=(0,0), B=(3,4). "
            "Is distance AB equal to 5?"
        ),
        condition="persistent_state",
    )

    assert (
        result["prediction"]
        == "yes"
    )

    assert (
        result["status"]
        == "ok"
    )

    assert (
        result["tool_calls"]
        == 3
    )

    assert (
        result["state_chars_sent"]
        == 0
    )


def test_serialized_agent():
    client = ScriptedClient(
        SCRIPT
    )

    result = run_geometry_agent(
        client=client,
        problem_prompt=(
            "A=(0,0), B=(3,4). "
            "Is distance AB equal to 5?"
        ),
        condition="serialized_state",
    )

    assert (
        result["prediction"]
        == "yes"
    )

    assert (
        result["status"]
        == "ok"
    )

    assert (
        result["tool_calls"]
        == 3
    )

    assert (
        result["state_chars_sent"]
        > 0
    )