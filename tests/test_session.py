from tinygeo.session import (
    EMPTY_STATE,
    PersistentGeometrySession,
    StatelessGeometrySession,
    restore_geometry_state,
)


def test_persistent_session_retains_state():
    session = PersistentGeometrySession()

    session.execute(
        {
            "op": "create_point",
            "name": "A",
            "x": 0,
            "y": 0,
        }
    )

    session.execute(
        {
            "op": "create_point",
            "name": "B",
            "x": 3,
            "y": 4,
        }
    )

    result = session.execute(
        {
            "op": "distance",
            "a": "A",
            "b": "B",
        }
    )

    assert result["ok"] is True
    assert result["result"] == 5.0


def test_stateless_session_requires_state_to_be_carried():
    session = StatelessGeometrySession()

    first = session.execute(
        {
            "op": "create_point",
            "name": "A",
            "x": 0,
            "y": 0,
        },
        state=EMPTY_STATE,
    )

    # Deliberately do NOT pass first["state"].
    second = session.execute(
        {
            "op": "create_point",
            "name": "B",
            "x": 3,
            "y": 4,
        },
        state=EMPTY_STATE,
    )

    assert "A" in first["state"]["points"]

    # Because this call started from empty state,
    # A has disappeared.
    assert "A" not in second["state"]["points"]
    assert "B" in second["state"]["points"]


def test_stateless_session_can_carry_state_explicitly():
    session = StatelessGeometrySession()

    first = session.execute(
        {
            "op": "create_point",
            "name": "A",
            "x": 0,
            "y": 0,
        },
        state=EMPTY_STATE,
    )

    second = session.execute(
        {
            "op": "create_point",
            "name": "B",
            "x": 3,
            "y": 4,
        },
        state=first["state"],
    )

    third = session.execute(
        {
            "op": "distance",
            "a": "A",
            "b": "B",
        },
        state=second["state"],
    )

    assert third["ok"] is True
    assert third["result"] == 5.0

    assert "A" in third["state"]["points"]
    assert "B" in third["state"]["points"]


def test_restore_geometry_state():
    snapshot = {
        "points": {
            "A": {
                "x": 0.0,
                "y": 0.0,
            },
            "B": {
                "x": 4.0,
                "y": 0.0,
            },
        },
        "lines": {
            "AB": {
                "p1": "A",
                "p2": "B",
            }
        },
    }

    geo = restore_geometry_state(
        snapshot
    )

    assert "A" in geo.points
    assert "B" in geo.points
    assert "AB" in geo.lines

    assert (
        geo.lines["AB"].p1
        == "A"
    )

    assert (
        geo.lines["AB"].p2
        == "B"
    )