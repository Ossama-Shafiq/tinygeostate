# TinyGeoState Experiment Log

This document records experiments, failures, methodological changes, and decisions in chronological order.

Its purpose is to preserve the experimental history of TinyGeoState, including unsuccessful runs and discovered confounds.

Results should not be silently replaced when infrastructure or benchmarks are changed.

---

# 1. Geometry Engine Smoke Tests

Implemented a minimal persistent geometry engine containing:

- `Point`
- `Line`
- `GeometryState`

Initial primitive operations:

- distance
- orientation
- collinearity
- angle
- parallel
- perpendicular

The initial geometry test suite passed.

A command-line interface was also used to manually verify that objects persist across successive operations.

Example world:

```text
A = (0,0)
B = (4,0)
C = (0,3)

AB
AC
```

Correctly produced:

```text
AB = 4
AC = 3
angle BAC = 90 degrees
AB perpendicular AC = true
```

---

# 2. Structured Geometry Protocol

Added a structured protocol layer for executing geometry operations against `GeometryState`.

The protocol deliberately rejects arbitrary high-level operations such as:

```text
solve_everything
```

This is intentional.

TinyGeo should provide geometric primitives and state, not an automatic theorem solver.

---

# 3. Basic Text Baseline

A small coordinate-geometry benchmark was created to test the evaluation pipeline.

Qwen3-4B solved the benchmark at 100%.

Conclusion:

> The basic benchmark was useful as a smoke test but too easy for research evaluation.

---

# 4. Compositional v1

Created eight canonical geometry problems with seven representation variants each.

Variants included:

- original
- translation
- 90-degree rotation
- 180-degree rotation
- point renaming
- statement reordering
- combined transformations

Total:

```text
56 problems
```

The first text-only run appeared to contain failures.

Inspection showed that the failing generations had spent thousands of tokens reasoning but failed to emit the expected final-answer marker.

This exposed an **output-format confound**.

---

# 5. Structured Output and Thinking

The text baseline was changed to use structured JSON output.

An early test with Qwen3 thinking disabled produced a geometrically incorrect answer to a simple right-angle problem.

Thinking was therefore restored.

A generation budget of 1024 tokens was initially used.

This caused widespread apparent failures:

```text
8/56 correct
14.3% accuracy
```

Inspection showed that almost every failed record had:

```text
completion_tokens = 1024
raw_response = ""
```

The model had exhausted its reasoning budget before producing final content.

Conclusion:

> The 14.3% result was an infrastructure artifact and must not be treated as a geometry result.

---

# 6. Generation-Budget Diagnostics

A representative problem (`c003_original`) completed correctly with:

```text
1408 generated tokens
done_reason = stop
```

A harder example (`c005_original`) exhausted a 4096-token limit.

At an 8192-token limit it completed correctly after:

```text
6713 generated tokens
```

Decision:

```text
Qwen3-4B text baseline generation budget = 8192
```

The budget is fixed across comparable text-only runs rather than adapted per example.

---

# 7. Clean Compositional v1 Baseline

With thinking enabled and an 8192-token budget:

```text
Correct:                   56/56
Accuracy:                  100%
Fully valid bases:         8/8
Fully invariant bases:     8/8
Perfectly correct bases:   8/8
Truncated generations:     0
```

Conclusion:

> Compositional v1 is saturated and should be retained only as a regression/sanity benchmark.

---

# 8. Derived Geometry

TinyGeo was extended with:

- midpoint construction
- line intersection

This changed the geometry model from purely querying given coordinates to constructing new persistent objects.

Example dependency chain:

```text
initial points
    ↓
midpoint
    ↓
line
    ↓
intersection
    ↓
query derived object
```

This is more closely related to future CAD workflows.

---

# 9. Compositional v2

A second benchmark introduced:

- derived objects
- intersections
- midpoints
- distractors
- multiple predicates
- longer construction chains
- seven geometry-preserving variants

Initial text-only result:

```text
55/56
98.2%
```

The sole incorrect case was:

```text
d01b_combined
```

However, later inspection showed that the benchmark wording contained ambiguities introduced by multi-character renamed points.

For example:

```text
distance U3P7
```

was ambiguous.

Midpoint wording such as:

```text
midpoint of P7R9
```

was similarly ambiguous.

The original v2 benchmark is therefore retained historically but is not treated as the clean final version.

---

# 10. Persistent and Serialized Sessions

Two geometry-session conditions were implemented.

## Persistent state

`GeometryState` persists outside the LLM.

Objects created during earlier calls remain available by symbolic name.

## Serialized state

No geometry world persists inside the geometry session.

After each interaction, the complete world is serialized, carried through the language context, and reconstructed for the next call.

Both conditions use the same geometric primitives.

This distinction is intended to isolate **where geometric state lives** rather than whether one condition has stronger mathematics.

---

# 11. Autonomous Agent Failure

An initial free-form agent was asked to:

- read the complete geometry problem,
- plan the solution,
- choose among geometry tools,
- build the world,
- query predicates,
- produce the final answer.

Both persistent and serialized conditions exhausted large first-turn reasoning budgets before making any geometry call.

For example:

```text
4096 generated tokens
0 tool calls
```

A simple diagnostic confirmed that native Ollama tool calling itself worked correctly with Qwen3-4B.

Conclusion:

> The failure came from requiring the small model to plan the complete geometry problem before taking an obvious construction action.

The autonomous-agent experiment was therefore separated from the state-persistence experiment.

---

# 12. Phased Construction

The construction process was decomposed into one explicit instruction at a time.

Example:

```text
Create point M as the midpoint of points B and C.
```

The LLM was asked only to translate the instruction into a primitive geometry call.

For `m01a_original`, both conditions reconstructed the benchmark world exactly.

Persistent:

```text
prompt tokens:             4002
completion tokens:         3393
serialized state chars:    0
```

Serialized:

```text
prompt tokens:             4771
completion tokens:         3344
serialized state chars:    1245
```

Both final worlds matched ground truth.

This validated the state representation mechanism.

---

# 13. Query-Loop Confounds

Initial predicate verification required the model to perform sequences such as:

```text
distance(A,B)
distance(C,D)
remember both numbers
compare them
submit_truth(...)
```

This introduced unnecessary arithmetic and working-memory confounds.

TinyGeo was therefore extended with primitive relational queries:

- `distance_equal`
- `distance_less_than`
- `point_on_line`

These operations are treated as geometric primitives analogous to:

- parallel
- perpendicular
- collinear

They do not perform high-level theorem proving.

The redundant second `submit_truth` model turn was also removed.

An atomic predicate now follows:

```text
statement
    ↓
LLM selects primitive and object references
    ↓
TinyGeo returns primitive result
    ↓
predicate truth
```

---

# 14. Floating-Point State Comparison

Transformed geometries caused exact Python dictionary equality to report different states because of floating-point representation.

A tolerant state-equivalence function was introduced.

Object identities and topology must still match exactly.

Coordinates are compared numerically within tolerance.

This fixed false construction failures for transformed worlds.

---

# 15. Compositional v2.1

Benchmark wording was corrected to explicitly separate multi-character object names.

Example:

Old:

```text
distance U3P7 equals distance U3R9
```

New:

```text
the distance between points U3 and P7
equals the distance between points U3 and R9
```

Old:

```text
midpoint of P7R9
```

New:

```text
midpoint of points P7 and R9
```

The corrected benchmark was saved separately as:

```text
benchmarks/compositional_v2_1.jsonl
```

v2.1 is considered frozen.

---

# 16. v2.1 Phased Pilot

For `d01b_combined`, both conditions correctly reconstructed the geometry and verified every predicate.

Expected predicate results:

```text
True
True
True
False
```

Both persistent and serialized conditions produced the correct final answer:

```text
no
```

Persistent:

```text
query tool calls:          4
total prompt tokens:       6331
total completion tokens:   5387
serialized state chars:    0
```

Serialized:

```text
query tool calls:          4
total prompt tokens:       8123
total completion tokens:   5443
serialized state chars:    2740
```

Interpretation:

> This is a pilot observation only. Both conditions are correct. The serialized condition processes more state through the language context, but one example is insufficient to establish a general advantage.

---

# 17. Frozen v2.1 Text Baseline

Configuration:

```text
Model:               Qwen3-4B
Runtime:             Ollama
Temperature:         0
Thinking:            enabled
Generation budget:   8192
Tools:               none
Persistent state:    none
```

Results:

```text
Problems:                 56

Correct end-to-end:       55
End-to-end accuracy:      98.2%

Valid model answers:      55
Correct valid answers:    55
Valid-answer accuracy:    100%

Semantic answer errors:   0
Invalid/empty outputs:    1
Truncated generations:    0
```

The unsuccessful example was:

```text
t01a_combined
```

It produced:

```text
prediction = null
raw_response = ""
completion_tokens = 4978
done_reason = stop
truncated = false
```

This is classified as an **invalid-output failure**, not a demonstrated semantic geometry error.

The run should not be selectively repeated until the missing answer becomes correct.

---

# Current Status

v1:

```text
saturated
```

v2.1:

```text
near semantic ceiling
useful for validating infrastructure
```

Persistent and serialized phased pipelines:

```text
operational on pilot examples
```

Next experiment:

```text
Run the complete v2.1 phased benchmark
under persistent and serialized conditions.
```

After that:

```text
Design v3 around controlled geometric world-size
and construction-depth scaling.
```