from tinygeo.models.ollama_client import OllamaClient


CREATE_POINT_TOOL = {
    "type": "function",
    "function": {
        "name": "create_point",
        "description": "Create a named 2D point.",
        "parameters": {
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
            },
            "required": [
                "name",
                "x",
                "y",
            ],
            "additionalProperties": False,
        },
    },
}


def run_test(
    think: bool,
):
    print()
    print("=" * 70)
    print(f"THINK = {think}")
    print("=" * 70)

    client = OllamaClient(
        model="qwen3:4b",
        think=think,
        num_predict=2048,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "Use the supplied tool. "
                "Do not solve anything else."
            ),
        },
        {
            "role": "user",
            "content": (
                "Create point A at coordinates (0, 0)."
            ),
        },
    ]

    response = client.chat(
        messages=messages,
        tools=[
            CREATE_POINT_TOOL
        ],
        num_predict=2048,
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
        "content:",
        repr(response.text),
    )

    print(
        "tool_calls:",
        response.tool_calls,
    )

    if response.thinking:
        print()
        print("LAST 1000 THINKING CHARS:")
        print(
            response.thinking[-1000:]
        )


if __name__ == "__main__":
    run_test(
        think=True
    )

    run_test(
        think=False
    )