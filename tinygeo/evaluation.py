import re
from typing import Any


def normalize_answer(value: Any) -> str:
    """
    Convert an answer into a simple canonical form.

    This intentionally stays conservative. We don't want a
    complicated evaluator accidentally giving models credit.
    """

    text = str(value).strip().lower()

    # Remove surrounding punctuation/whitespace.
    text = re.sub(r"^[\s.,;:!?]+|[\s.,;:!?]+$", "", text)

    # Common boolean variants.
    yes_values = {
        "yes",
        "true",
        "correct",
    }

    no_values = {
        "no",
        "false",
        "incorrect",
    }

    if text in yes_values:
        return "yes"

    if text in no_values:
        return "no"

    # Normalize integer-looking floats:
    # "90.0" -> "90"
    try:
        number = float(text)

        if number.is_integer():
            return str(int(number))

        return str(number)

    except ValueError:
        pass

    return text


def score_prediction(prediction: Any, expected: Any) -> bool:
    """
    Exact match after conservative normalization.
    """

    return normalize_answer(prediction) == normalize_answer(expected)
