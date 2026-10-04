from tinygeo.models.base import (
    ModelResponse,
)
from tinygeo.phased import (
    run_phased_problem,
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


def response(
    tool_name,
    arguments,
):
    return ModelResponse(
        text="",
        thinking="",
        tool_calls=[
            tool_call(
                tool_name,
                arguments,
            )
        ],
        prompt_tokens=10,
        completion_tokens=5,
        done_reason="stop",
    )


def make_problem():
    return {
        "id": "test",
        "answer": "yes",

        "initial_points": {
            "A": [0, 0],
            "B": [4, 0],
            "C": [0, 4],
        },

        "operations": [
            {
                "op": "line",
                "name": "L1",
                "p1": "A",
                "p2": "B",
            }
        ],

        "predicates": [
            {
                "kind": "orientation",
                "points": [
                    "A",
                    "B",
                    "C",
                ],
                "expected": (
                    "counterclockwise"
                ),
            }
        ],

        "predicate_results": [
            True
        ],

        "final_state": {
            "points": {
                "A": {
                    "x": 0.0,
                    "y": 0.0,
                },
                "B": {
                    "x": 4.0,
                    "y": 0.0,
                },
                "C": {
                    "x": 0.0,
                    "y": 4.0,
                },
            },

            "lines": {
                "L1": {
                    "p1": "A",
                    "p2": "B",
                }
            },
        },
    }


def scripted_responses():
    return [
        response(
            "create_point",
            {
                "name": "A",
                "x": 0,
                "y": 0,
            },
        ),

        response(
            "create_point",
            {
                "name": "B",
                "x": 4,
                "y": 0,
            },
        ),

        response(
            "create_point",
            {
                "name": "C",
                "x": 0,
                "y": 4,
            },
        ),

        response(
            "create_line",
            {
                "name": "L1",
                "p1": "A",
                "p2": "B",
            },
        ),

        response(
            "orientation",
            {
                "a": "A",
                "b": "B",
                "c": "C",
            },
        ),
    ]


def test_persistent_phased_problem():
    client = ScriptedClient(
        scripted_responses()
    )

    result = run_phased_problem(
        client=client,
        problem=make_problem(),
        condition="persistent_state",
        step_token_cap=2048,
    )

    assert result[
        "construction_correct"
    ]

    assert result[
        "all_predicates_correct"
    ]

    assert result[
        "prediction"
    ] == "yes"

    assert result[
        "correct"
    ]

    assert (
        result[
            "total_state_chars"
        ]
        == 0
    )


def test_serialized_phased_problem():
    client = ScriptedClient(
        scripted_responses()
    )

    result = run_phased_problem(
        client=client,
        problem=make_problem(),
        condition="serialized_state",
        step_token_cap=2048,
    )

    assert result[
        "construction_correct"
    ]

    assert result[
        "all_predicates_correct"
    ]

    assert result[
        "prediction"
    ] == "yes"

    assert result[
        "correct"
    ]

    assert (
        result[
            "total_state_chars"
        ]
        > 0
    )