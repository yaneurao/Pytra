# P0-ISINS-DETID-CPP: Remove PYTRA_TID_* reverse lookup from C++ emitter and migrate to type-name-based approach

Last updated: 2026-04-03

## Background

EAST3's `IsInstance` node references deprecated type_id constants such as `expected_type_id: {"id": "PYTRA_TID_DICT"}` (listed as deprecated in spec-adt.md §6).

The C++ emitter maintains an internal table that reverse-looks up these `PYTRA_TID_*` values to type names, converting `PYTRA_TID_DICT` → `dict` → `std::holds_alternative<dict<...>>`.

The infra task P0-ISINSTANCE-DETID (S1-S3) will change EAST3's `IsInstance` node to carry `expected_type_name: "dict"` directly. Once that is done, the C++ emitter's reverse lookup table will be unnecessary and should be removed.

## Prerequisites

- Infra's P0-ISINSTANCE-DETID S1-S3 must be completed
- `PYTRA_TID_*` must not appear in EAST3 golden files

## Target

- `src/toolchain2/emit/cpp/emitter.py` — the `PYTRA_TID_*` → type-name reverse lookup table and related logic

## Changes

Current C++ emitter isinstance handling:

```python
# Current: reverse-lookup PYTRA_TID_* to type name
expected_name = _normalize_expected_type_name(expected_type_id)  # "PYTRA_TID_DICT" → "dict"
```

After the change:

```python
# After: use expected_type_name directly
expected_name = _str(node, "expected_type_name")  # "dict"
```

Items to remove:
- The `PYTRA_TID_*` branch in `_normalize_expected_type_name`
- Reverse lookup tables such as `_TYPE_ID_TO_NAME` (if present)

## Acceptance Criteria

- [ ] The C++ emitter references `expected_type_name` directly
- [ ] The `PYTRA_TID_*` reverse lookup table has been removed from the C++ emitter
- [ ] Fixtures that use isinstance (`isinstance_narrowing`, `isinstance_pod_exact`, `isinstance_tuple_check`, etc.) pass C++ parity
- [ ] No regression in C++ parity for fixture + sample + stdlib

## Decision Log

- 2026-04-03: The C++ emitter work was separated from infra's P0-ISINSTANCE-DETID and filed as its own ticket. Work begins after infra has modified EAST3.
