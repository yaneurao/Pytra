# P1: C++ `py_to` Template Consolidation Plan

Last updated: 2026-02-25

Related TODO:
- `ID: P1-CPP-PYTO-01` in `docs-ja/todo/index.md`

Background:
- Currently `py_to_int64()` / `py_to_float64()` / `py_to_bool()` exist as separate APIs, and conversion routes for `object` / `std::any` / primitive types tend to duplicate.
- To improve conversion quality on `Any/object` paths while keeping call-site consistency manageable, we want staged introduction of a type-parameterized API.

Goal:
- Move toward unified C++ conversion helpers using `py_to<T>()`, while retaining existing `py_to_int64` and similar APIs as compatibility wrappers during migration.

In scope:
- Main implementation: `py_to_int64/py_to_float64/py_to_bool` family in `src/runtime/cpp/pytra-core/built_in/py_runtime.h` (while preserving compatibility with existing implementation and generated/used shape in `src/runtime/cpp/pytra/built_in/py_runtime.h`).
- Calls from `src/hooks/cpp/emitter/cpp_emitter.py` and related emitters.
- Type-cast paths in `src/hooks/cpp/emitter/expr.py`.

Out of scope:
- Full redesign of `py_to_string` stringification policy (separate task).
- Full replacement of runtime conversion APIs in other languages.

Acceptance criteria:
- Main conversion paths use `py_to<T>` while preserving equivalent runtime semantics.
- Existing compatibility wrappers `py_to_int64` / `py_to_float64` / `py_to_bool` remain, avoiding destructive change for existing code.
- Selfhost / C++ transpile regression tests pass.

Verification commands:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_todo_priority.py` (when updated)
- `python3 test/unit/test_unit_runtime.py` (or corresponding runtime test set)

Execution policy:
1) Define `py_to<T>` skeleton in runtime headers (`enable_if` / SFINAE / dedicated overloads for `object` and `std::any`).
2) Replace emitter-side call sites in phases while retaining existing `py_to_*` calls as wrappers.
3) To avoid implementation drift between `src/runtime/cpp/pytra-core` and `src/runtime/cpp/pytra`, validate include dependencies and generation diffs during migration and record decisions in plans docs.

Related docs:
- `docs-ja/spec/spec-type_id.md`
- `docs-ja/plans/p2-any-object-boundary.md`

Note:
- Design starts from the `pytra-core` API. `pytra/built_in` follows within a range that does not break current reference paths.

`P1-CPP-PYTO-01-S1` finalized (2026-02-25):
- Added `py_to<T>` templates (`object` / `std::any` / value types) in `src/runtime/cpp/pytra-core/built_in/py_runtime.h`, unifying major destinations (`int64` / `float64` / `bool` / `str` / `object`).
- Kept existing APIs (`py_to_int64` / `py_to_float64` / `py_to_bool`) as compatibility wrappers and moved arithmetic/object routes through `py_to<T>`.
- Validation:
  - `python3 tools/check_py2cpp_transpile.py` (`checked=131 ok=131 fail=0 skipped=6`)
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 01_mandelbrot --ignore-unstable-stdout` (`SUMMARY cases=1 pass=1 fail=0 targets=cpp`)

`P1-CPP-PYTO-01-S2` finalized (2026-02-25):
- Migrated cast lowering in `src/hooks/cpp/emitter/expr.py` to `py_to<float64>` / `py_to<int64>` / `py_to<bool>` style.
- Replaced direct `py_to_int64/py_to_float64/py_to_bool` calls in `src/hooks/cpp/emitter/cpp_emitter.py` in phases (`dict` default retrieval, indexing, truthy checks, `range/enumerate` args, etc.) with `py_to<...>` style.
- Validation:
  - `python3 test/unit/test_py2cpp_smoke.py` (3 passed)
  - `python3 tools/check_py2cpp_transpile.py` (`checked=131 ok=131 fail=0 skipped=6`)
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 01_mandelbrot --ignore-unstable-stdout` (`SUMMARY cases=1 pass=1 fail=0 targets=cpp`)

`P1-CPP-PYTO-01-S3` finalized (2026-02-25):
- Added runtime smoke checks in `test/unit/test_cpp_runtime_boxing.py` for `py_to_int64(object/any)` and `py_to<int64>(object/any)` behavior, fixing the contract difference: non-convertible values return `0`; strict validation uses `obj_to_int64_or_raise`.
- Added note to `readme-ja.md` / `readme.md` describing C++ runtime conversion policy (`py_to_int64` family prioritizes compatibility and returns `0`; strict mode uses `_or_raise`).
- Validation:
  - `python3 test/unit/test_cpp_runtime_boxing.py` (1 passed)
  - `python3 tools/check_py2cpp_transpile.py` (`checked=131 ok=131 fail=0 skipped=6`)
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 01_mandelbrot --ignore-unstable-stdout` (`SUMMARY cases=1 pass=1 fail=0 targets=cpp`)

Decision log:
- [2026-02-25] [ID: P1-CPP-PYTO-01]
  - Added staged `py_to<T>` consolidation task to TODO with a compatibility-wrapper-first policy.
- 2026-02-25: As `P1-CPP-PYTO-01-S1`, introduced `py_to<T>` templates in `py_runtime.h` and converted major `py_to_int64`/`py_to_float64`/`py_to_bool` paths to backward-compatible wrappers.
- 2026-02-25: As `P1-CPP-PYTO-01-S2`, migrated direct `py_to_*` calls in `cpp_emitter.py` / `expr.py` to `py_to<...>` in phases and confirmed no behavioral diffs on C++ transpile/smoke/parity (1-case spot check).
- 2026-02-25: As `P1-CPP-PYTO-01-S3`, fixed runtime tests for default/strict behavior of `py_to_int64(object/any)` and updated README notes (JA/EN).
