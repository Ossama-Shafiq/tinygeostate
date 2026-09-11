from tinygeo.state_utils import (
    states_equivalent,
)


def test_states_equivalent_allows_small_float_error():
    actual = {
        "points": {
            "A": {
                "x": 1.0000001,
                "y": 2.0,
            }
        },
        "lines": {},
    }

    expected = {
        "points": {
            "A": {
                "x": 1.0,
                "y": 2.0,
            }
        },
        "lines": {},
    }

    assert states_equivalent(
        actual,
        expected,
    )


def test_states_equivalent_rejects_topology_change():
    actual = {
        "points": {
            "A": {
                "x": 0.0,
                "y": 0.0,
            },
            "B": {
                "x": 1.0,
                "y": 0.0,
            },
        },
        "lines": {
            "L": {
                "p1": "A",
                "p2": "B",
            }
        },
    }

    expected = {
        "points": {
            "A": {
                "x": 0.0,
                "y": 0.0,
            },
            "B": {
                "x": 1.0,
                "y": 0.0,
            },
        },
        "lines": {
            "L": {
                "p1": "B",
                "p2": "A",
            }
        },
    }

    assert not states_equivalent(
        actual,
        expected,
    )