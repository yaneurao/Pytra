# P2: Simplify C++ Selfhost Virtual Dispatch

## Background
After aligning `virtual`/`override` behavior with the current class model, some manually constructed branch logic once used in selfhost-generated C++ (`type_id` checks + switch-like dispatch) became potentially removable.
Even if behavior remains correct as-is, simplification improves readability, maintainability, and debuggability of selfhost outputs.

## Acceptance criteria

- In selfhost-generated C++ (including regenerated `sample/` outputs), method-call paths should use `virtual` where possible, reducing unnecessary `type_id` dispatch branches.
- `py2cpp.py` and `CppEmitter` should generate override-compatible call paths with minimal branching.
- No regression in `tools/check_selfhost_cpp_diff.py` / `tools/verify_selfhost_end_to_end.py`.

## Subtasks

### S1: Pre-scope

1. `P2-CPP-SELFHOST-VIRTUAL-01-S1-01`: Extract class-method generation sites that use `type_id` conditional dispatch (`if (...) >= ... && ... <= ...`, `switch`) from `src`/`sample`/`test` via `rg` and lightweight AST scans.
2. `P2-CPP-SELFHOST-VIRTUAL-01-S1-02`: Classify extracted results into base-call / recursive-call / utility-call categories and document out-of-scope cases.
3. `P2-CPP-SELFHOST-VIRTUAL-01-S1-03`: Prioritize candidates that can be safely limited to override-enabled method calls.

`S1` finalized (2026-02-25):
- Scans over `sample/cpp`, `src/runtime/cpp/pytra-gen/{compiler,std,utils}`, and related test/code paths found **0** class-method dispatch branches using `type_id` conditional/switch logic.
- Remaining `type_id` condition logic was limited to `src/runtime/cpp/pytra-gen/built_in/type_id.cpp` registry/state management, which is out of scope for this task.

### S2: Prepare emitter-side replacement

4. `P2-CPP-SELFHOST-VIRTUAL-01-S2-01`: Decompose `render`/`call` candidate paths in `src/hooks/cpp/emitter` one-by-one (first `PyObj` methods, then user class methods).
5. `P2-CPP-SELFHOST-VIRTUAL-01-S2-02`: Table-ize class-method call-generation logic and explicitly separate default `type_id` fallback from virtual-route branches.
6. `P2-CPP-SELFHOST-VIRTUAL-01-S2-03`: Align replacement targets with S2-01 and keep known out-of-scope paths as fallback.

`S2` finalized (2026-02-26):
- Call/render paths were explicitly separated:
  - Built-in/PyObj path (non-target): name/attribute routes that require `BuiltinCall` lowering.
  - User class-method path (target): `_render_call_class_method` path with signature-based call shaping.
- Introduced explicit class-method dispatch modes in `src/hooks/cpp/emitter/call.py`:
  - `virtual`
  - `direct`
  - `fallback`
- Consolidated class-method candidate collection logic and reduced duplication.
- Locked non-target boundaries:
  - built-in lowering prerequisite paths
  - runtime/type_id API call routes (`IsInstance/IsSubtype/IsSubclass/ObjTypeId`)
  - `built_in/type_id.cpp` registry/state management

### S3: Apply replacements

7. `P2-CPP-SELFHOST-VIRTUAL-01-S3-01`: Start from 2-3 `sample` cases and replace removable `type_id` branches with `virtual` calls.
8. `P2-CPP-SELFHOST-VIRTUAL-01-S3-02`: Expand replacement range in small batches and check selfhost re-transpile feasibility.
9. `P2-CPP-SELFHOST-VIRTUAL-01-S3-03`: Add non-replaceable cases (where `type_id` segmentation is required) to non-target list with reasons.

`S3` finalized (2026-02-26):
- Re-scan confirmed no class-dispatch `type_id` branches in `sample/cpp` and `src/runtime/cpp/pytra-gen`; remaining `type_id` usage was initialization (`set_type_id(...)`) only.
- `check_selfhost_cpp_diff` remained stable (`mismatches=0 known_diffs=2`).
- `verify_selfhost_end_to_end` remained blocked by known selfhost pre-build issue in `tools/prepare_selfhost_source.py` (`CodeEmitter import` removal failure).

### S4: Regression lock and spec reflection

10. `P2-CPP-SELFHOST-VIRTUAL-01-S4-01`: Add/update selfhost-related unit/sample regression checks.
11. `P2-CPP-SELFHOST-VIRTUAL-01-S4-02`: Re-run `check_selfhost_cpp_diff.py` / `verify_selfhost_end_to_end.py` and verify reproducibility.
12. `P2-CPP-SELFHOST-VIRTUAL-01-S4-03`: Reflect concise progress to `docs/ja/spec/spec-dev.md` (and `spec-type_id` if needed).

`S4` finalized (2026-02-26):
- Added `test/unit/test_selfhost_virtual_dispatch_regression.py`:
  - verifies no reintroduction of `type_id` comparison/switch dispatch in `sample/cpp/*.cpp` and `src/runtime/cpp/pytra-gen/**/*.cpp` (excluding `built_in/type_id.cpp`).
- Reconfirmed:
  - `check_selfhost_cpp_diff`: `mismatches=0 known_diffs=2 skipped=0`
  - `verify_selfhost_end_to_end`: still blocked by known pre-build issue
- Reflected dispatch-mode and non-target boundary notes into `docs/ja/spec/spec-dev.md`.

### S5: Test additions (highest priority inside this task)

13. `P2-CPP-SELFHOST-VIRTUAL-01-S5-01`: Add test cases for `Base.f` call from `Child.f` (`Base.f` qualified and `super().f`) and verify `virtual/override` path with no `type_id` dispatch.
14. `P2-CPP-SELFHOST-VIRTUAL-01-S5-02`: Add boundary cases (staticmethod/classmethod/object receiver) for mixed `Base`/`Child` regeneration and lock type_id-switch absence.
15. `P2-CPP-SELFHOST-VIRTUAL-01-S5-03`: Add checks that at least two re-transpiled target cases keep semantics in `verify_selfhost_end_to_end.py`, locking no conflict between simplification and recursive calls.

`S5` finalized (2026-02-26):
- Added/updated `test/unit/test_py2cpp_codegen_issues.py` cases:
  - base-qualified method call path
  - `super().method(...)` lowering path (`Base::method(*this, ...)`)
  - staticmethod/classmethod/object-receiver boundaries with no `type_id` dispatch-switch generation
- Added selfhost e2e regression in `test/unit/test_selfhost_virtual_dispatch_regression.py` using `tools/verify_selfhost_end_to_end.py --skip-build` for:
  - `test/fixtures/core/fib.py`
  - `sample/py/17_monte_carlo_pi.py`

## Decision log summary

- 2026-02-25: Added as low-priority simplification task after virtual/override model alignment.
- 2026-02-25 to 2026-02-26: Completed S1-S5 with the key finding that class-dispatch `type_id` switch/if branches were already absent in target regions; work focused on explicit mode-table organization, non-target boundary fixation, and regression locking.
- Known blocker outside this task remains: selfhost pre-build failure in `tools/prepare_selfhost_source.py`.
