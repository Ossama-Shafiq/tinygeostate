import json
import math
import random
from copy import deepcopy
from pathlib import Path

from tinygeo.geometry import GeometryState


OUTPUT_PATH = Path(
    "benchmarks/compositional_v2.jsonl"
)

POINT_LABELS = [
    "P7",
    "Q2",
    "R9",
    "S4",
    "T8",
    "U3",
    "V6",
    "W1",
]

LINE_LABELS = [
    "K7",
    "J2",
    "H9",
    "G4",
    "F8",
    "E3",
    "D6",
    "C1",
]


def make_cases():
    """
    Create 8 canonical cases:

    4 geometries where every final statement is true.
    4 paired geometries where one final statement is false.

    This gives us a balanced YES/NO benchmark.
    """

    cases = []

    def add_pair(
        prefix,
        points,
        operations,
        common_predicates,
        true_predicate,
        false_predicate,
    ):
        cases.append(
            {
                "id": f"{prefix}a",
                "points": deepcopy(points),
                "operations": deepcopy(operations),
                "predicates": deepcopy(
                    common_predicates
                    + [true_predicate]
                ),
            }
        )

        cases.append(
            {
                "id": f"{prefix}b",
                "points": deepcopy(points),
                "operations": deepcopy(operations),
                "predicates": deepcopy(
                    common_predicates
                    + [false_predicate]
                ),
            }
        )

    # --------------------------------------------------
    # CASE PAIR 1
    #
    # Triangle medians.
    #
    # M = midpoint of BC
    # N = midpoint of AC
    #
    # L1 = A--M
    # L2 = B--N
    #
    # X = intersection of the two medians.
    # --------------------------------------------------

    points = {
        "A": (0, 0),
        "B": (9, 0),
        "C": (0, 6),

        # Distractor point.
        "E": (11, -2),
    }

    operations = [
        {
            "op": "midpoint",
            "name": "M",
            "a": "B",
            "b": "C",
        },
        {
            "op": "midpoint",
            "name": "N",
            "a": "A",
            "b": "C",
        },
        {
            "op": "line",
            "name": "L1",
            "p1": "A",
            "p2": "M",
        },
        {
            "op": "line",
            "name": "L2",
            "p1": "B",
            "p2": "N",
        },
        {
            "op": "intersection",
            "name": "X",
            "line1": "L1",
            "line2": "L2",
        },

        # Distractor construction.
        {
            "op": "line",
            "name": "LD",
            "p1": "A",
            "p2": "E",
        },
    ]

    common = [
        {
            "kind": "point_on_line",
            "points": ["X"],
            "lines": ["L1"],
        },
        {
            "kind": "point_on_line",
            "points": ["X"],
            "lines": ["L2"],
        },
        {
            "kind": "orientation",
            "points": ["A", "B", "X"],
            "expected": "counterclockwise",
        },
    ]

    add_pair(
        prefix="m01",
        points=points,
        operations=operations,
        common_predicates=common,

        true_predicate={
            "kind": "distance_lt",
            "points": ["X", "M", "A", "X"],
        },

        false_predicate={
            "kind": "distance_eq",
            "points": ["A", "X", "X", "M"],
        },
    )

    # --------------------------------------------------
    # CASE PAIR 2
    #
    # Rectangle diagonals.
    #
    # X = diagonal intersection.
    # M/N = midpoints of opposite sides.
    # L3 = midpoint line.
    # --------------------------------------------------

    points = {
        "A": (0, 0),
        "B": (8, 0),
        "C": (8, 6),
        "D": (0, 6),

        # Distractor point.
        "E": (11, 1),
    }

    operations = [
        {
            "op": "line",
            "name": "L1",
            "p1": "A",
            "p2": "C",
        },
        {
            "op": "line",
            "name": "L2",
            "p1": "B",
            "p2": "D",
        },
        {
            "op": "intersection",
            "name": "X",
            "line1": "L1",
            "line2": "L2",
        },
        {
            "op": "midpoint",
            "name": "M",
            "a": "A",
            "b": "B",
        },
        {
            "op": "midpoint",
            "name": "N",
            "a": "C",
            "b": "D",
        },
        {
            "op": "line",
            "name": "L3",
            "p1": "M",
            "p2": "N",
        },
        {
            "op": "line",
            "name": "L4",
            "p1": "A",
            "p2": "B",
        },

        # Distractor.
        {
            "op": "line",
            "name": "LD",
            "p1": "A",
            "p2": "E",
        },
    ]

    common = [
        {
            "kind": "point_on_line",
            "points": ["X"],
            "lines": ["L1"],
        },
        {
            "kind": "collinear",
            "points": ["M", "X", "N"],
        },
        {
            "kind": "line_perpendicular",
            "lines": ["L3", "L4"],
        },
    ]

    add_pair(
        prefix="r01",
        points=points,
        operations=operations,
        common_predicates=common,

        true_predicate={
            "kind": "distance_eq",
            "points": ["X", "A", "X", "C"],
        },

        false_predicate={
            "kind": "distance_eq",
            "points": ["X", "M", "X", "A"],
        },
    )

    # --------------------------------------------------
    # CASE PAIR 3
    #
    # Diamond / rhombus.
    #
    # Diagonals intersect at X.
    # --------------------------------------------------

    points = {
        "A": (-4, 0),
        "B": (0, 3),
        "C": (4, 0),
        "D": (0, -3),

        # Distractor.
        "E": (7, 5),
    }

    operations = [
        {
            "op": "line",
            "name": "L1",
            "p1": "A",
            "p2": "C",
        },
        {
            "op": "line",
            "name": "L2",
            "p1": "B",
            "p2": "D",
        },
        {
            "op": "intersection",
            "name": "X",
            "line1": "L1",
            "line2": "L2",
        },
        {
            "op": "midpoint",
            "name": "M",
            "a": "A",
            "b": "C",
        },

        # Distractor.
        {
            "op": "line",
            "name": "LD",
            "p1": "A",
            "p2": "E",
        },
    ]

    common = [
        {
            "kind": "line_perpendicular",
            "lines": ["L1", "L2"],
        },
        {
            "kind": "distance_eq",
            "points": ["X", "A", "X", "C"],
        },
        {
            "kind": "point_on_line",
            "points": ["M"],
            "lines": ["L2"],
        },
    ]

    add_pair(
        prefix="d01",
        points=points,
        operations=operations,
        common_predicates=common,

        true_predicate={
            "kind": "distance_eq",
            "points": ["X", "B", "X", "D"],
        },

        false_predicate={
            "kind": "distance_eq",
            "points": ["X", "A", "X", "B"],
        },
    )

    # --------------------------------------------------
    # CASE PAIR 4
    #
    # Trapezoid.
    #
    # M/N are side midpoints.
    # L1 is the midpoint line.
    # X is the intersection of the diagonals.
    # --------------------------------------------------

    points = {
        "A": (0, 0),
        "B": (10, 0),
        "C": (8, 6),
        "D": (2, 6),

        # Distractor.
        "E": (13, 2),
    }

    operations = [
        {
            "op": "midpoint",
            "name": "M",
            "a": "A",
            "b": "D",
        },
        {
            "op": "midpoint",
            "name": "N",
            "a": "B",
            "b": "C",
        },
        {
            "op": "line",
            "name": "L1",
            "p1": "M",
            "p2": "N",
        },
        {
            "op": "line",
            "name": "L2",
            "p1": "A",
            "p2": "B",
        },
        {
            "op": "line",
            "name": "L3",
            "p1": "C",
            "p2": "D",
        },
        {
            "op": "line",
            "name": "L4",
            "p1": "A",
            "p2": "C",
        },
        {
            "op": "line",
            "name": "L5",
            "p1": "B",
            "p2": "D",
        },
        {
            "op": "intersection",
            "name": "X",
            "line1": "L4",
            "line2": "L5",
        },

        # Distractor.
        {
            "op": "line",
            "name": "LD",
            "p1": "A",
            "p2": "E",
        },
    ]

    common = [
        {
            "kind": "line_parallel",
            "lines": ["L1", "L2"],
        },
        {
            "kind": "line_parallel",
            "lines": ["L1", "L3"],
        },
        {
            "kind": "distance_lt",
            "points": ["M", "N", "A", "B"],
        },
    ]

    add_pair(
        prefix="t01",
        points=points,
        operations=operations,
        common_predicates=common,

        true_predicate={
            "kind": "orientation",
            "points": ["M", "N", "X"],
            "expected": "counterclockwise",
        },

        false_predicate={
            "kind": "orientation",
            "points": ["M", "N", "X"],
            "expected": "clockwise",
        },
    )

    return cases


BASE_CASES = make_cases()


# --------------------------------------------------
# Execute hidden ground-truth geometry
# --------------------------------------------------

def build_state(
    points,
    operations,
):
    geo = GeometryState()

    for name, (x, y) in points.items():
        geo.create_point(
            name,
            x,
            y,
        )

    for operation in operations:
        op = operation["op"]

        if op == "midpoint":
            geo.create_midpoint(
                operation["name"],
                operation["a"],
                operation["b"],
            )

        elif op == "line":
            geo.create_line(
                operation["name"],
                operation["p1"],
                operation["p2"],
            )

        elif op == "intersection":
            geo.create_intersection(
                operation["name"],
                operation["line1"],
                operation["line2"],
            )

        else:
            raise ValueError(
                f"Unknown operation: {op}"
            )

    return geo


def evaluate_predicate(
    geo,
    predicate,
):
    kind = predicate["kind"]

    points = predicate.get(
        "points",
        [],
    )

    lines = predicate.get(
        "lines",
        [],
    )

    if kind == "line_parallel":
        return geo.parallel(
            lines[0],
            lines[1],
        )

    if kind == "line_perpendicular":
        return geo.perpendicular(
            lines[0],
            lines[1],
        )

    if kind == "point_on_line":
        line = geo.lines[
            lines[0]
        ]

        return geo.collinear(
            line.p1,
            line.p2,
            points[0],
        )

    if kind == "collinear":
        return geo.collinear(
            *points
        )

    if kind == "orientation":
        return (
            geo.orientation(
                *points
            )
            == predicate["expected"]
        )

    if kind == "distance_eq":
        return math.isclose(
            geo.distance(
                points[0],
                points[1],
            ),
            geo.distance(
                points[2],
                points[3],
            ),
            rel_tol=1e-8,
            abs_tol=1e-8,
        )

    if kind == "distance_lt":
        return (
            geo.distance(
                points[0],
                points[1],
            )
            <
            geo.distance(
                points[2],
                points[3],
            )
        )

    raise ValueError(
        f"Unknown predicate: {kind}"
    )


def evaluate_case(
    points,
    operations,
    predicates,
):
    geo = build_state(
        points,
        operations,
    )

    results = [
        evaluate_predicate(
            geo,
            predicate,
        )
        for predicate in predicates
    ]

    return (
        geo,
        results,
        all(results),
    )


# --------------------------------------------------
# Geometry-preserving transformations
# --------------------------------------------------

def rotate_345(
    x,
    y,
):
    """
    Rotation using:

        cos(theta) = 3/5
        sin(theta) = 4/5

    This is ~53.13 degrees.

    Unlike an arbitrary irrational rotation, this keeps
    the generated coordinates relatively clean.
    """

    return (
        (3 * x - 4 * y) / 5,
        (4 * x + 3 * y) / 5,
    )


def transform_points(
    points,
    transform,
):
    return {
        name: transform(
            x,
            y,
        )
        for name, (x, y)
        in points.items()
    }


# --------------------------------------------------
# Object renaming
# --------------------------------------------------

def rename_case(
    points,
    operations,
    predicates,
):
    derived_points = [
        operation["name"]
        for operation in operations
        if operation["op"]
        in {
            "midpoint",
            "intersection",
        }
    ]

    line_names = [
        operation["name"]
        for operation in operations
        if operation["op"] == "line"
    ]

    all_point_names = (
        list(points)
        + derived_points
    )

    if (
        len(all_point_names)
        > len(POINT_LABELS)
    ):
        raise ValueError(
            "Not enough point rename labels."
        )

    if (
        len(line_names)
        > len(LINE_LABELS)
    ):
        raise ValueError(
            "Not enough line rename labels."
        )

    point_map = dict(
        zip(
            all_point_names,
            POINT_LABELS,
        )
    )

    line_map = dict(
        zip(
            line_names,
            LINE_LABELS,
        )
    )

    renamed_points = {
        point_map[name]: coords
        for name, coords
        in points.items()
    }

    renamed_operations = []

    for operation in operations:
        op = operation["op"]

        if op == "midpoint":
            renamed_operations.append(
                {
                    "op": "midpoint",
                    "name": point_map[
                        operation["name"]
                    ],
                    "a": point_map[
                        operation["a"]
                    ],
                    "b": point_map[
                        operation["b"]
                    ],
                }
            )

        elif op == "line":
            renamed_operations.append(
                {
                    "op": "line",
                    "name": line_map[
                        operation["name"]
                    ],
                    "p1": point_map[
                        operation["p1"]
                    ],
                    "p2": point_map[
                        operation["p2"]
                    ],
                }
            )

        elif op == "intersection":
            renamed_operations.append(
                {
                    "op": "intersection",
                    "name": point_map[
                        operation["name"]
                    ],
                    "line1": line_map[
                        operation["line1"]
                    ],
                    "line2": line_map[
                        operation["line2"]
                    ],
                }
            )

    renamed_predicates = []

    for predicate in predicates:
        new_predicate = deepcopy(
            predicate
        )

        if "points" in new_predicate:
            new_predicate["points"] = [
                point_map[name]
                for name
                in new_predicate["points"]
            ]

        if "lines" in new_predicate:
            new_predicate["lines"] = [
                line_map[name]
                for name
                in new_predicate["lines"]
            ]

        renamed_predicates.append(
            new_predicate
        )

    return (
        renamed_points,
        renamed_operations,
        renamed_predicates,
    )


# --------------------------------------------------
# Natural-language generation
# --------------------------------------------------

def format_number(
    value,
):
    if abs(value) < 1e-10:
        value = 0.0

    if float(value).is_integer():
        return str(
            int(value)
        )

    return (
        f"{value:.4f}"
        .rstrip("0")
        .rstrip(".")
    )


def describe_operation(
    operation,
):
    op = operation["op"]

    if op == "midpoint":
        return (
            f"Construct point "
            f"{operation['name']} "
            f"as the midpoint of "
            f"{operation['a']}"
            f"{operation['b']}."
        )

    if op == "line":
        return (
            f"Construct line "
            f"{operation['name']} "
            f"through points "
            f"{operation['p1']} and "
            f"{operation['p2']}."
        )

    if op == "intersection":
        return (
            f"Construct point "
            f"{operation['name']} "
            f"as the intersection of "
            f"lines "
            f"{operation['line1']} and "
            f"{operation['line2']}."
        )

    raise ValueError(op)


def describe_predicate(
    predicate,
):
    kind = predicate["kind"]

    points = predicate.get(
        "points",
        [],
    )

    lines = predicate.get(
        "lines",
        [],
    )

    if kind == "line_parallel":
        return (
            f"line {lines[0]} "
            f"is parallel to "
            f"line {lines[1]}"
        )

    if kind == "line_perpendicular":
        return (
            f"line {lines[0]} "
            f"is perpendicular to "
            f"line {lines[1]}"
        )

    if kind == "point_on_line":
        return (
            f"point {points[0]} "
            f"lies on line {lines[0]}"
        )

    if kind == "collinear":
        return (
            f"points {points[0]}, "
            f"{points[1]}, and "
            f"{points[2]} "
            f"are collinear"
        )

    if kind == "orientation":
        return (
            f"point {points[2]} is "
            f"{predicate['expected']} "
            f"relative to the directed "
            f"line from {points[0]} "
            f"to {points[1]}"
        )

    if kind == "distance_eq":
        return (
            f"distance "
            f"{points[0]}{points[1]} "
            f"equals distance "
            f"{points[2]}{points[3]}"
        )

    if kind == "distance_lt":
        return (
            f"distance "
            f"{points[0]}{points[1]} "
            f"is less than distance "
            f"{points[2]}{points[3]}"
        )

    raise ValueError(kind)


def build_prompt(
    points,
    operations,
    predicates,
    point_order,
    predicate_order,
):
    coordinate_text = ", ".join(
        (
            f"{name}=("
            f"{format_number(points[name][0])},"
            f"{format_number(points[name][1])})"
        )
        for name in point_order
    )

    construction_text = " ".join(
        describe_operation(
            operation
        )
        for operation in operations
    )

    statement_text = "; ".join(
        (
            f"({number}) "
            f"{describe_predicate(predicates[index])}"
        )
        for number, index
        in enumerate(
            predicate_order,
            start=1,
        )
    )

    return (
        f"Start with {coordinate_text}. "
        f"{construction_text} "
        f"After carrying out all constructions, "
        f"are all of the following statements true? "
        f"{statement_text}. "
        f"Answer yes or no."
    )


# --------------------------------------------------
# Record generation
# --------------------------------------------------

def make_record(
    base,
    variant,
    transform,
    rename=False,
    reorder=False,
):
    points = transform_points(
        base["points"],
        transform,
    )

    operations = deepcopy(
        base["operations"]
    )

    predicates = deepcopy(
        base["predicates"]
    )

    if rename:
        (
            points,
            operations,
            predicates,
        ) = rename_case(
            points,
            operations,
            predicates,
        )

    point_order = list(
        points
    )

    predicate_order = list(
        range(
            len(predicates)
        )
    )

    if reorder:
        rng = random.Random(
            f"{base['id']}:{variant}"
        )

        rng.shuffle(
            point_order
        )

        rng.shuffle(
            predicate_order
        )

    (
        geo,
        predicate_results,
        value,
    ) = evaluate_case(
        points,
        operations,
        predicates,
    )

    return {
        "id": (
            f"{base['id']}_"
            f"{variant}"
        ),

        "base_id": base["id"],

        "variant": variant,

        "prompt": build_prompt(
            points,
            operations,
            predicates,
            point_order,
            predicate_order,
        ),

        "answer": (
            "yes"
            if value
            else "no"
        ),

        # Hidden ground truth.
        "initial_points": {
            name: [x, y]
            for name, (x, y)
            in points.items()
        },

        # Hidden construction program.
        "operations": operations,

        # Hidden predicates.
        "predicates": predicates,

        # Individual truth values.
        "predicate_results": (
            predicate_results
        ),

        # Full derived world after construction.
        "final_state": (
            geo.snapshot()
        ),
    }


def generate_records():
    variants = [
        (
            "original",
            lambda x, y: (
                x,
                y,
            ),
            False,
            False,
        ),

        (
            "translated",
            lambda x, y: (
                x + 17.5,
                y - 11.25,
            ),
            False,
            False,
        ),

        (
            "rotated53",
            lambda x, y: (
                rotate_345(
                    x,
                    y,
                )
            ),
            False,
            False,
        ),

        (
            "scaled",
            lambda x, y: (
                x * 3.5,
                y * 3.5,
            ),
            False,
            False,
        ),

        (
            "renamed",
            lambda x, y: (
                x,
                y,
            ),
            True,
            False,
        ),

        (
            "reordered",
            lambda x, y: (
                x,
                y,
            ),
            False,
            True,
        ),

        (
            "combined",
            lambda x, y: (
                rotate_345(
                    x,
                    y,
                )[0] + 17.5,

                rotate_345(
                    x,
                    y,
                )[1] - 11.25,
            ),
            True,
            True,
        ),
    ]

    records = []

    for base in BASE_CASES:
        (
            _,
            _,
            canonical_value,
        ) = evaluate_case(
            base["points"],
            base["operations"],
            base["predicates"],
        )

        canonical_answer = (
            "yes"
            if canonical_value
            else "no"
        )

        for (
            variant,
            transform,
            rename,
            reorder,
        ) in variants:

            record = make_record(
                base=base,
                variant=variant,
                transform=transform,
                rename=rename,
                reorder=reorder,
            )

            if (
                record["answer"]
                != canonical_answer
            ):
                raise AssertionError(
                    "Geometry-preserving "
                    "transformation changed "
                    f"answer for {record['id']}"
                )

            records.append(
                record
            )

    return records


def main():
    records = generate_records()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:

        for record in records:
            output_file.write(
                json.dumps(record)
                + "\n"
            )

    yes_count = sum(
        record["answer"] == "yes"
        for record in records
    )

    no_count = (
        len(records)
        - yes_count
    )

    print(
        f"Wrote {len(records)} problems."
    )

    print(
        f"YES: {yes_count}"
    )

    print(
        f"NO:  {no_count}"
    )

    print(
        f"Path: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
