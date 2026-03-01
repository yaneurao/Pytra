# P1: C++ `list` Migration to the PyObj/RC Model (Phased Rollout)

Last updated: 2026-02-28

Related TODO:
- `ID: P1-LIST-PYOBJ-MIG-01` in `docs/ja/todo/index.md`
- Dependency: `ID: P1-EAST3-NONESCAPE-IPA-01` (interprocedural non-escape annotations)

Background:
- In the current C++ runtime, `list<T>` is a value model as a `std::vector<T>` wrapper and is not managed as `rc<PyObj>`.
- At the `Any/object` boundary, values are boxed into `PyListObj(list<object>)`, but statically typed paths still center on value-copy semantics, leaving a gap from Python reference semantics.
- Per user policy, we should move `list` toward the PyObj/RC model and then reduce only non-escape paths through RAII/stack optimization.

Objective:
- Migrate `list` to a reference model that is PyObj/RC-managed by default.
- In early migration, prioritize fail-closed behavior and compatibility, and manage regression surface with phased rollout (dual model).
- Ultimately connect to `EAST3 non-escape` annotations and establish groundwork so only local non-escape paths can be stack/RAII-lowered.

Scope:
- C++ runtime:
  - `src/runtime/cpp/pytra-core/built_in/list.h`
  - `src/runtime/cpp/pytra-core/built_in/py_runtime.h`
  - `dict.h`/`set.h` as needed (only where they depend on `list`)
- C++ backend:
  - `src/hooks/cpp/emitter/*`
  - `src/hooks/cpp/optimizer/*` (when adding RAII reduction passes)
- EAST3 optimizer:
  - Use annotations from `P1-EAST3-NONESCAPE-IPA-01`
- Tests/validation:
  - `test/unit/test_cpp_runtime_*`
  - `test/unit/test_py2cpp_*`
  - `tools/check_py2cpp_transpile.py`
  - `tools/runtime_parity_check.py`

Out of scope:
- Simultaneous PyObj migration of `str/dict/set` (not covered by this task)
- Simultaneous expansion to all backends
- Aggressive optimizations (replacements without semantics-preservation evidence)

Design Policy:
- Policy A (early migration): dual model
  - Do not immediately remove the old value model for `list`; allow backend option switch between `value` and `pyobj`.
  - Switch default in stages (keep `value` first, then change to `pyobj` after regression lock-in).
- Policy B (safe side): fail-closed
  - Keep `pyobj` (no stack lowering) for unconvertible/unknown types or external-call-involved paths.
- Policy C (separation of responsibilities):
  - EAST3 goes only up to "non-escape judgment annotations."
  - Actual `pyobj -> stack` replacement is applied on the C++ optimizer/emitter side.

## Phase Plan

### Phase 0: Lock specification and visualize gaps

- Document the `list` reference-semantics contract (assignment alias / argument sharing / return-value sharing).
- Inventory locations in existing fixtures/samples that assume value-copy behavior.
- Add alias-expected cases (`a = b; b.append(...)`) as regression tests and explicitly fix current gaps.

### Phase 1: Introduce PyObj list model in runtime (compatible coexistence)

- Add PyObj-side `list` implementation (template or wrapper) so RC can manage it.
- Connect `make_object` / `obj_to_*` / iterable hooks to the new list model.
- Keep minimum interconversion with old model to suppress compile breaks during staged switching.

### Phase 2: Switch backend list generation via model switch

- Unify C++ emitter type output/literals/append-pop/for-range through model switch.
- Add `--cpp-list-model {value,pyobj}` (tentative name) so generated artifacts can be compared explicitly.
- Establish compile/run/parity of the `pyobj` model in representative cases including `sample/18`.

### Phase 3: Connect with non-escape annotations (RAII reduction)

- Pass `meta` annotations from `P1-EAST3-NONESCAPE-IPA-01` to the C++ side.
- Add passes that reduce only provably non-escape local lists to stack/RAII.
- Always keep heap (pyobj) when mixed with unknown/external/dynamic calls.

### Phase 4: Default switch and cleanup

- After passing regressions (transpile/smoke/parity/perf), switch default to `pyobj`.
- Remove temporary compatibility code for old value model in stages (with rollback window).
- Sync operation differences into docs/spec/how-to-use.

#### S4-03 Finalized: Removal plan for old `value` compatibility code

- Compatibility targets (removal candidates)
  - C++ emitter branches for `cpp_list_model == "value"` (value-specific branches in type rendering/collection ops/for lowering)
  - Runtime value-side bridges such as `list<T>(object)` / `obj_to_list<T>`
  - `py2cpp` rollback option (`--cpp-list-model value`)
- Removal stages
  - Stage A (current): default is `pyobj`; keep `value` only for rollback.
  - Stage B (next ID): re-measure actual use of `value` branches on `sample + fixture + selfhost`, and confirm no/low usage.
  - Stage C (next ID): remove value-specific emitter branches in stages and reduce to single `pyobj` path.
  - Stage D (next ID): minimize runtime bridges (`list<T>(object)` etc.) and delete unnecessary paths.
  - Stage E (next ID): remove `--cpp-list-model value` and update CLI contract to fixed `pyobj`.
- Conditions for filing separate IDs (fail-closed)
  - If removal of `value` causes regression in any of `check_py2cpp_transpile` / `runtime_parity_check --targets cpp` / selfhost.
  - If simultaneous impact spreads beyond `list` (e.g., `dict/set/tuple`) and exceeds this ID's acceptance scope.
  - If existing user paths still require rollback and explicit phased deprecation period is needed.

## Acceptance Criteria

- `check_py2cpp_transpile` and C++ smoke pass under the `pyobj` list model.
- Alias-expected cases match Python.
- `runtime_parity_check --targets cpp` on major `sample/py` cases is non-regressive.
- Unknown non-escape paths are not stack-lowered and remain fail-closed.
- Diff-comparison logs for `value` / `pyobj` are available, with enough evidence for default-switch decisions.

## Risks and Mitigations

- Risk: Frequent compile breaks from chained type-signature changes.
  - Mitigation: dual model + switch flag + small-batch migration.
- Risk: Performance degradation from increased RC usage.
  - Mitigation: include limited RAII reduction using non-escape annotations in the same plan.
- Risk: Dual implementation between `Any/object` boundary and statically typed paths.
  - Mitigation: consolidate list model-switch entry into emitter base helpers to keep a single branch point.

## Validation Commands (planned)

- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2cpp_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_cpp_runtime_*.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_*.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp --all-samples --ignore-unstable-stdout`

Decision Log:
- 2026-02-28: Per user instruction, finalized policy to prioritize migrating `list` alone to the PyObj/RC model before expanding to `str/dict/set`.
- 2026-02-28: Adopted staged switching based on `value/pyobj` dual model to reduce migration risk.
- 2026-02-28: Added `docs/ja/spec/spec-cpp-list-reference-semantics.md` and documented current `value model` contract (copy assignment) and target `pyobj model` contract (shared aliases).
- 2026-02-28: Added alias-expected fixture `test/fixtures/collections/list_alias_shared_mutation.py` and fixed the gap by confirming `output mismatch` with `python3 tools/runtime_parity_check.py --case-root fixture --targets cpp list_alias_shared_mutation` (Python=`True`, C++=`False`).
- 2026-02-28: AST-scanned `sample/py` + `test/fixtures` for `name = name` assignments with list type annotations, and found only one candidate at this point: `test/fixtures/collections/list_alias_shared_mutation.py:7 (b = a)`.
- 2026-02-28: Extended runtime `PyListIterObj` to owner-list reference mode, and changed `PyListObj::py_iter_or_raise()` to return an iterator that holds the owner entity instead of a snapshot.
- 2026-02-28: Added regression in `test_cpp_runtime_iterable.py` where iterator observes elements appended by `py_append` during iteration, and confirmed runtime compile-run tests pass for both `test_cpp_runtime_iterable.py` and `test_cpp_runtime_boxing.py`.
- 2026-02-28: Added `obj_to_list_obj()` to runtime, consolidated `obj_to_list_ptr` / `py_append` through PyListObj acquisition helpers, and added `make_object(const list<object>&)` / `make_object(list<object>&&)` for direct `list<object>` boxing path.
- 2026-02-28: Added `obj_to_list_obj` regression in `test_cpp_runtime_boxing.py` and confirmed runtime compile-run tests pass.
- 2026-02-28: Fixed old value-model compatibility bridge behavior in `test_cpp_runtime_boxing.py` (`list<int64> legacy_list = list<int64>(as_list)` works and PyListObj-side size remains unchanged).
- 2026-02-28: Added list-model regressions to runtime unit tests (owner-linked iterator / `obj_to_list_obj` / legacy bridge) and confirmed both `test_cpp_runtime_iterable.py` and `test_cpp_runtime_boxing.py` pass.
- 2026-02-28: Added `cpp_list_model` (`value|pyobj`) in C++ emitter and consolidated `_cpp_type_text(list[...])` through model switch. In `pyobj` mode, list types render as `object`.
- 2026-02-28: Added list model switch regression in `test_cpp_type.py`, and confirmed non-regression with `python3 tools/check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`).
- 2026-02-28: Added runtime helpers (`py_extend/py_pop/py_clear/py_reverse/py_sort`) for `pyobj` list mode, and switched emitter `ListAppend/ListExtend/ListPop/ListClear/ListReverse/ListSort` to object runtime calls.
- 2026-02-28: Added branches that render list literals as `make_object(list<...>{...})`, `list(...)` ctor `pyobj` path, and list indexing in `Subscript` via `py_at(...)`.
- 2026-02-28: Added `pyobj` list-mode regressions to `test_py2cpp_codegen_issues.py` and confirmed pass of `test_cpp_runtime_iterable.py` / `test_py2cpp_codegen_issues.py` / `check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`).
- 2026-02-28: Updated for-iteration mode selection to fail-closed choose `runtime_protocol` for `list[...]` types when `cpp_list_model=pyobj`, and made list comprehensions valid via `object` return + `make_object(__out)`. Confirmed pass of `test_py2cpp_codegen_issues.py` (61 tests) and `check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`).
- 2026-02-28: In `ForCore(RuntimeIterForPlan)`, disabled static typed iteration when `cpp_list_model=pyobj` and `iter_expr` is `list[...]`, forcing `py_dyn_range` + runtime unbox. Also added path to unbox `py_at` results for `Subscript(list)` to expression type, and changed empty list initialization in `AnnAssign` to `make_object(list<object>{})`.
- 2026-02-28: Added runtime `py_enumerate(const object&)` / `py_enumerate(const object&, int64)` and normalized runtime iteration for `pyobj` list model to indexable `list<object>`. Confirmed pass of `test_py2cpp_list_pyobj_model.py` (2 tests: `sample/18` + `list_alias_shared_mutation`) / `test_py2cpp_codegen_issues.py` (61 tests) / `check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`).
- 2026-02-28: Added non-escape handoff state to C++ emitter (`non_escape_summary_map` / `function_non_escape_summary_map` / `current_function_non_escape_summary` / `non_escape_callsite_records`) and implemented collection of `meta.non_escape_summary`, `FunctionDef.meta.escape_summary`, and `Call.meta.non_escape_callsite` on the C++ side. Confirmed pass of `test_cpp_non_escape_bridge.py` (2 tests) / `test_py2cpp_codegen_issues.py` (61 tests) / `check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`).
- 2026-02-28: Added fail-closed reduction path so only non-escape empty local lists (`AnnAssign list[...] = []`) reduce to value-model when `cpp_list_model=pyobj`. Prioritize escape decisions from `Call.meta.non_escape_callsite`; unknown/external calls are excluded from reduction. Added two regressions in `test_py2cpp_codegen_issues.py` for successful reduction/escape retention, and confirmed non-regression with `test_cpp_non_escape_bridge.py` (2), `test_py2cpp_list_pyobj_model.py` (2), `test_py2cpp_codegen_issues.py` (63), and `check_py2cpp_transpile.py` (`checked=134 ok=134 fail=0 skipped=6`).
- 2026-02-28: Added fail-closed fixed regressions (2 cases) in `test_py2cpp_codegen_issues.py` for mixed unknown/external/dynamic calls, confirming local lists do not stack-reduce under `cpp_list_model=pyobj` (`object xs` + `py_append` retained). Confirmed pass in `test_py2cpp_codegen_issues.py` (65 tests).
- 2026-02-28: Added `tools/benchmark_cpp_list_models.py` to compare transpile+compile+run (`warmup=1`,`repeat=3`) between `value` and `pyobj`. In measured `work/logs/cpp_list_model_compare_20260228_all.json`, success was 6/18 (`01,02,03,04,17,18`), failure 12/18 (`05..16`), and medians on successful cases were `elapsed=0.999x` / `bin=1.000x` / `src=1.000x` (pyobj/value). Diffs concentrated in `18` (`elapsed=1.954x`,`changed_lines=344`), so default switch was judged "not yet" (continue to S4-02).
- 2026-02-28: Added `--cpp-list-model {value,pyobj}` to `py2cpp`, propagating through both single-file and multi-file paths to `CppEmitter.cpp_list_model`. Added regressions for `parse_py2cpp_argv` (`test_py2cpp_features.py`, 1) and API override (`test_py2cpp_codegen_issues.py`, 66), confirmed `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py --cpp-list-model pyobj` outputs `py_append/make_object(list<object>{})`, and confirmed `check_py2cpp_transpile.py` passes (`checked=134 ok=134 fail=0 skipped=6`).
- 2026-02-28: To resolve compile blocker for nested index assignment in `pyobj` (`object(...)[x] = ...`), added runtime helper `py_set_at` and lower for `Assign(Subscript)`. Added nested-subscript assignment regression in `test_py2cpp_codegen_issues.py`; `check_py2cpp_transpile.py` passed. Re-benchmark (`work/logs/cpp_list_model_compare_20260228_cases07_09_after_setat.json`) showed `07/08/09` moved from compile fail to runtime fail (`setitem on non-list object`), identifying next blocker as row-build/boxing path correction.
- 2026-02-28: In `pyobj`, when list repeat was emitted as `py_repeat(make_object(list<int64>{0}), w)`, rows in `07/08/09` stopped being list objects and hit `setitem on non-list object`. Added fix in `operator.py` to explicitly unbox list-repeat input to `list<T>(object_expr)` when `cpp_list_model=pyobj`. Added regression `test_pyobj_list_model_list_repeat_unboxes_to_value_list_before_py_repeat` in `test_py2cpp_codegen_issues.py` and confirmed 68 tests pass.
- 2026-02-28: After the above fix, `07/08/09` failed with `frame size mismatch`; fixed unsupported arithmetic-type handling for `uint8` in runtime `py_object_try_cast`. Added regression for `object -> bytes/list<bytes>` conversion in `test_cpp_runtime_boxing.py`, and confirmed all three run successfully with `tools/benchmark_cpp_list_models.py 07_game_of_life_loop 08_langtons_ant 09_fire_simulation --warmup 0 --repeat 1 --allow-failures`.
- 2026-02-28: Confirmed compile blocker in `12_sort_visualizer` where stack-reduced `list<int64>` was passed as-is to `render(const object&)`. Added correction in `type_bridge._coerce_call_arg` to shift effective target to `object` for list-annotated signatures when `cpp_list_model=pyobj`, boxing only stack lists via `make_object(...)`. Added regression `test_pyobj_list_model_boxes_stack_list_when_call_target_param_is_list_annotation` in `test_py2cpp_codegen_issues.py` and confirmed run success with `benchmark_cpp_list_models.py 12_sort_visualizer --warmup 0 --repeat 1 --allow-failures`.
- 2026-02-28: Confirmed tuple/list runtime blocker in `13_maze_generation_steps` (`index access on non-indexable object`). Root causes: in `make_object(list<T>)`, `make_object(v)` missed tuple overload and collapsed tuple elements to `object()`, and tuple unboxing for pyobj-list subscript was missing. Fixed by placing tuple-boxing overload before `list<T>`, and adding `tuple[...]` conversion `::std::make_tuple(py_at(...))` in `_render_unbox_target_cast`. Confirmed tuple-subscript regression `test_pyobj_list_model_tuple_subscript_unboxes_to_make_tuple_before_destructure` and successful run of `benchmark_cpp_list_models.py 13_maze_generation_steps --warmup 0 --repeat 1 --allow-failures`.
- 2026-02-28: Added additional compile/run verification for `pyobj` only on `05..16`, confirming all 12 succeed (`passed=12 failed=0`). Validation command was a one-shot script iterating per case with `python3 src/py2cpp.py ... --cpp-list-model pyobj` + `g++ -O0` + run. Marked `S4-02-S2` complete.
- 2026-02-28: Switched default `cpp_list_model_opt` in `parse_py2cpp_argv` to `pyobj`, and unified fallback in `py2cpp` main to `pyobj`. Added rollback procedure (`--cpp-list-model value`) to C++ section in `docs/ja/how-to-use.md`, confirmed pass of `test_parse_py2cpp_argv_defaults_cpp_list_model_to_pyobj`, `python3 tools/check_todo_priority.py`, and `python3 tools/check_py2cpp_transpile.py`. Also compared `python3 src/py2cpp.py sample/py/18_mini_language_interpreter.py --single-file` vs `--cpp-list-model value`, confirming default switches to `object lines = make_object(list<object>{});` and rollback switches to `list<str> lines = ...;`. Marked `S4-02-S3` and parent `S4-02` complete.
- 2026-02-28: As `S4-03`, finalized old `value` compatibility-code removal targets (emitter branches / runtime bridge / CLI rollback) and staged removal (A-E). Also defined separate-ID filing conditions (parity/selfhost regression, spread beyond `list`, need to declare deprecation period), fixing this ID scope.
- 2026-02-28: As `S4-04`, synchronized operation descriptions in `docs/ja/how-to-use.md` (default/rollback), `docs/ja/spec/spec-cpp-list-reference-semantics.md` (pyobj default + value rollback contract), and `docs/ja/todo/index.md` (parent/child completion). Re-ran `python3 tools/check_todo_priority.py` and confirmed TODO operation consistency remains valid.

## Breakdown

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S0-01] Document `list` reference-semantics contract (alias/share/destructive update) in docs/spec.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S0-02] Add alias-expected fixture (shared `append/pop` after `a=b`) and visualize current gap.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S0-03] Inventory locations in current samples/fixtures that depend on list value-copy and fix them in decision logs.

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-01] Add new list PyObj model in runtime (type/lifetime/iter/len/truthy contract).
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-02] Extend `make_object` / `obj_to_*` / `py_iter_or_raise` to support the new list model.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-03] Add minimal compatibility bridge with old value model to suppress compile breaks during staged migration.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S1-04] Add runtime unit tests (construction/alias/iter/boundary conversion).

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-01] Consolidate C++ emitter list type rendering through model switch (`value|pyobj`).
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-02] Update output for list literal/ctor/append/extend/pop/index/slice to support `pyobj` model.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-03] Make list iteration lowering for for/enumerate/comprehension work under `pyobj` list.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S2-04] Pass compile/run/parity in representative fixtures including `sample/18` under `pyobj` model.

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S3-01] Add path to hand off annotations from `P1-EAST3-NONESCAPE-IPA-01` to C++ side.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S3-02] Add Cpp pass that reduces only non-escape local lists to stack/RAII.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S3-03] Add fail-closed regression tests that avoid reduction when mixed with unknown/external/dynamic calls.

- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-01] Compare performance/size/diffs of `value` vs `pyobj` on samples and record default-switch decision.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02] Switch default model to `pyobj` and establish rollback procedure (`value` by flag).
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S1] Add `--cpp-list-model {value,pyobj}` to `py2cpp` for rollback prep and apply to single/multi-file output.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2] Resolve compile/runtime blockers in 12 failing sample cases (`05..16`) in stages and expand executable coverage under `pyobj`.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S1] Resolve compile blocker where `grid[y][x] = ...` falls into `object[...]` under pyobj via `py_set_at(...)` lowering.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S2] Identify cause of runtime failures in `07/08/09` (`setitem on non-list object`) and fix lowering/runtime so `py_set_at` input is list object.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S3] Resolve `12_sort_visualizer` compile blocker (list-annotated arg mismatches `object` signature) with callsite boxing correction.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S2-S4] Resolve tuple/list runtime blocker in `13_maze_generation_steps` (missing tuple boxing and tuple-subscript unboxing).
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-02-S3] Switch default model to `pyobj` and reflect `--cpp-list-model value` as rollback procedure in operation docs.
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-03] Finalize old value-model compatibility-code removal plan (including criteria for filing separate IDs).
- [x] [ID: P1-LIST-PYOBJ-MIG-01-S4-04] Synchronize operational descriptions in docs/how-to-use/spec/todo and satisfy final acceptance criteria.
