<a href="../../ja/plans/p6-cpp-fixture-parity-failures.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-%E6%97%A5%E6%9C%AC%E8%AA%9E-2563EB?style=flat-square">
</a>

# P6: Resolving C++ fixture parity failures

Last updated: 2026-03-31

Related TODO:
- `ID: P6-CPP-FIXPAR-*` in `docs/ja/todo/cpp.md`

## Background

Running:
`PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2`
resulted in C++ fixture parity of `131 cases / 126 pass / 5 fail`.

The 5 failures are as follows:

| Case | Type | Symptom |
|---|---|---|
| `optional_none` | output mismatch | Output for `Any | None` does not match Python |
| `integer_promotion` | output mismatch | Execution result for integer promotion does not match Python |
| `nested_closure_def` | compile failure | Reference target in nested closure becomes `::inner` / `::rec`, which is unresolved |
| `ok_generator_tuple_target` | compile failure | `py_zip` / `py_sum` in `zip_ops.h` and `list_ops.h` are redefined |
| `ok_typed_varargs_representative` | compile failure | Binding `const ControllerState&` to `ControllerState&` corrupts const qualification |

These 5 cases remain as known C++ red cases in `docs/ja/progress/backend-progress-fixture.md`. The goal here is to address each of these outstanding issues individually and raise fixture parity.

## Target

- `src/toolchain2/emit/cpp/` — C++ emitter / signature / closure / include generation
- `src/toolchain2/emit/common/` — to the extent needed for common renderer / lowering connections
- `src/runtime/cpp/built_in/` — fix if duplicate definition cleanup in `zip_ops.h` / `list_ops.h` is needed
- `tools/unittest/toolchain2/` / `tools/unittest/emit/cpp/` — add regression tests
- `docs/ja/todo/cpp.md` — update progress

## Out of scope

- New improvements to sample parity (only verify no regression from fixture failure resolution)
- Comprehensive improvement of the C++ backend beyond the known red cases

## Acceptance Criteria

- [ ] `optional_none` passes C++ fixture parity
- [ ] `integer_promotion` passes C++ fixture parity
- [ ] `nested_closure_def` passes C++ fixture parity
- [ ] `ok_generator_tuple_target` passes C++ fixture parity
- [ ] `ok_typed_varargs_representative` passes C++ fixture parity
- [ ] Representative unit / parity tests are added, with no new regressions

## Subtasks

1. [ ] [ID: P6-CPP-FIXPAR-S1] Resolve `output mismatch` for `optional_none`
2. [ ] [ID: P6-CPP-FIXPAR-S2] Resolve `output mismatch` for `integer_promotion`
3. [ ] [ID: P6-CPP-FIXPAR-S3] Fix closure reference resolution for `nested_closure_def`
4. [ ] [ID: P6-CPP-FIXPAR-S4] Resolve `py_zip` / `py_sum` redefinition for `ok_generator_tuple_target`
5. [ ] [ID: P6-CPP-FIXPAR-S5] Resolve const qualification mismatch for `ok_typed_varargs_representative`

## Decision Log

- 2026-03-31: Filed. Prioritize the 3 compile failures (`nested_closure_def`, `ok_generator_tuple_target`, `ok_typed_varargs_representative`) first, then address the 2 `output mismatch` cases (`optional_none`, `integer_promotion`).
- 2026-03-31: In the C++ emitter, registered local closures in visible local scope, and corrected mutable params with call-graph-based fixup. Reorganized `zip_ops.h` as a shim to `list_ops.h`, treated `is None` as `py_is_none(...)`, and decided to ignore stale integer `numeric_promotion` casts at emit time.
- 2026-03-31: Verification complete. `PYTHONPATH=src:tools python3 tools/check/runtime_parity_check_fast.py --targets cpp --case-root fixture --east3-opt-level 2` is `131/131 PASS`, and `--case-root sample` is `18/18 PASS`. All 5 P6 cases resolved.
