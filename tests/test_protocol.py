from tinygeo.geometry import GeometryState
from tinygeo.protocol import execute


def test_protocol_creates_persistent_points():
    geo = GeometryState()

    execute(
        geo,
        {
            "op": "create_point",
            "name": "A",
            "x": 0,
            "y": 0,
        },
    )

    execute(
        geo,
        {
            "op": "create_point",
            "name": "B",
            "x": 3,
            "y": 4,
        },
    )

    result = execute(
        geo,
        {
            "op": "distance",
            "a": "A",
            "b": "B",
        },
    )

    assert result["ok"] is True
    assert result["result"] == 5.0


def test_protocol_preserves_geometry_state():
    geo = GeometryState()

    execute(
        geo,
        {
            "op": "create_point",
            "name": "A",
            "x": 0,
            "y": 0,
        },
    )

    execute(
        geo,
        {
            "op": "create_point",
            "name": "B",
            "x": 1,
            "y": 0,
        },
    )

    snapshot = execute(
        geo,
        {
            "op": "snapshot",
        },
    )

    assert snapshot["ok"] is True
    assert "A" in snapshot["result"]["points"]
    assert "B" in snapshot["result"]["points"]


def test_protocol_rejects_unknown_operation():
    geo = GeometryState()

    result = execute(
        geo,
        {
            "op": "solve_everything",
        },
    )

    assert result["ok"] is False
