from typing import Any, Dict

from tinygeo.geometry import GeometryState


def execute(
    geo: GeometryState,
    action: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute one structured action against GeometryState.

    The protocol deliberately exposes only primitive
    geometric operations and constructions.

    It does NOT expose theorem proving or automatic
    problem solving.
    """

    try:
        op = action["op"]

        if op == "create_point":
            result = geo.create_point(
                action["name"],
                action["x"],
                action["y"],
            )

        elif op == "create_line":
            result = geo.create_line(
                action["name"],
                action["p1"],
                action["p2"],
            )

        elif op == "create_midpoint":
            result = geo.create_midpoint(
                action["name"],
                action["a"],
                action["b"],
            )

        elif op == "create_intersection":
            result = geo.create_intersection(
                action["name"],
                action["line1"],
                action["line2"],
            )

        elif op == "distance":
            result = geo.distance(
                action["a"],
                action["b"],
            )

        elif op == "angle":
            result = geo.angle(
                action["a"],
                action["b"],
                action["c"],
            )

        elif op == "orientation":
            result = geo.orientation(
                action["a"],
                action["b"],
                action["c"],
            )

        elif op == "collinear":
            result = geo.collinear(
                action["a"],
                action["b"],
                action["c"],
            )

        elif op == "parallel":
            result = geo.parallel(
                action["line1"],
                action["line2"],
            )

        elif op == "perpendicular":
            result = geo.perpendicular(
                action["line1"],
                action["line2"],
            )

        elif op == "snapshot":
            result = geo.snapshot()

        else:
            return {
                "ok": False,
                "error": (
                    f"Unknown operation: {op}"
                ),
            }

        return {
            "ok": True,
            "result": result,
        }

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        return {
            "ok": False,
            "error": str(exc),
        }