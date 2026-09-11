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

    assert (
        "A"
        in snapshot["result"]["points"]
    )

    assert (
        "B"
        in snapshot["result"]["points"]
    )


def test_protocol_rejects_unknown_operation():
    geo = GeometryState()

    result = execute(
        geo,
        {
            "op": "solve_everything",
        },
    )

    assert result["ok"] is False


def test_protocol_creates_midpoint():
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
            "x": 6,
            "y": 4,
        },
    )

    result = execute(
        geo,
        {
            "op": "create_midpoint",
            "name": "M",
            "a": "A",
            "b": "B",
        },
    )

    assert result["ok"] is True

    assert (
        geo.points["M"].x
        == 3
    )

    assert (
        geo.points["M"].y
        == 2
    )


def test_protocol_creates_intersection():
    geo = GeometryState()

    for name, x, y in [
        ("A", 0, 0),
        ("B", 4, 4),
        ("C", 0, 4),
        ("D", 4, 0),
    ]:
        execute(
            geo,
            {
                "op": "create_point",
                "name": name,
                "x": x,
                "y": y,
            },
        )

    execute(
        geo,
        {
            "op": "create_line",
            "name": "L1",
            "p1": "A",
            "p2": "B",
        },
    )

    execute(
        geo,
        {
            "op": "create_line",
            "name": "L2",
            "p1": "C",
            "p2": "D",
        },
    )

    result = execute(
        geo,
        {
            "op": "create_intersection",
            "name": "X",
            "line1": "L1",
            "line2": "L2",
        },
    )

    assert result["ok"] is True

    assert (
        geo.points["X"].x
        == 2
    )

    assert (
        geo.points["X"].y
        == 2
    )

def test_protocol_point_on_line():
    geo = GeometryState()

    for name, x, y in [
        ("A", 0, 0),
        ("B", 4, 4),
        ("X", 2, 2),
    ]:
        execute(
            geo,
            {
                "op": "create_point",
                "name": name,
                "x": x,
                "y": y,
            },
        )

    execute(
        geo,
        {
            "op": "create_line",
            "name": "L1",
            "p1": "A",
            "p2": "B",
        },
    )

    result = execute(
        geo,
        {
            "op": "point_on_line",
            "point": "X",
            "line": "L1",
        },
    )

    assert result["ok"] is True
    assert result["result"] is True

def test_protocol_distance_equal():
    geo = GeometryState()

    for name, x, y in [
        ("A", 0, 0),
        ("B", 3, 4),
        ("C", 10, 0),
        ("D", 13, 4),
    ]:
        execute(
            geo,
            {
                "op": "create_point",
                "name": name,
                "x": x,
                "y": y,
            },
        )

    result = execute(
        geo,
        {
            "op": "distance_equal",
            "a": "A",
            "b": "B",
            "c": "C",
            "d": "D",
        },
    )

    assert result["ok"] is True
    assert result["result"] is True


def test_protocol_distance_less_than():
    geo = GeometryState()

    for name, x, y in [
        ("A", 0, 0),
        ("B", 1, 0),
        ("C", 0, 0),
        ("D", 4, 0),
    ]:
        execute(
            geo,
            {
                "op": "create_point",
                "name": name,
                "x": x,
                "y": y,
            },
        )

    result = execute(
        geo,
        {
            "op": "distance_less_than",
            "a": "A",
            "b": "B",
            "c": "C",
            "d": "D",
        },
    )

    assert result["ok"] is True
    assert result["result"] is True