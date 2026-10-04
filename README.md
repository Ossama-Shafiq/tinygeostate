# TinyGeoState

TinyGeoState is a research prototype for studying whether large language models reason about geometry more reliably and efficiently when geometric state is represented explicitly outside the token stream.

The long-term goal is to investigate architectures for reliable LLM-driven CAD and engineering simulation, with a path toward:

**natural language → structured geometric state → Gmsh → FEM/physics solver**

The current project deliberately begins with small 2D constructive geometry so that the effect of geometric state representation can be isolated and measured cleanly.

## Research Question

The central question is:

> Does persistent structured geometric state improve LLM geometric reasoning, representation invariance, and computational efficiency compared with carrying the same geometric state through tokens?

A key experimental comparison is:

### Text-only

The LLM receives the entire geometry problem in text and solves it without geometry tools.

### Serialized state

The LLM uses geometric primitives, but the complete geometric world is serialized and passed back through the language-model context.

The geometry engine itself does not retain the world between interactions.

### Persistent state

The LLM uses the same geometric primitives, but the geometric world persists externally in `GeometryState`.

The model refers to persistent objects by symbolic identity rather than repeatedly receiving the complete world through tokens.

The goal is to keep the mathematical capabilities of the serialized and persistent conditions identical so that **state persistence itself** is the main experimental variable.

## Current Geometry Engine

TinyGeo currently supports persistent 2D objects:

- points
- lines

Constructive operations include:

- explicit point creation
- line creation
- midpoint construction
- line intersection

Primitive geometric queries include:

- distance
- distance equality
- distance comparison
- angle
- orientation
- collinearity
- point-on-line
- parallelism
- perpendicularity

TinyGeo is intentionally weak.

It does **not** currently perform:

- theorem proving
- automatic proof search
- task planning
- high-level geometry solving
- automatic CAD design

The language model must still decide which primitive operation to use and which geometric objects are relevant.

## Current Experimental Architecture

The current phased experiment separates geometry into two stages.

### Phase 1 — construction

Natural-language construction instructions are translated by the LLM into primitive geometry calls.

Example:

```text
Construct point M as the midpoint of points B and C.
```

becomes a call equivalent to:

```json
{
  "op": "create_midpoint",
  "name": "M",
  "a": "B",
  "b": "C"
}
```

### Phase 2 — predicate verification

The constructed world is queried using atomic geometric relations.

Example:

```text
the distance between points A and B
equals the distance between points C and D
```

can be checked using:

```text
distance_equal(A, B, C, D)
```

The geometry engine returns the primitive result, while the model remains responsible for selecting the correct operation and object references.

## Benchmarks

### `basic.jsonl`

Small coordinate-geometry smoke tests.

Used primarily to validate the evaluation pipeline.

### `compositional_v1.jsonl`

Eight canonical problems with seven geometry-preserving variants each:

- original
- translated
- rotated
- renamed
- reordered
- combined transformations

Total:

```text
56 problems
```

Qwen3-4B reached 100% accuracy after generation-budget confounds were removed.

This benchmark is considered saturated and retained as a regression/sanity benchmark.

### `compositional_v2_1.jsonl`

Constructive geometry benchmark containing:

- derived points
- midpoints
- intersections
- named lines
- distractor geometry
- multiple predicates
- geometry-preserving transformations

Total:

```text
56 problems
28 yes
28 no
```

The benchmark wording was revised to remove ambiguity when multi-character point names are used.

For example:

```text
distance U3P7
```

was replaced by the unambiguous:

```text
the distance between points U3 and P7
```

The v2.1 benchmark is now frozen.

## Current Text-Only Baseline

Model:

```text
Qwen3-4B
Ollama
temperature = 0
thinking = enabled
generation budget = 8192 tokens
```

On `compositional_v2_1.jsonl`:

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

The single unsuccessful case produced no final structured answer despite terminating normally. It was therefore an output-validity failure rather than a demonstrated incorrect geometry answer.

v2.1 is effectively near ceiling for Qwen3-4B and is not intended to be the final research benchmark.

## Initial Persistent vs Serialized Pilot

Both state conditions have successfully reconstructed identical geometric worlds and solved controlled predicate-verification examples.

In one transformed v2.1 pilot (`d01b_combined`):

| Metric | Persistent state | Serialized state |
| --- | ---: | ---: |
| Final answer | correct | correct |
| Geometry queries | 4 | 4 |
| Total prompt tokens | 6,331 | 8,123 |
| Total completion tokens | 5,387 | 5,443 |
| Serialized state characters | 0 | 2,740 |

This is a pilot observation only and is **not yet evidence of a general performance advantage**.

The important result is that the experimental machinery now provides equivalent geometric capabilities while allowing state-representation cost to be measured separately.

## Planned Experiments

The next stages are:

1. Run the complete v2.1 phased benchmark under both persistent and serialized conditions.
2. Measure correctness, validity, token usage, tool errors, and serialized-state growth.
3. Build a larger **v3 world-size scaling benchmark**.
4. Vary geometric world size and construction depth systematically.
5. Test multiple open model sizes.
6. Move toward CAD-style constructive geometry.
7. Introduce a simulation-aware geometric representation.
8. Compile structured geometry into Gmsh.
9. Preserve named physical regions and boundary identities for FEM solvers such as Elmer.

The main v3 hypothesis will concern scaling:

> As geometric worlds become larger, repeatedly serializing geometric state through language-model tokens may impose increasing context, reasoning, and reliability costs compared with persistent external geometric state.

## Repository Structure

```text
tinygeostate/
├── tinygeo/
│   ├── geometry.py
│   ├── protocol.py
│   ├── session.py
│   ├── state_utils.py
│   ├── agent.py
│   └── models/
│
├── benchmarks/
│   ├── basic.jsonl
│   ├── compositional_v1.jsonl
│   ├── compositional_v2_1.jsonl
│   └── benchmark generators
│
├── experiments/
│   ├── text baseline runners
│   ├── invariance analysis
│   ├── phased construction diagnostics
│   └── phased reasoning diagnostics
│
├── tests/
├── results/
├── docs/
│   ├── EXPERIMENT_LOG.md
│   └── METHODOLOGY.md
│
└── README.md
```

## Setup

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the tests:

```bash
python -m pytest -v
```

Local model experiments currently use Ollama with:

```text
qwen3:4b
```

## Research Status

TinyGeoState is currently an experimental research prototype.

Results should not yet be interpreted as demonstrating that persistent geometric state improves model accuracy.

The present repository establishes the controlled infrastructure required to test that hypothesis rigorously.