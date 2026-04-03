# Plan: EAST3 optimizer expansion of `in` literals (P0-EAST3-IN-EXPAND)

## Background

Python's `x in (1, 2, 3)` and `x in [1, 2]` should be processed as `__contains__` on an iterable, but when the elements are a small number of literals, expanding to `x == 1 || x == 2 || x == 3` avoids the runtime cost of array construction + iteration.

This expansion is the responsibility of the **EAST3 optimizer** — the emitter must not make this decision by inspecting element counts (spec-emitter-guide §1.1).

## Design

### Target Pattern

A `Compare` node in EAST3 where:
- `ops` is `["In"]` or `["NotIn"]`
- `comparators[0]` is a `Tuple` or `List`
- All `elements` are `Constant` (literals)
- Element count is at or below threshold N (N = 3 recommended)

### Transformation

**Before (EAST3 input)**:

```json
{
  "kind": "Compare",
  "left": {"kind": "Name", "id": "x", "resolved_type": "int64"},
  "ops": ["In"],
  "comparators": [{
    "kind": "Tuple",
    "elements": [
      {"kind": "Constant", "value": 1, "resolved_type": "int64"},
      {"kind": "Constant", "value": 2, "resolved_type": "int64"}
    ]
  }]
}
```

**After (EAST3 optimizer output)**:

```json
{
  "kind": "BoolOp",
  "op": "Or",
  "values": [
    {
      "kind": "Compare",
      "left": {"kind": "Name", "id": "x", "resolved_type": "int64"},
      "ops": ["Eq"],
      "comparators": [{"kind": "Constant", "value": 1, "resolved_type": "int64"}]
    },
    {
      "kind": "Compare",
      "left": {"kind": "Name", "id": "x", "resolved_type": "int64"},
      "ops": ["Eq"],
      "comparators": [{"kind": "Constant", "value": 2, "resolved_type": "int64"}]
    }
  ],
  "resolved_type": "bool"
}
```

For `NotIn`, convert to `BoolOp(And, [Compare(NotEq), ...])`.

### Threshold

- N = 3 is recommended. Leave 4 or more elements as an iterable `contains`
- The threshold is a parameter of the optimizer, not hardcoded

### Out of Scope

- Cases containing non-literal elements (variables, function calls, etc.) are not expanded — risk that the evaluation order of side effects changes
- `x in range(...)` is a separate optimization (range membership test) and is out of scope for this task
- `x in set_literal` is not expanded because O(1) set lookup is preferable

## Implementation Location

Add a pass under `src/toolchain2/optimize/`. Incorporate it into the existing optimizer pass list.

## Impact

- EAST3 node shape changes, so golden diffs will appear after the transformation
- The emitter only needs to render the transformed `BoolOp` / `Compare(Eq)` — no emitter changes required
- Verify no regressions in all-language fixture + sample parity
