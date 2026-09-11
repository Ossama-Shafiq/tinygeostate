from copy import deepcopy
from typing import Any, Dict, Optional

from tinygeo.geometry import GeometryState
from tinygeo.protocol import execute


EMPTY_STATE = {
    "points": {},
    "lines": {},
}


def restore_geometry_state(
    snapshot: Optional[Dict[str, Any]],
) -> GeometryState:
    """
    Reconstruct a GeometryState from its serialized snapshot.

    This is intentionally deterministic and contains no
    geometric reasoning.
    """

    geo = GeometryState()

    if snapshot is None:
        snapshot = EMPTY_STATE

    points = snapshot.get(
        "points",
        {},
    )

    lines = snapshot.get(
        "lines",
        {},
    )

    # Points must exist before lines can reference them.
    for name, data in points.items():
        geo.create_point(
            name,
            data["x"],
            data["y"],
        )

    for name, data in lines.items():
        geo.create_line(
            name,
            data["p1"],
            data["p2"],
        )

    return geo


class PersistentGeometrySession:
    """
    Geometry state lives outside the language model.

    The caller only needs to issue operations referencing
    object names. The session retains previous objects.
    """

    def __init__(self):
        self.geo = GeometryState()

    def execute(
        self,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:

        return execute(
            self.geo,
            action,
        )

    def snapshot(self):
        return self.geo.snapshot()


class StatelessGeometrySession:
    """
    No geometric state is retained between calls.

    The caller must explicitly provide the complete serialized
    geometric state with every action.

    After execution, the updated state is returned so that the
    caller may carry it forward through its own context.
    """

    def execute(
        self,
        action: Dict[str, Any],
        state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        geo = restore_geometry_state(
            deepcopy(state)
        )

        result = execute(
            geo,
            action,
        )

        response = {
            "ok": result["ok"],
            "state": geo.snapshot(),
        }

        if result["ok"]:
            response["result"] = result["result"]

        else:
            response["error"] = result["error"]

        return response