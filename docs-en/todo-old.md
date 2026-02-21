# TODO (Archive)

This file is a historical archive migrated from prior `docs/todo.md` states.
Completed items are kept for traceability. Active items were later moved to the current `docs/todo.md`.

## 2026-02-21 Completed: Pass-through Notation

1. [x] Specified and minimally implemented transpile-time pass-through notation (`# Pytra::cpp` / `# Pytra::pass`).
- [x] Added rules to `docs/spec-east.md` for placement, indentation, multi-block concatenation, and precedence against docstring-comment conversion.
- [x] Implemented EAST storage using `leading_trivia` comment text and C++ emitter expansion path.
- [x] Added minimal fixture (`test/fixtures/core/pass_through_comment.py`) and unit test proving no behavior impact in Python execution and correct C++ line emission.

## 2026-02-20 Completed: Immediate Highest Priority

1. [x] Removed unused symbols one by one.
- [x] Built candidate list from `src/py2cpp.py` and `src/runtime/cpp/pytra/built_in/py_runtime.h`.
- [x] Classified via `rg` into unused symbols and thin wrappers replaceable with direct forms.
- [x] Removed identified unused symbols and simplified profile/runtime-map loaders.
- [x] Verified with `python3 tools/check_py2cpp_transpile.py` (`checked=103 ok=103 fail=0 skipped=5`).
- [x] Committed in small units for easier rollback.
- [x] Confirmed no missing public API docs entries for removed symbols.
2. [x] Added purpose comments for classes/functions in `src/runtime/cpp/pytra/built_in/py_runtime.h`.

## 2026-02-20 Completed: `spec-import` Alignment (Top Priority)

1. [x] Aligned supported phase-1 import forms with implementation.
- [x] Supported: `import M`, `import M as A`, `from M import S`, `from M import S as A`.
- [x] Unsupported forms (`from M import *`, relative import) unified as `input_invalid` with `kind=unsupported_import_form`.
2. [x] Introduced `ImportBinding` as canonical import model.
3. [x] Unified module resolution through `resolve_module_name(raw_name, root_dir)`.
4. [x] Added `ExportTable` validation for `from M import S`.
5. [x] Fixed name-resolution priority and collision handling (`duplicate_binding`).
6. [x] Unified C++ generation to always normalize to fully qualified names.
7. [x] Enforced same `module_namespace_map` for single-file and multi-file.
8. [x] Unified import-error detail format (`kind`, `file`, `import`).
9. [x] Added minimal import acceptance matrix tests.
10. [x] Added language-agnostic import IR groundwork (`QualifiedSymbolRef`).

## 2026-02-20 Completed: `todo2`-aligned Tasks

1. [x] Kept `docs/todo2.md` MUST items satisfied (at that time).
- [x] `math` generation uses generic `py2cpp.py` flow; no module-specific hardcoded branch.
- [x] Verified `src/pytra/std/math.py -> src/runtime/cpp/pytra/std/math.h/.cpp` via `--emit-runtime-cpp`.
- [x] Rechecked Python/C++ parity for `math_extended`.
- [x] Cleared module-attr default map and unified module attribute resolution.
- [x] Removed hardcoded `png/gif` generation branches and moved to generic runtime generation flow.
- [x] Eliminated literal module-name hardcoding for `math/png/gif`.
- [x] Updated `sys.py` / `typing.py` to selfhost-convertible forms and revalidated runtime fixtures.
2. [x] Resolved duplicate management between `src/pytra/utils/std` and `src/pytra/std` (unified to `src/pytra/std`).
3. [x] Documented role of `src/runtime/cpp/pytra/built_in/`.
4. [x] Split former `containers.h` into `str/path/list/dict/set`.
5. [x] Moved `py_isdigit` / `py_isalpha` to `built_in/str.h`.
6. [x] Reassessed `src/pytra/utils/east.py` placement.
7. [x] Removed empty `src/pytra/utils/std/` directory.
8. [x] Moved `src/pytra/runtime/cpp/` to `src/hooks/cpp/` and synchronized references.
9. [x] Renamed `src/runtime/cpp/base/` to `src/runtime/cpp/pytra/built_in/` and migrated references/docs.
10. [x] Unified `--emit-runtime-cpp` outputs for `src/pytra/utils/*.py` under `src/runtime/cpp/pytra/utils/`.
11. [x] Removed direct `math/png/gif` includes from `py_runtime.h`; emit includes only when imported.
12. [x] Moved `py_runtime.h` under `src/runtime/cpp/pytra/built_in/` and removed compatibility forwarding header.
13. [x] Migrated `py_sys_*` from `py_runtime.h` to `pytra/std/sys.h/.cpp`.
14. [x] Migrated `perf_counter` from `py_runtime.h` to `pytra/std/time.h/.cpp`.

## 2026-02-20 Completed: Import Resolution Priority Queue

1. [x] Completed import-resolution phase before selfhost work.
- [x] Implemented `import`/`from import` collection and dependency graph (`--dump-deps`).
- [x] Added path resolution, duplicate detection, and cycle detection for `pytra.*` and user modules.
- [x] Removed hook-side short-name dependency for png/gif runtime modules.
- [x] Synchronized include path resolution with one-to-one import rules.
- [x] Removed tail-name fallback for `pytra.*` module resolution.
- [x] Added explicit runtime-call mapping for `pytra.std.math`.
- [x] Unified `from-import` resolution through include + call resolution path.
- [x] Synchronized runtime include paths and import normalization rules.
- [x] Added multi-file import checks in gate path.
- [x] Removed hardcoded library branches from `cpp_hooks.py` and unified through runtime-call + module-attr map.

## 2026-02-19 Completed: Multi-file (Import Enhancement) Lead Queue

1. [x] Started dependency-resolution phase for final multi-file goal.
2. [x] Implemented dependency graph generation for `import` and `from ... import ...`.
3. [x] Implemented `pytra.*` and user-module path resolution plus conflict rules.
4. [x] Migrated to module-level EAST and multi-file output (`.h/.cpp`).

## 2026-02-19 Completed: Compatibility Options (Output Shape)

1. [x] Made multi-file output default.
2. [x] Added `--single-file` for legacy single `.cpp` bundling.
3. [x] Documented migration steps in `docs/how-to-use.md`.

## 2026-02-19 Completed: C++ Multi-file Output

1. [x] Generate `.h/.cpp` per module with declaration/definition separation.
2. [x] Main module can include/link dependent modules.
3. [x] Removed duplicated runtime include/namespace setup.

## 2026-02-19 Completed: Multi-file Build/Run Verification

1. [x] Added `tools/build_multi_cpp.py`.
2. [x] Added `tools/verify_multi_file_outputs.py` and confirmed `sample/py` 16/16 (`OK=16 NG=0`).
3. [x] Added binary-equality verification for image outputs.

## 2026-02-19 Completed: Module-level EAST Preparation

1. [x] Added per-module EAST conversion for entry + dependencies.
2. [x] Added module metadata for exported symbols/import aliases.
3. [x] Added minimal shared schema for cross-module type information.

## 2026-02-19 Completed: Auto-generation Migration for `runtime/cpp/pytra/std/*`

1. [x] Migrated `runtime/cpp/pytra/std/*` (including `math`) to generated artifacts.
2. [x] Replaced handwritten `math.h/.cpp` and aligned `pathlib/time/dataclasses/sys` to generated flow.
3. [x] Passed stale checks and regressions (`check_py2cpp_transpile`, `verify_sample_outputs`).

## 2026-02-19-20 Completed: `py2cpp` Import + Runtime Placement Sync

1. [x] Implemented one-to-one mapping of import and include generation.
2. [x] Aligned C++ runtime layout with include rules.
3. [x] Added/strengthened import regression tests.
4. [x] Synchronized docs and implementation.

## 2026-02-19 Migration: TODO Reorganization (Completed Sections)

## 2026-02-19 Migration: CodeEmitter Conversion (Completed Subsections)

Working rules (step-by-step) were completed:
- [x] Apply `CodeEmitter` changes incrementally with fixture checks each step.
- [x] Check all `sample/py` conversion each step.
- [x] Fix regressions before moving to next step.

Main completed items:
1. [x] Renamed `BaseEmitter` to `CodeEmitter` and migrated references.
2. [x] Split language differences into `LanguageProfile` JSON.
3. [x] Injected profile/hook model into `CodeEmitter`.
4. [x] Added regression checks for code-emitter boundaries.
5. [x] Partially restored selfhost input path (`.json` route first).
6. [x] Resolved stdlib compile-fail set incrementally to 10/10 compile-run parity.
7. [x] Completed full auto-generation migration from handwritten `runtime/cpp/pylib` wrappers.
8. [x] Fixed local-CI equivalent flow (`tools/run_local_ci.py`).
9. [x] Aligned `unit` and `fixtures/stdlib` runtime parity coverage.

## 2026-02-20 Migration: `enum` Support (Completed)

1. [x] Added `pytra.std.enum` with minimal `Enum` / `IntEnum` / `IntFlag` compatibility.
2. [x] Added EAST handling for enum class-member syntax (`NAME = expr`).
3. [x] Added C++ lowering path for enum families and IntFlag bitwise helpers.
4. [x] Added fixtures for runtime parity.
5. [x] Updated docs.

Additional completed lines in the same period:
- [x] Implemented option system from `spec-options`.
- [x] Ran selfhost executable conversion batch for fixtures `case05..case100` and verified compile success (`CASE_TOTAL=96`, `TRANSPILE_FAIL=0`, `COMPILE_OK=96`, `COMPILE_FAIL=0`).

## Transpiler Functionality TODO (Deficiency Cleanup at the Time)

All listed items were completed:
- [x] full `AugAssign` family
- [x] exponent `**` lowering
- [x] `bytearray`/`bytes` compatibility improvements
- [x] `list.pop()` and `list.pop(index)` support
- [x] expanded `math` compatibility
- [x] GIF runtime formalization and tests
- [x] chained comparison lowering

## Additional TODO Found While Building Samples (05-14)

All listed items were completed:
- [x] correct real-division semantics for `int / int`
- [x] safer empty-container inference
- [x] improved bytes/bytearray conversion rules
- [x] entrypoint-name collision avoidance
- [x] comprehension support (including nested)
- [x] index-assignment regressions
- [x] list-method compatibility regressions

## Additional Items from `sample/py` Runtime Parity

### `py2cs.py` Side

All listed items were completed, including:
- module-call resolution (`math.sqrt` etc.)
- ignoring `from __future__ import annotations`
- reserved-word auto-rename
- range-loop temp-name and redeclaration conflicts
- large-integer literal handling

### `py2cpp.py` Side

All listed items were completed, including:
- replacing floating-sensitive sample with integer checksum sample for stable cross-language comparison
- range-loop temp-name conflict fix

## TODO Found When Adding `sample/py/15`

All listed items were completed, including:
- `int(<str>)` lowering
- string single-char index consistency
- string range-compare lowering
- C# control-flow false positive on return-path analysis
- typed empty-list generation in C#
- typed container-return call acceptance
- C++ const dict access issue
- modulo policy clarification
- long string literal escaping
- moving sample-side workarounds into transpiler logic

## Candidate Simplifications in `sample/py`

All listed simplifications were completed (built-in API usage, tuple swap, concise conditions, concise grid initialization, etc.).

## Additional TODO for Go/Java Native Conversion

All listed items were completed:
- native conversion mode migration
- fixture parity for case01-30
- `math` runtime support
- PNG and GIF runtime support

## Additional TODO for Rust

All listed items were completed:
- runtime PNG behavior and import-cleanup optimization

## Cross-language Runtime Standardization TODO

All listed items were completed:
- expanding math/pathlib parity to all targets
- documenting function-level support differences
- adding common parity fixtures for math/pathlib across targets

## EAST / CppEmitter Simplification TODO

All listed items were completed:
- lowering major builtins into EAST runtime-call forms
- dedicated nodes for `in/not in`, slice, and string-concat handling
- assignment declaration metadata and class metadata extension
- for-loop normalization split (`ForRange` / `ForEach`)

## On Hold (Go/Java Frozen Until EAST Migration)

Historical hold-items at that time:
- keep stronger static typing in Go/Java where annotation exists
- avoid unnecessary `any`/`Object` fallback in annotations and byte-sequence paths
- stabilize typed container operations in generated code

Subsequent notes show partial progress was made, but this section remains as historical hold context.

## EAST C++ Readability Improvement TODO

All listed items were completed:
- reduced redundant parentheses
- removed meaningless expression statements
- normalized for-step output (`++i/--i` where applicable)

## EAST `py2cpp` Sample Support TODO (Completed)

All listed items were completed:
- append lowering to `push_back`
- `perf_counter` runtime mapping
- removing raw `range` calls before backend
- `min`/`max` type-consistent output
- tuple-destructure declaration fixes
- full re-run of `sample/py` 16 cases

## self_hosted AST/Parser Phased Migration TODO

### Case-order migration (from `test/fixtures/case01`)

- [x] Completed migration and parity checks through case10 and onward class/loop/extended case groups.

### Switch-complete conditions

- Historical placeholder section retained from old plan.

## Image-output Mismatch Investigation Base TODO (2026-02-17)
## Migrated from `docs/todo.md` (2026-02-18)

Large block completed, including:
- expression/precedence parity checks
- docstring/comment handling cleanup
- parser backend unification to selfhost
- selfhost tokenizer/parser core build-out
- comment carryover and leading-comment emission
- runtime image parity automation
- reference-semantics policy for user classes
- class storage-strategy split (`rc<T>` vs value type) with acceptance tests
- selfhost goal fixation and parser signature support expansions
- f-string handling in selfhost parser

## Migration: 2026-02-18 (Completed from `todo.md`)

### Any/object policy migration (completed)

- [x] Introduced `object = rc<PyObj>`.
- [x] Implemented object boxing/unboxing helpers.
- [x] Unified `None` checks and object stringification.

### `py2cpp` Any lowering (completed)

- [x] Type resolution and container mapping for `Any/object`.
- [x] Boxing/unboxing generation.
- [x] `is None` handling via `py_is_none`.

### selfhost recovery (partially completed in this section)

- [x] Regenerated selfhost C++ and measured compile errors at that stage.

### comprehension/lambda regressions (completed)

- [x] Added broad fixtures and runtime regression checks.

### documentation update (completed)

- [x] Updated spec/docs/readme around Any/object policy.

## Migration: 2026-02-18 (Completed Group 2)

Completed items included:
- selfhost parser fixes for parse failures
- object-receiver method-call restrictions
- additional `super()` regression coverage
- further EAST-side lowering for call normalization
- emitter utility centralization in shared base

## Migration: 2026-02-18 (Completed Group 3)

Completed items included:
- no-value `return` support in selfhost parser
- additional base-emitter helper paths
- optional-dict runtime helper overloads

## Migration: 2026-02-18 (C++ runtime wrapper alignment)

Completed items included:
- migration from STL inheritance to wrapper composition for runtime containers/strings
- preserving readable `for (str c : s)` generation
- syncing docs with wrapper-based implementation

## Migration: 2026-02-18 (selfhost recovery 1-3)

Completed items included:
- unifying object-to-container conversions through typed helpers
- disambiguating dict-get defaults through typed helpers
- harmonizing Any/dict boundaries across key emitter paths

## Migration: 2026-02-18 (Completed Group 4)

### Image-runtime unification (Python source of truth)

Completed:
- moved PNG/GIF C++ runtime generation toward transpiled output from Python source modules
- expanded parser support needed for this route
- standardized binary-identity acceptance policy
- documented optimization policy boundaries

### Import enhancements

Completed:
- import and alias resolution across EAST + `py2cpp`
- regression coverage for runtime imports
- spec updates for supported import range

### selfhost recovery (completed items)

Completed:
- automated source preparation (`tools/prepare_selfhost_source.py`)
- restored selfhost conversion path to green

## Migration Snapshot: 2026-02-21 (before `todo.md` reorganization)

The following section was preserved from the old TODO snapshot to keep historical progression.

# TODO (Unfinished Items Only at That Snapshot)

## Highest Priority (Added 2026-02-20: reflected `todo2` priority)

The checklist under this heading is now marked complete in this archive snapshot:
- [x] runtime-cpp regeneration for `src/pytra/std/*.py`
- [x] remaining `extended_runtime` failures
- [x] `enumerate(start)` expansion and regression lock
- [x] comprehension/lambda regression expansion
- [x] root-cause and recurrence test for stray `import_pytra_runtime_png.png`

## Highest Priority (Added 2026-02-20: `py2cpp` codegen issues)

Completed in this archive snapshot:
- [x] fixed branch-first assignment scope bug in generated C++
- [x] added dedicated issue-regression tests
- [x] fixed optional-tuple destructure typing path
- [x] verified with targeted unittest suite and runtime regeneration compile checks

## Priority Policy (Updated 2026-02-19)

Historical policy:
- complete import resolution first
- run selfhost work after import-resolution stabilization

## Near-term Execution Queue (Detailed)

1. [ ] Phased recovery of selfhost `.py` path.
- [x] dependency inventory and split of safe-vs-split candidates
- [x] bridge route (`tools/selfhost_transpile.py`) for `.py -> EAST JSON -> selfhost`
- [x] recovery for representative samples (`sample/py/01_mandelbrot.py`)
- [x] runtime module path expansion for `pytra.compiler.*`
- [x] compileability of generated `runtime/cpp/pytra/compiler/east_parts/core.cpp`
- [x] restored pure selfhost `.py -> -o` path
- [x] restored `.json` path and parity checks (`mismatches=0` in default bridge cases)
- [x] synchronized error categories and `--help` behavior
- [x] re-enabled build gate to green after removing key blockers
- [x] confirmed selfhost direct conversion + compile/run parity on representative sample
3. [ ] Resume hook migration under selfhost-safe constraints.
- [x] defined constrained hook API without selfhost-hostile annotation patterns
- [x] migrated initial `png/gif` hook logic to `cpp_hooks.py`
- [x] enforced dual gate (`build_selfhost.py` + `check_py2cpp_transpile.py`)

## CodeEmitter Conversion (JSON + Hooks)

4. [ ] Implement hook injection (`EmitterHooks`).
- [x] defined minimal hook surfaces
- [ ] further split remaining large `render_expr` branches (partly completed)
- [x] delegated many expr kinds to hook entry points
- [x] split major statement emit paths into helper/template forms
- [ ] continue moving profile-hard cases to hooks while reducing conditionals in `py2cpp.py`
- [x] separated C++ hooks into `src/hooks/cpp/hooks/cpp_hooks.py`

## `py2cpp` Reduction (Line-count reduction)

1. [ ] Continue moving remaining logic from `src/py2cpp.py` to `CodeEmitter` helpers.
- [x] fixed measurable target and baseline
- [ ] continue splitting remaining call/arith/compare/type-conversion branches (partly completed)
- [x] moved many builtin/runtime-call branches into dedicated helpers
- [x] shrank `render_expr(Call)` to helper-centric flow
- [ ] continue moving `Constant`/`Attribute` common rendering to `CodeEmitter`
- [ ] continue template-izing control-structure output and class/function body scaffolding
2. [ ] Continue unused-function cleanup.
- [x] removed multiple zero-reference helpers and wrappers.

## selfhost Recovery (Later Stage)

1. [ ] Continue hardening Any/dict boundaries under selfhost.
- [x] stabilized many helper and kind-resolution paths
- [x] added boundary regression tests
- [x] normalized hook-container shape for selfhost stability
- [x] reduced default-argument object coercion with typed helpers
- [ ] continue remaining boundary cleanup work
2. [ ] Minimize unnecessary `object` fallback in `cpp_type` and expression rendering.
- [x] improved optional-union handling (`std::optional<T>` preference)
- [ ] split necessary vs unnecessary `Any -> object` paths
- [ ] clean up default-argument paths requiring object coercion
- [ ] reduce `nullopt` default overuse in typed contexts
- [ ] continue hotspot-guided removal of `std::any` routes
3. [ ] Reduce remaining selfhost compile/link/runtime issues to zero on full path.
- [x] achieved staged compile-error reductions, then compile error `0`
- [x] restored minimal diff-gate success for representative cases
- [ ] continue full-path stability work beyond representative subset
4. [ ] Continue selfhost source preparation cleanup in `tools/prepare_selfhost_source.py`.
- [x] restored `.py` and `.json` input handling in selfhost execution path
- [x] restored build to green after safe-path fixes
- [ ] continue removing temporary selfhost-specific stubs
5. [x] Automated conversion-diff comparison between Python and selfhost versions.

## Multi-file Structure (Final Goal)

1. [x] Added dependency-resolution phase.
- [x] graph building for `import` and `from ... import ...`
- [x] unified cycle errors as `input_invalid`
- [x] `--dump-deps` visualization path

## Recent Notes

Historical notes preserved in this archive reported:
- major error causes around Any/object/optional-dict boundaries
- progressive hotspot reductions by helper normalization
- build and diff script additions (`summarize_selfhost_errors`, `selfhost_error_hotspots`, `run_local_ci`)
- evolution from temporary `.py` bridge operation to direct selfhost `.py`/`.json` handling
- periodic confirmations that representative `check_selfhost_cpp_diff` cases reached `mismatches=0`

