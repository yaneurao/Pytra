# P0-CPP-OPT-VARIANT: C++ parity recovery after optional<variant> migration

Last updated: 2026-04-02

## Background

The C++ emitter changed the type mapping for `T1 | T2 | None` from `std::variant<..., std::monostate>` to `std::optional<std::variant<...>>` (commit f8c4c618b).

This makes EAST's `OptionalType(inner=UnionType)` → C++ `std::optional<std::variant<...>>` correspond to Rust's `Option<enum>`, and `is None` checks are unified under `py_is_none()` / `has_value()`.

Parity status after the migration:
- fixture: 130/137 PASS (same as before the change, no regression)
- sample: 18/18 PASS
- stdlib non-JSON: 13/13 PASS
- stdlib JSON: 0/3 FAIL (`json_extended`, `json_indent_optional`, `json_nested`)

The 3 JSON FAILs occur because JsonValue's `resolved_type` is expanded to `bool | int64 | float64 | str | ... | None`, causing `list[JsonValue]` to become `list<optional<variant<...>>>` and producing function signature mismatches. JsonValue should be treated as a `NominalAdtType`; the expansion of the `resolved_type` string is the root cause.

## Target

- `src/toolchain2/emit/cpp/emitter.py` — emit corrections around optional<variant>
- `src/toolchain2/emit/cpp/types.py` — type mapping for NominalAdtType / JsonValue
- `src/runtime/cpp/` — add runtime helpers for optional<variant> if needed
- `test/stdlib/source/py/` — json_extended, json_indent_optional, json_nested

## Out of scope

- Rust emitter enum migration (separate task)
- The remaining 7 failures out of fixture 130→137 (pre-existing failures with different causes)

## Acceptance Criteria

- [ ] `json_extended` passes C++ stdlib parity
- [ ] `json_indent_optional` passes C++ stdlib parity
- [ ] `json_nested` passes C++ stdlib parity
- [ ] No regression in fixture 130/137 or sample 18/18

## Subtasks

1. [ ] [ID: P0-CPP-OPT-VAR-S1] Investigate why JsonValue's resolved_type expansion gets caught up in optional<variant>, and fix the NominalAdtType type mapping
2. [ ] [ID: P0-CPP-OPT-VAR-S2] Confirm that json_extended / json_indent_optional / json_nested pass C++ parity
3. [ ] [ID: P0-CPP-OPT-VAR-S3] Confirm that there is no regression in fixture + sample

## Decision Log

- 2026-04-01: Performed monostate → optional<variant> migration. No regression in fixture/sample/stdlib(non-JSON). The 3 JSON failures were filed with NominalAdtType's resolved_type expansion identified as the root cause.
