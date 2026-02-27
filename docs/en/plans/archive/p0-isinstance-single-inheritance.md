# P0: Reformat `type_id` `isinstance` Handling for Single-Inheritance Ranges

Related TODO:
- `ID: P0-ISINSTANCE-01` in `docs/ja/todo/index.md`

Background:
- `spec-type_id.md` has been updated toward a unified single-inheritance model with `type_id_min/max`, but `isinstance` implementation residue remains by language and keeps runtime branching.
- `P0-SAMPLE-GOLDEN-ALL-01` aims for all-language golden parity, but inconsistent `isinstance` logic causes cascading rework.
- We first force-unify `isinstance` to `type_id` interval checks and align semantics across emitters.

In scope:
- Emitter output paths using `isinstance` (at minimum C++ / JS / TS / Rust / C#)
- `type_id` API call paths (`py_isinstance` / `py_is_subtype` / `py_issubclass`)
- Existing logic that assumes multiple inheritance, name-string-based comparisons, and exceptional built-in paths

Out of scope:
- Reproducing ABC/virtual subclass behavior
- One-shot migration for all targets at the same time (staged migration is allowed)

Acceptance criteria:
- `isinstance(x, T)` is unified to interval checks using `type_id_min/max` on all target backends.
- Multiple base declarations are explicitly treated as errors.
- Existing `isinstance` smoke/regression tests in `tools/` stay green.
- No contradiction with interval-check definition in `docs/ja/spec/spec-type_id.md`.

Subtasks:
- `P0-ISINSTANCE-01-S1`: Spec-vs-implementation inventory (`isinstance` lowering in target emitters/runtimes).
- `P0-ISINSTANCE-01-S2`: Convert C++ runtime/emit paths to `py_isinstance` API and interval-based checks.
- `P0-ISINSTANCE-01-S3`: Consolidate JS/TS/RS/CS runtime+lowering to `py_type_id` API.
- `P0-ISINSTANCE-01-S4`: Reorganize tests (`test/unit/*isinstance*`) and TODO linkage.
- `P0-ISINSTANCE-01-S5`: Reflect spec alignment log in `docs/ja/spec/spec-type_id.md`; add cross-conditions to `spec-boxing` / `spec-linker` if needed.

Current inventory (2026-02-25):
- `C++`: Emitter lowering is already unified to `py_isinstance` / `py_is_subtype` / `py_issubclass`; `src/pytra/built_in/type_id.py` has moved to `order/min/max` interval checks.
- `JS/TS`: `isinstance` is lowered to `pyIsInstance`; runtime already uses interval checks via `pyTypeId` + `pyIsSubtype` (`order/min/max`).
- `Rust`: Emitter moved to `py_isinstance(&x, <type_id>)`; generated code embeds `PyTypeInfo(order/min/max)`, `py_is_subtype`, and `py_isinstance` helpers.
- `C#`: Emitter/runtime are unified to `py_isinstance` / `py_runtime_type_id` / `py_is_subtype`.
- `self_hosted parser`: Multiple base classes (`class C(A, B):`) are now explicitly rejected with `multiple inheritance is not supported`.

Decision log:
- 2026-02-25: `type_id` moved to a single-inheritance interval model, so this was added as a top-priority implementation task. The strategy is to avoid mixing with unrelated runtime predicates.
- 2026-02-25: In `P0-ISINSTANCE-01`, the self-hosted parser now emits an explicit error for multiple base classes. Also recorded `isinstance` lowering inventory for C++/JS/TS/RS/CS.
- 2026-02-25: In `P0-ISINSTANCE-01`, switched `src/pytra/built_in/type_id.py` and JS/TS runtime `py_is_subtype` to interval checks (`order/min/max`) and added regression tests to prevent sibling false-inclusion.
- 2026-02-25: In `P0-ISINSTANCE-01`, C# `isinstance` lowering was unified to `Pytra.CsModule.py_runtime.py_isinstance`; runtime gained `PYTRA_TID_*`, `py_runtime_type_id`, `py_is_subtype`, `py_isinstance`.
- 2026-02-25: In `P0-ISINSTANCE-01`, Rust emitter was updated to runtime-API lowering via `py_isinstance`; helper output for `type_id` interval tables (`PyTypeInfo`) was added. Verified: `test/unit/test_py2rs_smoke.py` (22 cases), `tools/check_py2rs_transpile.py` (`checked=130 ok=130 fail=0 skipped=6`), `tools/check_py2cpp_transpile.py` (`checked=131 ok=131 fail=0 skipped=6`), `tools/check_py2cs_transpile.py` (`checked=130 ok=130 fail=0 skipped=6`). For JS/TS, existing `east3-contract` failures were bypassed with `--skip-east3-contract-tests` and verified at `checked=130 ok=130 fail=0 skipped=6`.
- 2026-02-25: As `P0-ISINSTANCE-01-S4`, resolved blocking failures in `test_east3_cpp_bridge.py` (kept strict EAST3 while allowing limited stage2/self_hosted compatibility path; re-unified `dict[str,*]` key conversion to `py_to_string`; re-fixed `render_cond(Any)` to `py_to_bool`). Verified normal-mode checks: `tools/check_py2cpp_transpile.py` (`checked=131 ok=131 fail=0 skipped=6`) and `tools/check_py2rs_transpile.py` / `tools/check_py2cs_transpile.py` / `tools/check_py2js_transpile.py` / `tools/check_py2ts_transpile.py` (each `checked=130 ok=130 fail=0 skipped=6`); plus `test/unit/test_py2{js,ts,cs,rs}_smoke.py`, `test/unit/test_js_ts_runtime_dispatch.py`, `test/unit/test_pytra_built_in_type_id.py`, and five `isinstance` cases in `test_py2cpp_codegen_issues.py` all green.
- 2026-02-25: As `P0-ISINSTANCE-01-S5`, added to `docs/ja/spec/spec-type_id.md` codegen contract: strict `meta.east_stage=3` (fail-fast for non-lowered `isinstance`/builtin calls) and positioning of compatibility layer for `east_stage=2 + parser_backend=self_hosted`, aligned with current `CppEmitter` implementation and regression constraints.
