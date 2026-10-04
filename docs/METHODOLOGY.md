# TinyGeoState Experimental Methodology

## Objective

TinyGeoState studies whether explicit persistent geometric state changes the reliability, invariance, and computational cost of language-model geometry reasoning.

The main causal variable is intended to be:

> whether geometric state persists externally or must repeatedly pass through the language-model token context.

---

# Experimental Conditions

## Text-only

The model receives a natural-language geometry problem.

It has:

```text
no TinyGeo tools
no external geometric state
```

The model performs the complete solution using its own token-based reasoning.

Text-only experiments primarily provide a reference baseline.

---

## Serialized-state geometry

The model can use TinyGeo's primitive geometric operations.

However, the geometry engine itself does not retain its world between interactions.

The complete state must be serialized and made available again for subsequent interactions.

Conceptually:

```text
LLM
 ↓
geometry operation
 ↓
temporary GeometryState
 ↓
serialize complete world
 ↓
token context
 ↓
reconstruct GeometryState
```

---

## Persistent-state geometry

The model receives the same primitive geometric capabilities.

However, the `GeometryState` instance persists externally.

Conceptually:

```text
LLM
 ↓
geometry operation
 ↓
persistent GeometryState
 ↓
symbolic references used on later calls
```

The complete world does not need to be repeatedly serialized through the model context.

---

# Fairness Constraint

Persistent and serialized conditions must expose the same mathematical capabilities.

A primitive added to one condition must also be available to the other.

Examples include:

```text
create_point
create_line
create_midpoint
create_intersection

distance
distance_equal
distance_less_than
orientation
collinear
point_on_line
parallel
perpendicular
angle
```

The persistent condition must not receive a hidden solver unavailable to the serialized condition.

---

# TinyGeo Capability Boundary

TinyGeo may perform deterministic primitive geometry calculations.

TinyGeo may:

```text
store geometric objects
create deterministic derived objects
calculate primitive relations
return numerical or Boolean geometric properties
```

TinyGeo must not:

```text
plan a solution
select relevant predicates automatically
perform theorem search
generate proofs
decide an entire benchmark problem
infer the user's intent
```

The language model remains responsible for selecting operations and referring to the correct objects.

---

# Phased Protocol

The current controlled experiment uses two phases.

## Construction phase

Explicit natural-language construction instructions are translated into geometry calls.

The benchmark harness may expose one construction instruction at a time.

The harness does not expose hidden predicate truth values or final answers.

## Predicate phase

Each benchmark statement is presented independently.

The model selects one primitive geometry query corresponding to that statement.

The returned primitive result determines the predicate truth.

The final problem answer is:

```text
yes
```

only when all predicates evaluate to true.

Otherwise:

```text
no
```

This is referred to as the **phased protocol**.

It is not currently treated as a fully autonomous geometry agent.

---

# Model Configuration

Comparable runs should hold constant:

```text
model
temperature
thinking configuration
tool definitions
generation budget
benchmark
scoring procedure
```

Current local pilot configuration:

```text
Model:          Qwen3-4B
Runtime:        Ollama
Temperature:    0
Thinking:       enabled
```

The text-only generation budget is:

```text
8192 tokens
```

Per-step phased tool calls currently use a bounded step budget.

Any changes to these settings should be logged before interpreting new experimental results.

---

# Failure Categories

Failures should not all be collapsed into "wrong."

At minimum classify:

## Semantic error

The model returns a valid final answer, but the answer is incorrect.

## Invalid output

The model terminates without producing a parseable/valid required response.

## Truncation

The model reaches the configured generation limit before completing the required response.

## Tool-selection error

The model chooses an inappropriate primitive or malformed tool call.

## Tool execution error

The requested TinyGeo operation fails.

## Construction error

The resulting geometric world does not match the benchmark's intended world.

## Predicate error

A benchmark predicate is assigned the wrong truth value.

These categories should be recorded separately.

---

# State Equality

Geometric states should not be compared with exact floating-point equality.

State validation requires:

```text
same object identities
same topology
approximately equal numerical coordinates
```

A numerical tolerance should be used for coordinates.

---

# Invariance Evaluation

Geometry-preserving variants may include:

```text
translation
rotation
uniform scaling
object renaming
statement reordering
combinations of the above
```

An invariance group counts as successful only if all required outputs are valid.

A collection of `None` predictions must never be classified as invariant.

Representation invariance and semantic accuracy should be reported separately.

---

# Token and State Metrics

For phased persistent-vs-serialized experiments, record:

```text
prompt tokens
completion tokens
thinking characters or thinking tokens where available
tool-call count
tool-error count
serialized-state characters
peak serialized-state size
construction success
predicate success
final accuracy
invalid-output rate
truncation rate
```

Report both mean and median token measures when sample sizes permit.

Large outliers are expected in reasoning-model generation.

---

# Interpreting Token Cost

Text-only and phased tool experiments use different interaction protocols.

Therefore:

> raw token totals from text-only runs should not be directly interpreted as a fair efficiency comparison against phased runs.

The cleaner efficiency comparison is:

```text
serialized-state phased
vs
persistent-state phased
```

because these conditions share the same interaction protocol and primitive capabilities.

---

# Benchmark Development Rules

A benchmark should not be silently modified after results are observed.

If a benchmark defect is discovered:

1. preserve the original version;
2. document the defect;
3. create a new benchmark version;
4. rerun required baselines;
5. freeze the corrected version before the main experiment.

This procedure produced:

```text
compositional_v2.jsonl
```

and the corrected:

```text
compositional_v2_1.jsonl
```

---

# Repeated Runs

Do not selectively rerun only failed examples and replace their original outputs.

If stochastic/reliability analysis is required, rerun the complete experimental condition for a predefined number of repetitions.

Report distributions or aggregate rates across those repetitions.

---

# Current Scope

The present system investigates small 2D constructive geometry.

The intended research trajectory is:

```text
2D geometric state
        ↓
larger persistent object worlds
        ↓
CAD-style constructive geometry
        ↓
topological and semantic regions
        ↓
Gmsh geometry / meshing
        ↓
physics-aware region semantics
        ↓
Elmer FEM
```

Future CAD/CAE extensions may include:

```text
curves
surfaces
volumes
transformations
Boolean operations
constraints
named regions
material regions
boundary roles
mesh intent
physics intent
```

These extensions should preserve the central experimental principle:

> deterministic external geometry should provide state and primitive operations without silently becoming the reasoning system itself.