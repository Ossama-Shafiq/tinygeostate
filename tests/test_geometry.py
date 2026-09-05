import pytest

from tinygeo.geometry import GeometryState


def test_distance():
    geo = GeometryState()

    geo.create_point("A", 0, 0)
    geo.create_point("B", 3, 4)

    assert geo.distance("A", "B") == pytest.approx(5.0)


def test_orientation():
    geo = GeometryState()

    geo.create_point("A", 0, 0)
    geo.create_point("B", 1, 0)
    geo.create_point("C", 0, 1)

    assert geo.orientation("A", "B", "C") == "counterclockwise"


def test_collinear():
    geo = GeometryState()

    geo.create_point("A", 0, 0)
    geo.create_point("B", 1, 1)
    geo.create_point("C", 2, 2)

    assert geo.collinear("A", "B", "C")


def test_right_angle():
    geo = GeometryState()

    geo.create_point("A", 1, 0)
    geo.create_point("B", 0, 0)
    geo.create_point("C", 0, 1)

    assert geo.angle("A", "B", "C") == pytest.approx(90.0)


def test_perpendicular_lines():
    geo = GeometryState()

    geo.create_point("A", 0, 0)
    geo.create_point("B", 1, 0)

    geo.create_point("C", 0, 0)
    geo.create_point("D", 0, 1)

    geo.create_line("L1", "A", "B")
    geo.create_line("L2", "C", "D")

    assert geo.perpendicular("L1", "L2")
