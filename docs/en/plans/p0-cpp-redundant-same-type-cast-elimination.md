# P0: Eliminate C++ Same-Type Casts and Pull Type Inference Earlier (highest priority)

Last updated: 2026-02-28

Related TODO:
- `ID: P0-CPP-SAMECAST-01` in `docs/en/todo/index.md`

Background:
- Same-type conversions such as `str(ch).isdigit()` remain in generated C++ for sample/18, reducing readability and optimization headroom.
- The issue is not specific to `isdigit`; it occurs across same-type casts including `str` in general.
- Current fail-closed behavior overuses defensive casts, and even type-known paths go through the same path, causing redundancy.

Goal:
- Unify C++ backend cast policy as "no conversion for same type" and avoid emitting unnecessary `str(...)` / `py_to_*` on type-known paths.
- At the same time, strengthen earlier-stage type inference to increase paths where downstream emitter can avoid falling back to `Any/object`.

Scope:
- `src/hooks/cpp/emitter/cpp_emitter.py`
- `src/hooks/cpp/emitter/expr.py`
- `src/hooks/cpp/emitter/type_bridge.py`
- `src/hooks/cpp/emitter/builtin_runtime.py`
- `src/pytra/compiler/east_parts/core.py` if needed (EAST3 typing)
- `test/unit/test_py2cpp_smoke.py` / `test/unit/test_east3_cpp_bridge.py`
- `sample/cpp/18_mini_language_interpreter.cpp`

Out of scope:
- Large-scale rewrite of the entire C++ backend
- Adding new optimization families to the EAST3 optimizer (this task is limited to cast policy and type inference)
- Simultaneous rollout to other language backends

Acceptance criteria:
- Around `isdigit/isalpha` in sample/18, `str(...)` disappears for type-known `str`.
- Add regression tests that prevent new same-type `py_to_string` / `py_to<int64>` / `py_to<float64>` on type-known paths.
- `check_py2cpp_transpile` and related unit/smoke pass.
- After regenerating `sample/cpp`, sample/18 compile/run pass.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_smoke.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout`

Decision log:
- 2026-02-28: By user instruction, confirmed policy to handle this at P0 as "remove same-type casts including `str` globally" rather than a point fix for `isdigit`.
- 2026-02-28: [ID: `P0-CPP-SAMECAST-01-S1-01`] Consolidated same-type cast decisions into `CppAnalysisEmitter.should_skip_same_type_cast()`, and fixed `apply_cast` / `_render_unbox_target_cast` to share one rule (same type on non-Any/object/unknown is no-op).
- 2026-02-28: [ID: `P0-CPP-SAMECAST-01-S1-02`] Added `Subscript(str, int) -> str` inference to `CppEmitter.get_expr_type()` for `Subscript`, preventing string-index type drops.
- 2026-02-28: [ID: `P0-CPP-SAMECAST-01-S1-03`] Updated `StrCharClassOp`: type-known `str` emits direct `receiver.isdigit()/isalpha()`, while only unknown/object paths keep defensive `str(...)` casts.
- 2026-02-28: [ID: `P0-CPP-SAMECAST-01-S2-01`] Added same-type no-op checks in `apply_cast` and `_render_unbox_target_cast` so same-type casts inferable from rendered expressions (non-Any/object/unknown) are omitted.
- 2026-02-28: [ID: `P0-CPP-SAMECAST-01-S2-02`] Added char-class regression for sample/18 (`test_sample18_charclass_avoids_redundant_str_cast`). Also updated expected values in `test_east3_cpp_bridge.py` to pin no-cast output for type-known `str`.
- 2026-02-28: [ID: `P0-CPP-SAMECAST-01-S3-01`] Re-ran `python3 tools/regenerate_samples.py --langs cpp --force` (`summary: total=18 skip=0 regen=18 fail=0`) and `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 18_mini_language_interpreter --ignore-unstable-stdout` (`[PASS] 18_mini_language_interpreter`), confirming regenerated sample and parity pass.

## Breakdown

- [x] [ID: P0-CPP-SAMECAST-01-S1-01] Fix same-type cast removal policy as shared C++ emitter rule (no conversion when source/target are same type and non-Any/object/unknown).
- [x] [ID: P0-CPP-SAMECAST-01-S1-02] Extend `get_expr_type()` `Subscript` inference to determine `Subscript(str, int) -> str`.
- [x] [ID: P0-CPP-SAMECAST-01-S1-03] Fix string-related lowering including `StrCharClassOp` so type-known `str` does not insert `str(...)`.
- [x] [ID: P0-CPP-SAMECAST-01-S2-01] Introduce same-type no-op checks in `apply_cast` / `Unbox` / builtin runtime conversion paths to suppress redundant `py_to_*` chains.
- [x] [ID: P0-CPP-SAMECAST-01-S2-02] Add regressions for no same-type-cast output (fixture + sample/18 fragment checks).
- [x] [ID: P0-CPP-SAMECAST-01-S3-01] Regenerate `sample/cpp`, reconfirm sample/18 compile/run/parity, and record results in context.
