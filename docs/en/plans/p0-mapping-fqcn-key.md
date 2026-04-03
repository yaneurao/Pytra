# P0-MAPPING-FQCN-KEY: Unify mapping.json calls keys to fully-qualified names

Last updated: 2026-04-03

## Background

The `calls` keys in mapping.json are bare symbols (`"sin"`, `"cos"`, etc.), because `resolve_runtime_symbol_name` (in `src/toolchain2/emit/common/code_emitter.py`) looks up mapping.json using only the `runtime_symbol` value.

This creates a risk of name collision. If a user defines `def sin(x):`, it would match `"sin": "std::sin"` in mapping.json and be converted to `std::sin`.

EAST3 already carries fully-qualified information as `runtime_module_id: "pytra.std.math"` + `runtime_symbol: "sin"`. The keys in mapping.json should also be fully-qualified (`"pytra.std.math.sin": "std::sin"`).

### Current problems

1. **Name collision**: bare `"sin"` can collide with user-defined functions
2. **Duplicate entries**: both `"math.sin"` and `"sin"` are registered (a remnant of old `builtin_name` handling)
3. **Dead entries**: `"math.sin"` is used neither as a `runtime_call` nor as a `runtime_symbol` in EAST3
4. **False lint positives**: `rt: call_cov` compares mapping.json keys against EAST3's `runtime_call` and reports many mismatches

### Affected areas

- `src/toolchain2/emit/common/code_emitter.py` — resolution logic in `resolve_runtime_symbol_name` and `collect_runtime_symbol_imports`
- `src/runtime/<lang>/mapping.json` for all 18 languages — rewriting `calls` keys
- `tools/check/check_runtime_call_coverage.py` — matching logic

## Approach

1. Pass `runtime_module_id` to `resolve_runtime_symbol_name`
2. Look up mapping.json first using the fully-qualified key (`runtime_module_id + "." + runtime_symbol`)
3. Fall back to bare symbol lookup as a compatibility measure during the migration period
4. Unify all language mapping.json keys to fully-qualified form
5. Remove the fallback and use fully-qualified keys only

## Subtasks

1. [ ] [ID: P0-FQCN-KEY-S1] Add a `module_id` parameter to `resolve_runtime_symbol_name` and look up `module_id + "." + symbol` first (keep bare fallback)
2. [ ] [ID: P0-FQCN-KEY-S2] Unify the `calls` keys in all language mapping.json files to fully-qualified form (e.g. `pytra.std.math.sin`). Consolidate duplicate entries (`"math.sin"` + `"sin"`) into a single fully-qualified entry
3. [ ] [ID: P0-FQCN-KEY-S3] Remove the bare fallback; resolve using fully-qualified keys only
4. [ ] [ID: P0-FQCN-KEY-S4] Update the matching logic in `check_runtime_call_coverage.py` to support fully-qualified keys
5. [ ] [ID: P0-FQCN-KEY-S5] Confirm no regression in C++ parity (representative check via C++; delegate per-language verification to respective owners)

## Decision Log

- 2026-04-03: Identified the risk that mapping.json's `"sin"` as a bare symbol can collide with user-defined functions. Since EAST3 already carries `runtime_module_id` + `runtime_symbol` as fully-qualified information, mapping.json keys should also be fully-qualified. Filed as a bug in the common infrastructure (`code_emitter.py`).
