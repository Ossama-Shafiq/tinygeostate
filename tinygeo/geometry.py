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

    It stores geometric objects but does NOT perform
    theorem proving or automatic deduction.
    """

    def __init__(self):
        self.points: Dict[str, Point] = {}
        self.lines: Dict[str, Line] = {}

    # ---------- Object creation ----------

    def create_point(self, name: str, x: float, y: float):
        if name in self.points:
            raise ValueError(f"Point {name} already exists.")

        self.points[name] = Point(name, float(x), float(y))

        return {
            "status": "created",
            "type": "point",
            "name": name,
        }

    def create_line(self, name: str, p1: str, p2: str):
        self._require_point(p1)
        self._require_point(p2)

        if p1 == p2:
            raise ValueError("A line requires two different points.")

        if name in self.lines:
            raise ValueError(f"Line {name} already exists.")

        self.lines[name] = Line(name, p1, p2)

        return {
            "status": "created",
            "type": "line",
            "name": name,
            "through": [p1, p2],
        }

    # ---------- Primitive queries ----------

    def distance(self, a: str, b: str) -> float:
        p = self._require_point(a)
        q = self._require_point(b)

        return hypot(q.x - p.x, q.y - p.y)

    def orientation(self, a: str, b: str, c: str) -> str:
        """
        Returns whether C is left/right of directed segment AB.
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

        return "counterclockwise" if cross > 0 else "clockwise"

    def collinear(self, a: str, b: str, c: str) -> bool:
        return self.orientation(a, b, c) == "collinear"

    def angle(self, a: str, b: str, c: str) -> float:
        """
        Angle ABC in degrees.
        B is the vertex.
        """

        pa = self._require_point(a)
        pb = self._require_point(b)
        pc = self._require_point(c)

        ba = (pa.x - pb.x, pa.y - pb.y)
        bc = (pc.x - pb.x, pc.y - pb.y)

        norm_ba = hypot(*ba)
        norm_bc = hypot(*bc)

        if norm_ba < EPS or norm_bc < EPS:
            raise ValueError("Cannot calculate angle with coincident points.")

        dot = ba[0] * bc[0] + ba[1] * bc[1]

        cos_theta = dot / (norm_ba * norm_bc)

        # Protect against floating point errors.
        cos_theta = max(-1.0, min(1.0, cos_theta))

        return degrees(acos(cos_theta))

    def parallel(self, line1: str, line2: str) -> bool:
        l1 = self._require_line(line1)
        l2 = self._require_line(line2)

        a = self.points[l1.p1]
        b = self.points[l1.p2]
        c = self.points[l2.p1]
        d = self.points[l2.p2]

        v1 = (b.x - a.x, b.y - a.y)
        v2 = (d.x - c.x, d.y - c.y)

        cross = v1[0] * v2[1] - v1[1] * v2[0]

        return abs(cross) < EPS

    def perpendicular(self, line1: str, line2: str) -> bool:
        l1 = self._require_line(line1)
        l2 = self._require_line(line2)

        a = self.points[l1.p1]
        b = self.points[l1.p2]
        c = self.points[l2.p1]
        d = self.points[l2.p2]

        v1 = (b.x - a.x, b.y - a.y)
        v2 = (d.x - c.x, d.y - c.y)

        dot = v1[0] * v2[0] + v1[1] * v2[1]

        return abs(dot) < EPS

    # ---------- Persistent state ----------

    def snapshot(self):
        """
        Returns the current geometric world.
        """

        return {
            "points": {
                name: {
                    "x": point.x,
                    "y": point.y,
                }
                for name, point in self.points.items()
            },
            "lines": {
                name: {
                    "p1": line.p1,
                    "p2": line.p2,
                }
                for name, line in self.lines.items()
            },
        }

    # ---------- Helpers ----------

    def _require_point(self, name: str) -> Point:
        if name not in self.points:
            raise KeyError(f"Unknown point: {name}")

        return self.points[name]

    def _require_line(self, name: str) -> Line:
        if name not in self.lines:
            raise KeyError(f"Unknown line: {name}")

        return self.lines[name]
