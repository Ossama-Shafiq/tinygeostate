import json
import math
import random
from pathlib import Path


OUTPUT_PATH = Path("benchmarks/compositional_v1.jsonl")
EPS = 1e-9


BASE_CASES = [
    {
        "id": "c001",
        "points": {
            "A": (0, 0),
            "B": (4, 0),
            "C": (0, 3),
            "D": (4, 3),
            "E": (2, 0),
        },
        "predicates": [
            ("perpendicular", "A", "B", "A", "C"),
            ("parallel", "A", "B", "C", "D"),
            ("collinear", "A", "E", "B"),
            ("distance_lt", "E", "A", "E", "C"),
        ],
    },
    {
        "id": "c002",
        "points": {
            "A": (0, 0),
            "B": (4, 0),
            "C": (0, 3),
            "D": (4, 3),
            "E": (2, 1),
        },
        "predicates": [
            ("perpendicular", "A", "B", "A", "C"),
            ("parallel", "A", "B", "C", "D"),
            ("collinear", "A", "E", "B"),
            ("distance_lt", "E", "A", "E", "C"),
        ],
    },
    {
        "id": "c003",
        "points": {
            "A": (0, 0),
            "B": (6, 0),
            "C": (3, 4),
            "D": (3, -2),
            "E": (3, 0),
        },
        "predicates": [
            ("orientation", "A", "B", "C", "counterclockwise"),
            ("orientation", "A", "B", "D", "clockwise"),
            ("collinear", "A", "E", "B"),
        ],
    },
    {
        "id": "c004",
        "points": {
            "A": (0, 0),
            "B": (6, 0),
            "C": (3, 4),
            "D": (3, 2),
            "E": (3, 0),
        },
        "predicates": [
            ("orientation", "A", "B", "C", "counterclockwise"),
            ("orientation", "A", "B", "D", "clockwise"),
            ("collinear", "A", "E", "B"),
        ],
    },
    {
        "id": "c005",
        "points": {
            "A": (0, 0),
            "B": (3, 4),
            "C": (-3, 4),
            "D": (0, 1),
            "E": (0, 5),
        },
        "predicates": [
            ("distance_eq", "A", "B", "A", "C"),
            ("perpendicular", "B", "C", "D", "E"),
            ("orientation", "B", "C", "A", "counterclockwise"),
        ],
    },
    {
        "id": "c006",
        "points": {
            "A": (0, 0),
            "B": (3, 4),
            "C": (-3, 4),
            "D": (0, 1),
            "E": (1, 5),
        },
        "predicates": [
            ("distance_eq", "A", "B", "A", "C"),
            ("perpendicular", "B", "C", "D", "E"),
            ("orientation", "B", "C", "A", "counterclockwise"),
        ],
    },
    {
        "id": "c007",
        "points": {
            "A": (0, 0),
            "B": (4, 0),
            "C": (4, 3),
            "D": (0, 3),
            "E": (2, 1.5),
        },
        "predicates": [
            ("parallel", "A", "B", "D", "C"),
            ("perpendicular", "B", "C", "C", "D"),
            ("distance_eq", "E", "A", "E", "C"),
        ],
    },
    {
        "id": "c008",
        "points": {
            "A": (0, 0),
            "B": (4, 0),
            "C": (4, 3),
            "D": (0, 3),
            "E": (1, 1),
        },
        "predicates": [
            ("parallel", "A", "B", "D", "C"),
            ("perpendicular", "B", "C", "C", "D"),
            ("distance_eq", "E", "A", "E", "C"),
        ],
    },
]


def point(points, name):
    return points[name]


def vector(p, q):
    return q[0] - p[0], q[1] - p[1]


def cross(v1, v2):
    return v1[0] * v2[1] - v1[1] * v2[0]


def dot(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1]


def distance(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def evaluate_predicate(points, predicate):
    kind = predicate[0]

    if kind == "parallel":
        _, a, b, c, d = predicate

        v1 = vector(point(points, a), point(points, b))
        v2 = vector(point(points, c), point(points, d))

        return abs(cross(v1, v2)) < EPS

    if kind == "perpendicular":
        _, a, b, c, d = predicate

        v1 = vector(point(points, a), point(points, b))
        v2 = vector(point(points, c), point(points, d))

        return abs(dot(v1, v2)) < EPS

    if kind == "collinear":
        _, a, b, c = predicate

        v1 = vector(point(points, a), point(points, b))
        v2 = vector(point(points, a), point(points, c))

        return abs(cross(v1, v2)) < EPS

    if kind == "orientation":
        _, a, b, c, expected = predicate

        v1 = vector(point(points, a), point(points, b))
        v2 = vector(point(points, a), point(points, c))

        value = cross(v1, v2)

        if abs(value) < EPS:
            actual = "collinear"
        elif value > 0:
            actual = "counterclockwise"
        else:
            actual = "clockwise"

        return actual == expected

    if kind == "distance_eq":
        _, a, b, c, d = predicate

        d1 = distance(point(points, a), point(points, b))
        d2 = distance(point(points, c), point(points, d))

        return math.isclose(d1, d2, abs_tol=EPS)

    if kind == "distance_lt":
        _, a, b, c, d = predicate

        d1 = distance(point(points, a), point(points, b))
        d2 = distance(point(points, c), point(points, d))

        return d1 < d2

    raise ValueError(f"Unknown predicate: {kind}")


def evaluate_case(points, predicates):
    return all(
        evaluate_predicate(points, predicate)
        for predicate in predicates
    )


def describe_predicate(predicate):
    kind = predicate[0]

    if kind == "parallel":
        _, a, b, c, d = predicate
        return f"the line through {a} and {b} is parallel to the line through {c} and {d}"

    if kind == "perpendicular":
        _, a, b, c, d = predicate
        return f"the line through {a} and {b} is perpendicular to the line through {c} and {d}"

    if kind == "collinear":
        _, a, b, c = predicate
        return f"{a}, {b}, and {c} are collinear"

    if kind == "orientation":
        _, a, b, c, expected = predicate
        return (
            f"{c} is {expected} relative to the directed line "
            f"from {a} to {b}"
        )

    if kind == "distance_eq":
        _, a, b, c, d = predicate
        return f"distance {a}{b} equals distance {c}{d}"

    if kind == "distance_lt":
        _, a, b, c, d = predicate
        return f"distance {a}{b} is less than distance {c}{d}"

    raise ValueError(kind)


def format_number(value):
    if abs(value) < EPS:
        value = 0

    if float(value).is_integer():
        return str(int(value))

    return f"{value:.4f}".rstrip("0").rstrip(".")


def build_prompt(
    points,
    predicates,
    point_order=None,
    predicate_order=None,
):
    if point_order is None:
        point_order = list(points)

    if predicate_order is None:
        predicate_order = list(range(len(predicates)))

    coordinate_text = ", ".join(
        (
            f"{name}=("
            f"{format_number(points[name][0])},"
            f"{format_number(points[name][1])})"
        )
        for name in point_order
    )

    statements = [
        describe_predicate(predicates[index])
        for index in predicate_order
    ]

    statement_text = "; ".join(
        f"({index + 1}) {statement}"
        for index, statement in enumerate(statements)
    )

    return (
        f"Given {coordinate_text}. "
        f"Are all of the following statements true? "
        f"{statement_text}. "
        f"Answer yes or no."
    )


def transform_points(points, transform):
    return {
        name: transform(x, y)
        for name, (x, y) in points.items()
    }


def rename_predicate(predicate, mapping):
    kind = predicate[0]

    if kind in {"parallel", "perpendicular", "distance_eq", "distance_lt"}:
        _, a, b, c, d = predicate
        return (
            kind,
            mapping[a],
            mapping[b],
            mapping[c],
            mapping[d],
        )

    if kind == "collinear":
        _, a, b, c = predicate
        return (
            kind,
            mapping[a],
            mapping[b],
            mapping[c],
        )

    if kind == "orientation":
        _, a, b, c, expected = predicate
        return (
            kind,
            mapping[a],
            mapping[b],
            mapping[c],
            expected,
        )

    raise ValueError(kind)


def rename_case(points, predicates):
    names = list(points)

    replacements = [
        "P7",
        "Q2",
        "R9",
        "S4",
        "T8",
        "U3",
        "V6",
    ]

    mapping = {
        old: new
        for old, new in zip(names, replacements)
    }

    renamed_points = {
        mapping[name]: coords
        for name, coords in points.items()
    }

    renamed_predicates = [
        rename_predicate(predicate, mapping)
        for predicate in predicates
    ]

    return renamed_points, renamed_predicates


def make_record(
    base_case,
    variant,
    transform,
    rename=False,
    reorder=False,
):
    points = transform_points(
        base_case["points"],
        transform,
    )

    predicates = list(base_case["predicates"])

    if rename:
        points, predicates = rename_case(
            points,
            predicates,
        )

    point_order = list(points)
    predicate_order = list(range(len(predicates)))

    if reorder:
        seed = f"{base_case['id']}:{variant}"

        rng = random.Random(seed)

        rng.shuffle(point_order)
        rng.shuffle(predicate_order)

    answer = "yes" if evaluate_case(points, predicates) else "no"

    prompt = build_prompt(
        points,
        predicates,
        point_order=point_order,
        predicate_order=predicate_order,
    )

    return {
        "id": f"{base_case['id']}_{variant}",
        "base_id": base_case["id"],
        "variant": variant,
        "prompt": prompt,
        "answer": answer,
        "world": {
            "points": {
                name: [x, y]
                for name, (x, y) in points.items()
            }
        },
        "predicates": [
            list(predicate)
            for predicate in predicates
        ],
    }


def main():
    variants = [
        (
            "original",
            lambda x, y: (x, y),
            False,
            False,
        ),
        (
            "translated",
            lambda x, y: (x + 17, y - 11),
            False,
            False,
        ),
        (
            "rotated90",
            lambda x, y: (-y, x),
            False,
            False,
        ),
        (
            "rotated180",
            lambda x, y: (-x, -y),
            False,
            False,
        ),
        (
            "renamed",
            lambda x, y: (x, y),
            True,
            False,
        ),
        (
            "reordered",
            lambda x, y: (x, y),
            False,
            True,
        ),
        (
            "combined",
            lambda x, y: (-y + 17, x - 11),
            True,
            True,
        ),
    ]

    records = []

    for base_case in BASE_CASES:
        canonical_answer = (
            "yes"
            if evaluate_case(
                base_case["points"],
                base_case["predicates"],
            )
            else "no"
        )

        for (
            variant,
            transform,
            rename,
            reorder,
        ) in variants:

            record = make_record(
                base_case,
                variant,
                transform,
                rename=rename,
                reorder=reorder,
            )

            # Every transformation used in v1 should preserve
            # the mathematical truth value.
            assert record["answer"] == canonical_answer

            records.append(record)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:

        for record in records:
            f.write(json.dumps(record) + "\n")

    yes_count = sum(
        record["answer"] == "yes"
        for record in records
    )

    no_count = len(records) - yes_count

    print(f"Wrote {len(records)} problems.")
    print(f"YES: {yes_count}")
    print(f"NO:  {no_count}")
    print(f"Path: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
