# Plan: Migrate C++ to std::variant and retire object/box/unbox

## Background

The current C++ runtime degrades union types to `object` (`{type_id, rc<RcObject>}`) and moves values in and out via boxing/unboxing. This is the root cause of the emitter's complexity.

The following has been demonstrated in `work/tmp/variant_test.cpp`:
- `std::variant<int64_t, std::string, NoneType>` works for basic unions
- Recursive types work with `struct { variant<..., shared_ptr<vector<Self>>> }` (forward reference + RC sharing)
- isinstance works natively via `std::holds_alternative<T>()`
- callables work via `std::function`

## Incremental Migration

### Phase 1: Add variant output to the C++ emitter

Read EAST3's `UnionType` and generate `std::variant<T1, T2, ...>`.

1. Add a `UnionType` → `std::variant<...>` path to the C++ emitter's type conversion
2. Add an `OptionalType` → `std::optional<T>` path (may already exist)
3. Convert isinstance narrowing to `std::holds_alternative<T>` + `std::get<T>`
4. Emit recursive types as `struct { variant<..., shared_ptr<vector<Self>>> }`
5. Keep the `object` path at this point as a fallback

Acceptance Criteria: Fixtures using basic unions such as `int | str`, `str | None`, `int | float | None` pass in C++

### Phase 2: Remove the object type from C++

Once variant is working in Phase 1, remove the degradation path to `object`.

1. Replace all `object` type output in the C++ emitter with `std::variant`
2. Change `Box` node C++ output to direct assignment into a variant
3. Change `Unbox` node C++ output to `std::get<T>`
4. Replace `type_id`-based isinstance with `std::holds_alternative<T>`
5. Delete `PYTRA_TID_*` constants, `g_type_table` (already removed), `py_runtime_object_type_id`, etc.
6. Delete or shrink the `object` class in `object.h`

Acceptance Criteria: All C++ fixtures + all samples pass without the `object` type

### Phase 3: Remove box/unbox processing from C++

1. Remove `_emit_box` / `_emit_unbox` from the C++ emitter
2. Emit assignments to variant as ordinary assignments
3. Emit extraction from variant as `std::holds_alternative` + `std::get`
4. Remove emitter code that depends on the `yields_dynamic` flag

Acceptance Criteria: Zero box/unbox-related code in the C++ emitter

### Phase 4: Remove object degradation / box / unbox from EAST

Once C++ is working in Phases 2–3, change the EAST3 lowering.

1. Remove boxing at lower.py:597 (generating `resolved_type="object"`)
2. Remove iter boundary at lower.py:2042-2075 (generating `resolved_type="object"`)
3. Rename `Box` / `Unbox` node kinds to `VariantStore` / `VariantNarrow` (or retire them)
4. Retire the `yields_dynamic` flag
5. Add EAST3 validation: error if `resolved_type: "object"` appears in the output
6. Remove `"object"` normalization from `type_summary.py` / `type_norm.py`

Acceptance Criteria: No `object` / `Box` / `Unbox` in EAST3 output. All languages' fixture + sample pass.

### Phase 5: Roll out to other languages

After object/box/unbox are removed from EAST, update other language emitters:

- Rust: convert to `enum` (already has a PyAny enum; unify on variant basis)
- Go: keep `any` (use type switch; no change needed)
- TS: union as-is (no change needed)
- C#: sealed record / abstract class
- Java: sealed class
- Dynamically typed languages: no change

## Notes

### int literal ambiguity

Assigning an `int` literal to `std::variant<int64_t, double, bool>` produces ambiguity (demonstrated). The emitter must make the type explicit, e.g. `int64_t(42)`. Coordination with P0-CPP-LITERAL-CAST's `literal_nowrap_ranges` is needed.

### Relationship to Optional

`T | None` can be expressed as `std::optional<T>`, but `std::variant<T, NoneType>` also works. The distinction between EAST3's `OptionalType` and `UnionType` needs to be clarified.

### Impact on selfhost

Selfhost code makes heavy use of `JsonVal`, which is a nominal ADT (spec-east.md §6.5). If it is converted as `struct { variant<...> }` rather than being degraded to `object`, the selfhost collapse pattern should also be resolved. However, retry selfhost only after Phases 1–3 are stable.

## Related

- [spec-adt.md](../spec/spec-adt.md): ADT specification (object degradation prohibited)
- [plan-union-to-nominal-adt.md](./plan-union-to-nominal-adt.md): Migration plan for all languages
- `work/tmp/variant_test.cpp`: Proof-of-concept code
