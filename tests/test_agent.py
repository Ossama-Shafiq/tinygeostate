from tinygeo.agent import (
    run_geometry_agent,
)

from tinygeo.models.base import (
    ModelResponse,
)


def tool_call(
    name,
    arguments,
):
    return {
        "function": {
            "name": name,
            "arguments": arguments,
        }
    }


class ScriptedClient:
    def __init__(
        self,
        responses,
    ):
        self.responses = list(
            responses
        )

        self.name = (
            "scripted-test-model"
        )

    def chat(
        self,
        messages,
        response_format=None,
        num_predict=None,
        tools=None,
    ):
        return self.responses.pop(
            0
        )


SCRIPT = [
    ModelResponse(
        text="",
        thinking="",
        tool_calls=[
            tool_call(
                "create_point",
                {
                    "name": "A",
                    "x": 0,
                    "y": 0,
                },
            ),
            tool_call(
                "create_point",
                {
                    "name": "B",
                    "x": 3,
                    "y": 4,
                },
            ),
        ],
        prompt_tokens=10,
        completion_tokens=5,
        done_reason="stop",
    ),

    ModelResponse(
        text="",
        thinking="",
        tool_calls=[
            tool_call(
                "distance",
                {
                    "a": "A",
                    "b": "B",
                },
            )
        ],
        prompt_tokens=10,
        completion_tokens=5,
        done_reason="stop",
    ),

    ModelResponse(
        text="",
        thinking="",
        tool_calls=[
            tool_call(
                "submit_answer",
                {
                    "answer": "yes",
                },
            )
        ],
        prompt_tokens=10,
        completion_tokens=5,
        done_reason="stop",
    ),
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