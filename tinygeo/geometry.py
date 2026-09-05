from dataclasses import dataclass
from math import acos, degrees, hypot
from typing import Dict


EPS = 1e-9


@dataclass(frozen=True)
class Point:
    name: str
    x: float
    y: float


@dataclass(frozen=True)
class Line:
    name: str
    p1: str
    p2: str


class GeometryState:
    """
    A deliberately small persistent geometric world.

    It stores geometric objects and supports primitive
    geometric constructions and queries.

    It does NOT perform theorem proving, search, or
    automatic high-level reasoning.
    """

    def __init__(self):
        self.points: Dict[str, Point] = {}
        self.lines: Dict[str, Line] = {}

    # --------------------------------------------------
    # Object creation
    # --------------------------------------------------

    def create_point(
        self,
        name: str,
        x: float,
        y: float,
    ):
        if name in self.points:
            raise ValueError(
                f"Point {name} already exists."
            )

        self.points[name] = Point(
            name,
            float(x),
            float(y),
        )

        return {
            "status": "created",
            "type": "point",
            "name": name,
        }

    def create_line(
        self,
        name: str,
        p1: str,
        p2: str,
    ):
        self._require_point(p1)
        self._require_point(p2)

        if p1 == p2:
            raise ValueError(
                "A line requires two different points."
            )

        if name in self.lines:
            raise ValueError(
                f"Line {name} already exists."
            )

        self.lines[name] = Line(
            name,
            p1,
            p2,
        )

        return {
            "status": "created",
            "type": "line",
            "name": name,
            "through": [p1, p2],
        }

    # --------------------------------------------------
    # Derived geometric constructions
    # --------------------------------------------------

    def create_midpoint(
        self,
        name: str,
        a: str,
        b: str,
    ):
        """
        Create a new point at the midpoint of points A and B.
        """

        p = self._require_point(a)
        q = self._require_point(b)

        x = (p.x + q.x) / 2
        y = (p.y + q.y) / 2

        return self.create_point(
            name,
            x,
            y,
        )

    def create_intersection(
        self,
        name: str,
        line1: str,
        line2: str,
    ):
        """
        Create a new point at the intersection of two
        infinite 2D lines.

        Parallel or coincident lines are rejected.
        """

        l1 = self._require_line(line1)
        l2 = self._require_line(line2)

        p1 = self.points[l1.p1]
        p2 = self.points[l1.p2]

        p3 = self.points[l2.p1]
        p4 = self.points[l2.p2]

        x1, y1 = p1.x, p1.y
        x2, y2 = p2.x, p2.y
        x3, y3 = p3.x, p3.y
        x4, y4 = p4.x, p4.y

        denominator = (
            (x1 - x2) * (y3 - y4)
            - (y1 - y2) * (x3 - x4)
        )

        if abs(denominator) < EPS:
            raise ValueError(
                "Lines are parallel or coincident."
            )

        determinant1 = (
            x1 * y2
            - y1 * x2
        )

        determinant2 = (
            x3 * y4
            - y3 * x4
        )

        x = (
            determinant1 * (x3 - x4)
            - (x1 - x2) * determinant2
        ) / denominator

        y = (
            determinant1 * (y3 - y4)
            - (y1 - y2) * determinant2
        ) / denominator

        return self.create_point(
            name,
            x,
            y,
        )

    # --------------------------------------------------
    # Primitive geometric queries
    # --------------------------------------------------

    def distance(
        self,
        a: str,
        b: str,
    ) -> float:
        p = self._require_point(a)
        q = self._require_point(b)

        return hypot(
            q.x - p.x,
            q.y - p.y,
        )

    def orientation(
        self,
        a: str,
        b: str,
        c: str,
    ) -> str:
        """
        Return the orientation of C relative to the
        directed line A -> B.
        """

        p = self._require_point(a)
        q = self._require_point(b)
        r = self._require_point(c)

        cross = (
            (q.x - p.x) * (r.y - p.y)
            - (q.y - p.y) * (r.x - p.x)
        )

        if abs(cross) < EPS:
            return "collinear"

        if cross > 0:
            return "counterclockwise"

        return "clockwise"

    def collinear(
        self,
        a: str,
        b: str,
        c: str,
    ) -> bool:
        return (
            self.orientation(a, b, c)
            == "collinear"
        )

    def angle(
        self,
        a: str,
        b: str,
        c: str,
    ) -> float:
        """
        Return angle ABC in degrees.

        Point B is the vertex.
        """

        pa = self._require_point(a)
        pb = self._require_point(b)
        pc = self._require_point(c)

        ba = (
            pa.x - pb.x,
            pa.y - pb.y,
        )

        bc = (
            pc.x - pb.x,
            pc.y - pb.y,
        )

        norm_ba = hypot(*ba)
        norm_bc = hypot(*bc)

        if norm_ba < EPS or norm_bc < EPS:
            raise ValueError(
                "Cannot calculate angle with coincident points."
            )

        dot = (
            ba[0] * bc[0]
            + ba[1] * bc[1]
        )

        cos_theta = (
            dot
            / (norm_ba * norm_bc)
        )

        # Floating point protection.
        cos_theta = max(
            -1.0,
            min(1.0, cos_theta),
        )

        return degrees(
            acos(cos_theta)
        )

    def parallel(
        self,
        line1: str,
        line2: str,
    ) -> bool:
        l1 = self._require_line(line1)
        l2 = self._require_line(line2)

        a = self.points[l1.p1]
        b = self.points[l1.p2]

        c = self.points[l2.p1]
        d = self.points[l2.p2]

        v1 = (
            b.x - a.x,
            b.y - a.y,
        )

        v2 = (
            d.x - c.x,
            d.y - c.y,
        )

        cross = (
            v1[0] * v2[1]
            - v1[1] * v2[0]
        )

        return abs(cross) < EPS

    def perpendicular(
        self,
        line1: str,
        line2: str,
    ) -> bool:
        l1 = self._require_line(line1)
        l2 = self._require_line(line2)

        a = self.points[l1.p1]
        b = self.points[l1.p2]

        c = self.points[l2.p1]
        d = self.points[l2.p2]

        v1 = (
            b.x - a.x,
            b.y - a.y,
        )

        v2 = (
            d.x - c.x,
            d.y - c.y,
        )

        dot = (
            v1[0] * v2[0]
            + v1[1] * v2[1]
        )

        return abs(dot) < EPS

    # --------------------------------------------------
    # Persistent state inspection
    # --------------------------------------------------

    def snapshot(self):
        """
        Return the current geometric world.
        """

        return {
            "points": {
                name: {
                    "x": point.x,
                    "y": point.y,
                }
                for name, point
                in self.points.items()
            },
            "lines": {
                name: {
                    "p1": line.p1,
                    "p2": line.p2,
                }
                for name, line
                in self.lines.items()
            },
        }

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------

    def _require_point(
        self,
        name: str,
    ) -> Point:
        if name not in self.points:
            raise KeyError(
                f"Unknown point: {name}"
            )

        return self.points[name]

    def _require_line(
        self,
        name: str,
    ) -> Line:
        if name not in self.lines:
            raise KeyError(
                f"Unknown line: {name}"
            )

        return self.lines[name]