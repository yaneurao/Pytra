# Plan: Remove redundant casts on integer literals (P0-CPP-LITERAL-CAST)

## Background

The C++ emitter's `_emit_constant` (`emitter.py:1026-1027`) always emits integer literals with an explicit type cast:

```cpp
// Current: redundant
for (int64 i = int64(0); i < max_iter; i += 1) {
int64 x = int64(42);
int32 count = int32(0);

// Ideal: no cast when safe
for (int64 i = 0; i < max_iter; i += 1) {
int64 x = 42;
int32 count = 0;
```

This problem is not C++-specific. Go / Rust / Java / etc. all share the same structure: "if the type and value are within a certain range, emit the literal directly; otherwise wrap it." Rather than having each language's emitter implement this independently, it should be shared in CommonRenderer.

## Literal Type Rules by Language

| Language | Literal type determination | When cast is unnecessary |
|---|---|---|
| C++ | `int` → `long` → `long long` based on value | Within `int` range for `int32` / `int64` |
| Go | Integer literals are untyped constants | Almost never needs a cast (type inference applies) |
| Rust | Integer literals without a suffix are inferred | No cast needed when type can be inferred from context |
| Java | `int` by default, `L` suffix for `long` | Not needed for `int` within `int` range; `long` requires `L` |
| C# | Same as Java | Same as above |

## Design: Add `literal_nowrap_ranges` to CommonRenderer

### Add configuration to the profile (mapping.json or profile.json)

```json
{
  "literal_nowrap_ranges": {
    "int32": [-2147483648, 2147483647],
    "int64": [-2147483648, 2147483647],
    "float64": "always"
  }
}
```

- Key: EAST `resolved_type`
- Value: `[min, max]` — no cast needed if the literal value is within this range. `"always"` means never cast.
- Types not in the table always require a cast (status quo preserved).

### Extend `render_constant` in CommonRenderer

```python
def render_constant(self, node: dict[str, JsonVal]) -> str:
    value = node.get("value")
    if value is None:
        return self._none_literal()
    if isinstance(value, bool):
        return self._bool_literal(value)
    if isinstance(value, str):
        return self._quote_string(value)
    if isinstance(value, int):
        rt = self._str(node, "resolved_type")
        if self._literal_needs_wrap(rt, value):
            return self._wrap_int_literal(rt, value)
        return str(value)
    return str(value)
```

- `_literal_needs_wrap(rt, value)`: consults the `literal_nowrap_ranges` table to decide whether wrapping is needed
- `_wrap_int_literal(rt, value)`: wraps with the type name. Default is `type_name(value)`. Can be overridden for language-specific formats (e.g. Java's `(long)42` or `42L`)

### Remove integer cast logic from C++ emitter's `_emit_constant`

Because CommonRenderer handles the decision, no override is needed in the C++ emitter. The integer branch in `_emit_constant` collapses to a delegation to CommonRenderer.

## Decision Rule (C++)

`literal_nowrap_ranges` table:

| EAST type | Range | Reason |
|---|---|---|
| `int32` | [-2^31, 2^31-1] | `int` → `int32_t` is a same-width conversion |
| `int64` | [-2^31, 2^31-1] | `int` → `int64_t` is a safe widening conversion |
| `float64` | always | `double` literals can be emitted as-is |
| `int8`, `int16` | (none) | Narrowing — always requires a cast |
| `uint*` | (none) | Sign conversion risk — always requires a cast |

## Impact

- Generated code appearance changes (`int64(0)` → `0`), so golden diffs will appear
- **Execution results do not change** — equivalent transformation under each language's implicit conversion rules
- Verify no regressions with fixture + sample parity check

## Implementation Order

1. Implement `literal_nowrap_ranges` table loading + `render_constant` extension in CommonRenderer
2. Configure `literal_nowrap_ranges` in the C++ profile/mapping
3. Delegate the integer cast logic in C++ emitter's `_emit_constant` to CommonRenderer
4. Verify fixture + sample parity
5. Configure `literal_nowrap_ranges` for other languages (Go, Rust, etc.) as a separate task

## Out of Scope

- Hardcoded `int64(0)` / `int64(1)` in `ForRange` and similar constructs (e.g. line 2445) should also be fixed, but may be done as a separate task

## Completion Notes

- Added `literal_nowrap_ranges` loading and integer literal determination to `CommonRenderer`, switching between bare literal and typed wrap based on the profile
- Set safe nowrap ranges for `int` / `int32` / `int64` in the C++ profile; `int8` / `int16` / `uint*` continue to wrap as before
- C++ emitter's `_emit_constant` now delegates integer types to CommonRenderer; a supplementary path that force-wraps argument literals with the target type is kept only for `min` / `max` to avoid breaking template deduction
- During parity verification, an existing bug was found where a `super().__init__(...)` call placed in an init-list for `ClosureDef` constructors was still left in the body; a regression fix was also applied to drop the leading `super().__init__` statement from the body when the constructor uses an init-list
