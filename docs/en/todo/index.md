# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-21 (Archived P0-1–P0-10, P1 pipeline stage separation, P4 vararg desugaring)

## Context Operation Rules

- Every task must include an `ID` and a context file (`docs/ja/plans/*.md`).
- To override priority, issue chat instructions in the format of `docs/ja/plans/instruction-template.md`; do not use `todo2.md`.
- The active target is fixed to the highest-priority unfinished ID (smallest `P<number>`, and the first one from the top when priorities are equal); do not move to lower priorities unless there is an explicit override instruction.
- If even one `P0` remains unfinished, do not start `P1` or lower.
- Before starting, check `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress memos and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memos in `docs/ja/todo/index.md` to a one-line summary only; details such as decisions and verification logs must be recorded in the `Decision log` of the context file (`docs/ja/plans/*.md`).
- If one `ID` is too large, you may split it into child tasks in `-S1` / `-S2` format in the context file, but keep the parent checkbox open until the parent `ID` is completed.
- If uncommitted changes remain due to interruptions, do not start a different `ID` until you complete the same `ID` or revert the diff.
- When updating `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and verify that each progress `ID` added in the diff matches the highest-priority unfinished `ID` or one of its child IDs.
- Append in-progress decisions to the context file `Decision log`.
- For temporary output, use existing `out/` or `/tmp` only when necessary, and do not add new temporary folders under the repository root.

## Notes

- This file keeps unfinished tasks only.
- Completed tasks are moved to history via `docs/ja/todo/archive/index.md`.
- `docs/ja/todo/archive/index.md` keeps only the index, and the history body is stored by date in `docs/ja/todo/archive/YYYYMMDD.md`.

## Unfinished Tasks

### P0: C++ Generated Runtime Header Generation Pipeline

#### P0-11: PowerShell Native Emitter Execution Parity

Context: [docs/ja/plans/p0-powershell-native-emitter-execution-parity.md](../../ja/plans/p0-powershell-native-emitter-execution-parity.md)

1. [ ] [ID: P0-PS-EXEC-PARITY-01-S1] Do not exclude the `self` parameter from FunctionDef; keep it as `$self` and pass it as the first argument when calling class methods.
2. [ ] [ID: P0-PS-EXEC-PARITY-01-S2] Map `bytearray`, `bytes`, `enumerate`, `sorted`, `reversed`, `zip` etc. to `__pytra_*` runtime functions; add any missing runtime functions.
3. [ ] [ID: P0-PS-EXEC-PARITY-01-S3] Translate stdlib Attribute Calls such as `math.sqrt` → `[Math]::Sqrt` directly to PowerShell syntax.
4. [ ] [ID: P0-PS-EXEC-PARITY-01-S4] When a tuple target appears on the left-hand side of an Assign, emit a temporary variable expansion.
5. [ ] [ID: P0-PS-EXEC-PARITY-01-S5] When the func of a Call is a class name, emit it as a constructor function call.
6. [ ] [ID: P0-PS-EXEC-PARITY-01-S6] Add pwsh execution tests to `test/unit/toolchain/emit/powershell/test_py2ps_smoke.py` and verify successful execution of major fixtures.

### P1: Pipeline Stage Separation — Decouple compile / link / emit

#### P1-2: Remove backend_registry Dependency

Context: [docs/ja/plans/p1-backend-registry-decoupling.md](../../ja/plans/p1-backend-registry-decoupling.md)

1. [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S1] Change the C++ emit path in `py2x.py` to invoke `east2cpp.py` as a subprocess and remove the `backend_registry` import.
2. [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S2] Change the non-C++ emit path in `py2x.py` to invoke `east2x.py` as a subprocess.
3. [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S3] Refactor `py2x-selfhost.py` to remove the `backend_registry_static` import; directly import `toolchain.emit.cpp.emitter` for C++ emit only.
4. [ ] [ID: P1-BACKEND-REGISTRY-DECOUPLING-01-S4] Verify that non-C++ backends are not included in the import graph during the compile+link stage of selfhost multi-module.

### P5: py_runtime.h Shrink

#### P5-1: Remove py_is_type Dead Code

Context: [docs/ja/plans/p5-cpp-py-is-type-dead-code-remove.md](../../ja/plans/p5-cpp-py-is-type-dead-code-remove.md)

1. [x] [ID: P5-CPP-PY-IS-TYPE-DEAD-CODE-REMOVE-01] Remove `py_is_dict` / `py_is_list` / `py_is_set` / `py_is_str` / `py_is_bool` / `py_is_int` / `py_is_float` from `py_runtime.h`. The emitter has already migrated to the `PYTRA_TID_*` + `py_runtime_value_isinstance` system; these functions are dead code.
- Progress: Completed. 7 functions removed, 1 test fixed. fixture/sample pass, selfhost mismatches=0.

#### P5-2: FloorDiv / Mod EAST3 IR Node

Context: [docs/ja/plans/p5-east3-floordiv-mod-node.md](../../ja/plans/p5-east3-floordiv-mod-node.md)

2. [x] [ID: P5-EAST3-FLOORDIV-MOD-NODE-01] Convert `py_floordiv` / `py_mod` to C++ inline emit via EAST3 IR nodes and remove from `py_runtime.h`. Lays the groundwork for each language backend to generate floor-division and modulo natively.
- Progress: Completed. py_div/floordiv/mod moved to scalar_ops.h. py_div inlined for arithmetic types, fallback kept for object boundary. mismatches=0. cpp 0.581.1.

### P6: py_runtime.h Shrink / Multi-language Support

#### P6-1: Fix C++ Emitter List-Mutation IR Bypass

Context: [docs/ja/plans/p6-cpp-list-mut-ir-bypass-fix.md](../../ja/plans/p6-cpp-list-mut-ir-bypass-fix.md)

1. [x] [ID: P6-CPP-LIST-MUT-IR-BYPASS-FIX-01] Route all `py_list_*_mut()` direct-emit paths in `cpp_emitter.py` through IR nodes (ListAppend, etc.) and remove the 6 functions from `py_runtime.h`.
- Progress: Completed. 6 functions moved to list_ops.h; emitter updated to direct method calls (.append() etc.); generated C++ files updated. mismatches=0. cpp 0.581.2.

#### P6-2: py_len / py_slice EAST3 IR Nodes

Context: [docs/ja/plans/p6-east3-len-slice-node.md](../../ja/plans/p6-east3-len-slice-node.md)

2. [x] [ID: P6-EAST3-LEN-SLICE-NODE-01] Add EAST3 IR nodes for `py_len` / `py_slice`, update the C++ emitter to generate inline expressions, and remove both from `py_runtime.h`.
- Progress: Completed. py_len moved to base_ops.h; py_slice str variant renamed to py_str_slice (same file); list variants removed (emitter emits py_list_slice_copy directly). truthy_len_expr override generates .empty() check. selfhost mismatches=0. cpp 0.581.3.

#### P6-2a: list/dict .clear() BuiltinCall Lowering

Context: [docs/ja/plans/p6-cpp-emit-list-dict-clear.md](../../ja/plans/p6-cpp-emit-list-dict-clear.md)

3. [ ] [ID: P6-CPP-EMIT-LIST-DICT-CLEAR-01] Add BuiltinCall lowering for `list[T].clear()` / `dict[K,V].clear()` to the C++ emitter so it emits `v.clear()`. Unblocks `type_id.py` regeneration.

#### P6-2b: General Union Type → std::variant / Multi-language Tagged Union

Context: [docs/ja/plans/p6-east3-general-union-variant.md](../../ja/plans/p6-east3-general-union-variant.md)

4. [ ] [ID: P6-EAST3-GENERAL-UNION-VARIANT-01] Convert general union types (`str | bool | None` etc.) to `std::variant<...>` in C++ emission. Unblocks `argparse.py` / `assertions.py` regeneration.

#### P6-3: Inline emit for py_is_none

Context: [docs/ja/plans/p6-east3-is-none-inline.md](../../ja/plans/p6-east3-is-none-inline.md)

5. [ ] [ID: P6-EAST3-IS-NONE-INLINE-01] Replace `py_is_none(v)` with type-based inline expressions (`!v.has_value()` / `!v` / `false`) and remove from `py_runtime.h`.

#### P6-4: Inline emit for py_to family

Context: [docs/ja/plans/p6-east3-py-to-inline.md](../../ja/plans/p6-east3-py-to-inline.md)

6. [ ] [ID: P6-EAST3-PY-TO-INLINE-01] Replace `py_to<T>` / `py_to_int64` / `py_to_float64` with `static_cast` / `std::stoll` etc. for type-certain cases and remove from `py_runtime.h`.

#### P6-5: Inline emit for py_to_string

Context: [docs/ja/plans/p6-east3-py-to-string-inline.md](../../ja/plans/p6-east3-py-to-string-inline.md)

7. [ ] [ID: P6-EAST3-PY-TO-STRING-INLINE-01] Replace `py_to_string(v)` with `std::to_string` / identity etc. for type-certain cases and remove from `py_runtime.h`.

#### P6-6: Inline emit for py_at (list/rc variants)

Context: [docs/ja/plans/p6-east3-py-at-inline.md](../../ja/plans/p6-east3-py-at-inline.md)

8. [ ] [ID: P6-EAST3-PY-AT-INLINE-01] Unify `py_at(list_or_rc, idx)` emit to direct `py_list_at_ref` emit and remove the list/rc variants of `py_at` from `py_runtime.h`.

#### P6-7: Eliminate object Fallback for Any-mixed Unions / Expressions

Context: [docs/ja/plans/p6-cpp-any-union-object-fallback.md](../../ja/plans/p6-cpp-any-union-object-fallback.md)

9. [ ] [ID: P6-CPP-ANY-UNION-OBJECT-FALLBACK-01] Eliminate silent `object` returns for dynamic unions (`int | Any` etc.) and Any-like binary operations (type_bridge.py L591, cpp_emitter.py L471/L2082).

#### P6-8: Eliminate object Fallback for unknown / Empty Types

Context: [docs/ja/plans/p6-cpp-unknown-type-object-fallback.md](../../ja/plans/p6-cpp-unknown-type-object-fallback.md)

10. [ ] [ID: P6-CPP-UNKNOWN-TYPE-OBJECT-FALLBACK-01] Convert silent `object` fallbacks for `"unknown"` / empty type strings (type_bridge.py L668, header_builder.py L1373) into compile errors.

#### P6-9: Eliminate object Fallback for if/else Branch Type Merge Failures

Context: [docs/ja/plans/p6-cpp-branch-merge-object-fallback.md](../../ja/plans/p6-cpp-branch-merge-object-fallback.md)

11. [ ] [ID: P6-CPP-BRANCH-MERGE-OBJECT-FALLBACK-01] Replace `object` fallback on if/else branch type merge failure (cpp_emitter.py L2101-2105) with `std::variant` or an explicit error.

#### P6-10: Eliminate object Fallback for Unknown For-loop Variable Types

Context: [docs/ja/plans/p6-cpp-for-loop-type-object-fallback.md](../../ja/plans/p6-cpp-for-loop-type-object-fallback.md)

12. [ ] [ID: P6-CPP-FOR-LOOP-TYPE-OBJECT-FALLBACK-01] Eliminate `object` fallback at 5 locations in for-loop variable type resolution (stmt.py L1135/1161/1217/1278/1865) via improved type inference or explicit errors.

#### P6-11: Eliminate object Fallback for Global Variable Type Inference Failures

Context: [docs/ja/plans/p6-cpp-global-var-type-object-fallback.md](../../ja/plans/p6-cpp-global-var-type-object-fallback.md)

13. [ ] [ID: P6-CPP-GLOBAL-VAR-TYPE-OBJECT-FALLBACK-01] Convert silent `object` fallback on global variable type inference failure (module.py L1155) into a compile error requiring explicit annotation.

### P7: Selfhost Full Independence

#### P7-1: Complete deletion of native/compiler/

Context: [docs/ja/plans/p7-selfhost-native-compiler-elim.md](../../ja/plans/p7-selfhost-native-compiler-elim.md)

1. [x] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S1] Unify the selfhost build pipeline to EAST3 JSON input only; remove the `.py` shell-out path from `transpile_cli.cpp`.
2. [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S2] Make `toolchain/emit/cpp/cli.py` (emitter) transpilable to C++ and remove the `emit_source_typed` shell-out. → Prerequisite: P7-SELFHOST-MULTIMOD-TRANSPILE-01.
3. [ ] [ID: P7-SELFHOST-NATIVE-COMPILER-ELIM-01-S3] Confirm zero shell-outs, delete `src/runtime/cpp/compiler/`, and redirect `generated/compiler/` includes to generated C++ directly.

#### P7-2: Selfhost Multi-module Transpile Infrastructure (prerequisite for S2)

Context: [docs/ja/plans/p7-selfhost-multimodule-transpile.md](../../ja/plans/p7-selfhost-multimodule-transpile.md)

1. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S1] Audit emitter modules (`src/toolchain/emit/cpp/emitter/*.py`) for selfhost constraint violations and enumerate them. → Details in context file decision log. Blockers: 4 dynamic dispatch issues.
1a. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-01] Implement `relative_to` / `with_suffix` on `pytra.std.pathlib.Path`; migrate emitter's `from pathlib import Path`.
1b. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-02] Implement `compile` / `Pattern` in `pytra.std.re`; migrate optimizer's `import re`.
1c. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-03] Migrate `multifile_writer.py`'s `import os` to `pytra.std`.
1d. [x] [ID: P7-SELFHOST-CONSTRAINT-FIX-04] Replace CppEmitter's dynamic mixin injection (`_attach_cpp_emitter_helper_methods` setattr/__dict__) with EAST3 mixin expansion via multiple inheritance. Remove `install_py2cpp_runtime_symbols` globals() injection.
2. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S2] Extend `tools/build_selfhost.py` to a multi-module transpile pipeline (compile → link). → `--multi-module` flag runs compile→link→emit via py2x.py. All 150 modules compiled to EAST3 successfully. Parser fixes (typing no-op, dict string-key `:`, multi-arg subscript). Object receiver fixes across the dependency chain (40+ files).
3. [ ] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S3] Call `emit_cpp_from_east` directly from `py2x-selfhost.py` and remove the `emit_source_typed` shell-out from `backend_registry_static.cpp`.
4. [x] [ID: P7-SELFHOST-MULTIMOD-TRANSPILE-01-S4] Investigate and fix missing symbol resolution for `from toolchain.compiler.transpile_cli import make_user_error` etc. in the linker. → Implemented wildcard re-export propagation in `module_export_table`. `from X import *` re-exports now reflected in export table. Link of 151 modules succeeds.
