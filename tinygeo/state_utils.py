import math
from typing import Any


def states_equivalent(
    actual: dict[str, Any],
    expected: dict[str, Any],
    tolerance: float = 1e-6,
) -> bool:
    """
    Compare two GeometryState snapshots.

    Object identities and topology must match exactly.
    Floating-point coordinates are compared approximately.
    """

    actual_points = actual.get(
        "points",
        {},
    )

    expected_points = expected.get(
        "points",
        {},
    )

    actual_lines = actual.get(
        "lines",
        {},
    )

    expected_lines = expected.get(
        "lines",
        {},
    )

    if set(actual_points) != set(
        expected_points
    ):
        return False

    if set(actual_lines) != set(
        expected_lines
    ):
        return False

    for name in actual_points:
        a = actual_points[name]
        b = expected_points[name]

        if not math.isclose(
            a["x"],
            b["x"],
            rel_tol=tolerance,
            abs_tol=tolerance,
        ):
            return False

        if not math.isclose(
            a["y"],
            b["y"],
            rel_tol=tolerance,
            abs_tol=tolerance,
        ):
            return False

    for name in actual_lines:
        a = actual_lines[name]
        b = expected_lines[name]

        if a["p1"] != b["p1"]:
            return False

        if a["p2"] != b["p2"]:
            return False

    return True