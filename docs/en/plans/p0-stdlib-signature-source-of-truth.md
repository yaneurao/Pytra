# P0: Make stdlib type specs a single source of truth (remove direct core writes)

Last updated: 2026-03-01

Related TODO:
- `ID: P0-STDLIB-SOT-01` in `docs/ja/todo/index.md`
- `ID: P0-STDLIB-SOT-02` in `docs/ja/todo/index.md`

Background:
- Standard-library specs such as `perf_counter -> float64` are currently hardcoded in `src/pytra/compiler/east_parts/core.py`.
- Type information also exists in library implementation side files such as `pytra/std/time.py`, so specs are managed in duplicate.
- If the spec source of truth is scattered on the compiler side, follow-up omissions on compiler updates become more likely when `pytra/std` changes.

Goal:
- Unify the source of truth for standard-library type specs on the `pytra/std` side, and reduce `core.py` to a consumer.
- Gradually remove direct hardcoding of per-stdlib knowledge (`perf_counter` / `Path` / `str.*`, etc.) from `core.py`.

In scope:
- `src/pytra/compiler/east_parts/core.py`
- `src/pytra/std/` (type-spec reference source)
- stdlib signature reference layer under `src/pytra/compiler/` (new)
- Type inference/lowering regressions in `test/unit`

Out of scope:
- Simultaneous large refactor across all backends
- Spec changes to stdlib APIs themselves
- Runtime implementation optimization

Acceptance criteria:
- Hardcoded stdlib return types such as `perf_counter` in `core.py` are replaced to go through the reference layer.
- Changing signatures on `pytra/std` side is reflected on compiler side (without duplicate definitions).
- Existing transpile/smoke tests do not regress.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `python3 -m unittest discover -s test/unit -p 'test_*core*.py' -v`
- `python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`

Decision log:
- 2026-02-28: Per user instruction, fixed the P0 policy to make `pytra/std` the single source of truth for type specs and remove standard-library knowledge from `core.py`.
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S1-01`] Inventoried direct stdlib hardcoding in `core.py` and fixed replacement targets into categories: built-in function map, owner-type method map, and `perf_counter` return-type hardcoding.
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S1-02`] Added `docs/ja/spec/spec-stdlib-signature-source-of-truth.md` and documented source-of-truth/reference boundary, lookup units, and fail-closed behavior.
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S2-01`] Added `src/pytra/compiler/stdlib/signature_registry.py` as a new reference layer that reads function/method return annotations from `pytra/std/*.py`.
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S2-02`] Removed hardcoded `perf_counter -> float64` in `core.py` and replaced it with `lookup_stdlib_function_return_type("perf_counter")`. Verified with `test_stdlib_signature_registry.py`, new cases in `test_east_core.py`, and existing perf_counter regression in `test_py2cpp_codegen_issues.py`.
- 2026-02-28: [ID: `P0-STDLIB-SOT-01-S2-03`] Moved method runtime maps for `str/Path/int/list/set/dict/unknown` and `Path` attribute type maps to `signature_registry.py`, removing large direct maps from `core.py`. Confirmed behavior retention with `test_stdlib_signature_registry.py` and existing lowering regressions in `test_east_core.py`.
- 2026-03-01: [ID: `P0-STDLIB-SOT-02`] Had been marked complete, but was reopened because direct branch `fn_name == "perf_counter"` still remained in `core.py`. Fixed policy to fully remove `perf_counter` string dependency from `core.py` and add a regression to prevent reintroduction.

## Inventory results (S1-01)

- Direct hardcoded built-in function calls:
  - `print/len/range/zip/str/int/float/bool/min/max/perf_counter/open/iter/next/reversed/enumerate/any/all/ord/chr/bytes/bytearray/list/set/dict`
- Direct hardcoded exception/special calls:
  - `Exception/RuntimeError -> std::runtime_error`
  - `Path -> Path`
- Direct hardcoded owner-type method maps:
  - `str`: `strip/lstrip/rstrip/startswith/endswith/find/rfind/replace/join/isdigit/isalpha`
  - `Path`: `mkdir/exists/write_text/read_text/parent/name/stem`
  - `int`: `to_bytes`
  - `list`: `append/extend/pop/clear/reverse/sort`
  - `set`: `add/discard/remove/clear`
  - `dict`: `get/pop/items/keys/values`
  - `unknown`: `append/extend/pop/get/items/keys/values/isdigit/isalpha`

## Breakdown

- [x] [ID: P0-STDLIB-SOT-01-S1-01] Inventory direct standard-library knowledge in `core.py` (`perf_counter` / `Path` / `str.*` / `dict.*`, etc.) and pin replacement targets.
- [x] [ID: P0-STDLIB-SOT-01-S1-02] Document signature-reference spec with `pytra/std` as source of truth (lookup units, type representation, fail-closed when undefined).
- [x] [ID: P0-STDLIB-SOT-01-S2-01] Add compiler-side stdlib signature reference layer and switch to a structure where `core.py` does not reference direct string maps.
- [x] [ID: P0-STDLIB-SOT-01-S2-02] Move representative cases including `perf_counter` to the reference layer and remove hardcoded return types from `core.py`.
- [x] [ID: P0-STDLIB-SOT-01-S2-03] Migrate method mappings such as `Path` / `str.*` step by step and limit `core.py` responsibility to syntax analysis + EAST shaping.
- [x] [ID: P0-STDLIB-SOT-01-S3-01] Add regression tests (type inference, lowering, representative sample cases) and pin detection for `pytra/std` spec changes.
- [x] [ID: P0-STDLIB-SOT-02] Remove direct branch `fn_name == "perf_counter"` from `core.py` and unify on stdlib signature reference layer.
- [x] [ID: P0-STDLIB-SOT-02-S1-01] Remove `perf_counter` string dependency from `core.py` and migrate `BuiltinCall` judgment through import-resolution info or common resolver.
- [x] [ID: P0-STDLIB-SOT-02-S1-02] Add anti-reintroduction regression in `test_east_core.py`.
- [x] [ID: P0-STDLIB-SOT-02-S2-01] Confirm no regression via `test_py2cpp_codegen_issues.py` and `check_py2cpp_transpile.py`.
