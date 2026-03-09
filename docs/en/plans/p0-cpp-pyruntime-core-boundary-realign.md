# P0: Realign the C++ `py_runtime.h` core boundary and move remaining helpers back upstream / to dedicated lanes

Last updated: 2026-03-09

Related TODO:
- `ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01` in `docs/ja/todo/index.md`

Related:
- `docs/en/spec/spec-runtime.md`

Background:
- `src/runtime/cpp/native/core/py_runtime.h` has already retired the first wave of non-core helpers such as `print/ord/chr/int(x, base)`, the process surface, and `scope_exit`, but helpers with weak justification for staying in `core` still remain.
- The main remaining debt is the re-aggregation of `generated/built_in` companions, typed convenience helpers, tuple access helpers, and handwritten `type_id` wrappers.
- `docs/en/spec/spec-runtime.md` requires that `native/core/py_runtime.h` must not permanently keep high-level built-in semantics, and that built-in companions other than `string_ops` must not flow back in through transitive includes.
- In the current tree, however, `py_runtime.h` still directly includes `runtime/cpp/generated/built_in/numeric_ops.h` and `runtime/cpp/generated/built_in/zip_ops.h`, and it also keeps `contains` under `native/core`. In practice, `core` is compensating for missing include collection in the emitter.
- In addition, some helpers such as `py_dict_get`, tuple `py_at`, and parts of the typed list mutation surface remain for C++ backend lowering convenience rather than for runtime ABI reasons. Leaving them in `core` makes it easier to accidentally replicate similar surfaces in other target runtimes.
- For `type_id`, a generated source of truth already exists, but `py_runtime.h` still carries `py_register_class_type`, `py_is_subtype`, `py_runtime_type_id`, and `py_isinstance`, while generated `type_id.cpp` calls back into them. Ownership is therefore cyclic.

Goal:
- Narrow the responsibility that remains in `src/runtime/cpp/native/core/py_runtime.h` down to `PyObj` / `object` / `rc<>` / raw `type_id` primitives / low-level container primitives / dynamic iteration / arithmetic primitives.
- Remove the places where `core` behaves like a high-level built-in include collector or backend compatibility layer.
- Move `type_id` ownership to the generated source of truth and reduce handwritten wrappers to the minimum necessary surface.
- Restore a state where future target runtimes do not inherit unnecessary helper surfaces from C++ core.

In scope:
- `src/runtime/cpp/native/core/py_runtime.h`
- `src/runtime/cpp/core/py_runtime.h`
- `src/runtime/cpp/generated/built_in/type_id.*`
- `src/runtime/cpp/generated/built_in/numeric_ops.h`
- `src/runtime/cpp/generated/built_in/zip_ops.h`
- `src/runtime/cpp/native/built_in/contains.h`
- `src/backends/cpp/emitter/module.py`
- `src/backends/cpp/emitter/runtime_expr.py`
- `src/backends/cpp/emitter/cpp_emitter.py`
- `src/backends/cpp/emitter/stmt.py` / `collection_expr.py` when required
- Related tests / specs / TODO

Out of scope:
- Full redesign of `PyObj` / `object` / boxing / unboxing
- Full removal of dynamic iteration primitives
- Moving `py_div` / `py_floordiv` / `py_mod`
- Simultaneous synchronization of `docs/en/`
- Purely physical header splitting that only reduces line count

Acceptance criteria:
- Implicit include dependencies on `numeric_ops` / `zip_ops` / `contains` are removed from `py_runtime.h`, and required callers include them explicitly.
- Checked-in typed dict subscript paths no longer depend on `py_dict_get`, allowing `py_dict_get` to be removed from `py_runtime.h`.
- Generated/runtime tuple constant-index paths use `std::get<N>`, and the tuple `py_at` helper is removed from `core` or at least loses all checked-in callers.
- Ownership of `type_id` registry / subtype / isinstance logic moves to `py_tid_*`, and handwritten implementations in `py_runtime.h` shrink to thin delegates or raw primitives.
- Redundant surfaces such as the `py_isinstance_of` fast path and the `PyFile` alias are inventoried and removed when no remaining justification exists.
- Representative C++ backend/runtime tests and parity remain green.
- `python3 tools/check_todo_priority.py` passes.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_type_id.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k json`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k argparse_extended_runtime`
- `python3 tools/runtime_parity_check.py --targets cpp --case-root fixture`
- `git diff --check`

## Priority Order

Proceed in this order. Touching only `type_id` first creates a wide regression surface, while fixing include ownership first makes it easier to shrink the surface and add guards.

1. Make `numeric_ops/zip_ops/contains` explicit includes.
2. Move `py_dict_get` and tuple `py_at` upstream.
3. Restrict typed list/dict mutation helpers to object-bridge-only use.
4. Flip `type_id` ownership.
5. Finish small cleanup and docs/archive work.

## Current Classification

### A. Includes / companions that must leave `core`

- `runtime/cpp/generated/built_in/numeric_ops.h`
- `runtime/cpp/generated/built_in/zip_ops.h`
- `runtime/cpp/native/built_in/contains.h`

Reason:
- They violate the `py_runtime` contract in `spec-runtime`.
- The only reason they still sit in `core` is that `module.py` does not yet collect `zip`, `contains`, and numeric helper includes explicitly.
- `numeric_ops.h` and `zip_ops.h` themselves include `runtime/cpp/core/py_runtime.h`, so the current responsibility boundary is cyclic.

### B. Upstreaming candidates

- `py_dict_get` used by typed dict subscripts
- tuple `py_at(const ::std::tuple<...>&, int64)`
- typed `append/extend/pop/clear/reverse/sort/set_at`

Reason:
- In typed lanes, the backend can lower these directly to `std::get`, `.at()`, member calls, or primitive helpers.
- Keeping them as generic convenience helpers in `core` makes emitter convenience take priority over ABI concerns.

### C. `type_id` surfaces that should be thinned

- `py_register_class_type`
- `py_is_subtype`
- `py_issubclass`
- `py_runtime_type_id`
- `py_isinstance`

Reason:
- `generated/built_in/type_id.cpp` already exists as a source of truth, but currently calls back into handwritten wrappers in `core`.
- What should remain in `core` is limited to `PYTRA_TID_*` constants, `PYTRA_DECLARE_CLASS_TYPE`, and raw tag access through `PyObj`.

### D. Small cleanup candidates

- `value->py_isinstance_of(expected_type_id)` fast path
- `using PyFile = pytra::runtime::cpp::base::PyFile`

Reason:
- No checked-in override or caller has been found, so meaning is unlikely to change by shrinking the surface.

## Phases

### Phase 1: Inventory and contract fixation

1. Classify the target helpers in `py_runtime.h` into `explicit include / upstream / object bridge only / keep`.
2. Inventory checked-in callers in `src/backends/cpp`, `src/runtime/cpp/generated`, tests, and samples.
3. Fix the end state in the decision log so it does not conflict with the current `spec-runtime` contract.

### Phase 2: Include ownership correction

1. Teach `module.py` to collect helper includes for `zip`, `contains`, and numeric helpers.
2. Emit required includes explicitly in generated artifacts and preludes.
3. Remove transitive `numeric_ops` / `zip_ops` / `contains` includes from `py_runtime.h`.
4. Add removed-include inventory guards in the relevant layout/unit checks.

### Phase 3: Upstream typed convenience helpers

1. Move typed dict subscripts to `.at()` and eliminate remaining checked-in `py_dict_get` callers.
2. Align tuple constant-index paths in generated/runtime code to `std::get<N>`.
3. Expand direct lowering for typed `append/extend/pop/clear/reverse/sort/set_at`, shrinking runtime helpers down to object-bridge-only surface.
4. Do not add new generic core helpers just to keep typed lanes alive.

### Phase 4: Flip `type_id` ownership

1. Treat `py_tid_runtime_type_id`, `py_tid_is_subtype`, and `py_tid_isinstance` as the canonical entrypoints.
2. Reduce `py_runtime.h` wrappers (`py_is_subtype`, `py_runtime_type_id`, `py_isinstance`) to thin delegates, or move checked-in callers to `py_tid_*` directly.
3. Re-evaluate `py_register_class_type` and `PYTRA_DECLARE_CLASS_TYPE`, and decide where ownership of the user-type registry lives.
4. Lock non-regression in `test_cpp_runtime_type_id.py` and generated runtime callers.

### Phase 5: Cleanup / docs / archive

1. Remove small leftovers such as the `py_isinstance_of` fast path and the `PyFile` alias.
2. Sync inventory guards, docs, TODO, and archive.
3. Pass `check_todo_priority.py` and representative verification, then close the task.

## Implementation Rules

- Do not introduce temporary compatibility aliases just to delete things from `py_runtime.h`.
- Do not hide missing includes by re-aggregating them on the `core` side.
- Even if handwritten `type_id` helpers remain temporarily, they must not become the source of truth; the generated lane must stay canonical.
- When removing `py_dict_get`, do not reintroduce older object-dict / optional-dict compatibility tranches.
- Even if uncommitted changes accumulate mid-task, do not mix in another `ID` until this one is completed within scope.

## Breakdown

- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01] Realign the `py_runtime.h` core boundary and move remaining helpers back upstream / to dedicated lanes.
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-01] Inventory checked-in callers of `numeric_ops/zip_ops/contains`, typed helpers, tuple helpers, and `type_id` wrappers, then classify the end state.
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-02] Record include ownership, upstream contracts, and non-goals in the decision log so they match `spec-runtime`.
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-01] Extend helper-include collection in the C++ emitter / prelude / generated path so `zip`, `contains`, and numeric helpers are explicitly included.
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-02] Remove transitive `numeric_ops` / `zip_ops` / `contains` includes from `py_runtime.h` and update the removed-include guards.
- [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-01] Switch typed dict subscripts to `.at()` and remove checked-in `py_dict_get` callers.
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-02] Move tuple constant-index access to `std::get<N>` even in generated/runtime paths, and slim or retire the tuple `py_at` helper.
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-03] Shrink typed list/dict mutation helpers down to object-bridge-only surface, prioritizing direct emitter lowering for typed lanes.
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-01] Move ownership of `type_id` registry / subtype / isinstance logic to `py_tid_*`, and slim the wrappers in `py_runtime.h`.
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-02] Update `test_cpp_runtime_type_id.py` and generated runtime callers, and add a guard so cyclic ownership does not reappear.
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-01] Clean up small remaining surfaces such as the `py_isinstance_of` fast path and the `PyFile` alias.
- [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-02] Refresh representative tests / parity / docs / archive and close the task.

## Decision Log

- 2026-03-09: Treat this as a plan to move helpers with weak justification out of `core` into explicit includes, upstream lowering, dedicated lanes, or generated SoT. It is not a plan for merely splitting `py_runtime.h` into more files.
- 2026-03-09: The first implementation step is explicit include ownership for `numeric_ops/zip_ops/contains`, not `type_id`. This is the lowest-risk way to reduce `core` dependencies and makes it easier to add inventory guards afterwards.
- 2026-03-09: Most object-dict / optional-dict / string-sugar variants of `py_dict_get` were already retired in previous tranches. The remaining debt is close to a single typed-dict convenience path in the backend, so it stays near the top of the queue.
- 2026-03-09: The main CppEmitter path already lowers constant tuple indices to `std::get<N>`, so remaining tuple-helper callers are treated as lagging generated/runtime paths.
- 2026-03-09: The intended end state for `type_id` is raw primitives in `core` and nominal subtype / registry algorithms in the generated lane. Avoid extending the life of handwritten wrappers.
- 2026-03-09: The `S1-01` inventory confirmed that the direct checked-in caller for `zip` is `src/backends/cpp/emitter/runtime_expr.py`, the direct checked-in callers for `contains` are in `src/backends/cpp/emitter/cpp_emitter.py`, and the public numeric helper surface already lives under `src/runtime/cpp/pytra/built_in/numeric_ops.h`. In other words, include ownership belongs in the C++ emitter, generated callers, and public companion headers, not in `py_runtime.h`.
- 2026-03-09: The checked-in `py_dict_get` callers now remain not only in the C++ emitter typed-dict path, but also in generated/selfhost paths such as `src/runtime/cpp/generated/std/argparse.cpp`, `src/runtime/cpp/generated/built_in/type_id.cpp`, and `selfhost/py2cpp.cpp`. Therefore `S3-01` must update generated callers as well, not just the emitter.
- 2026-03-09: Checked-in `type_id` wrapper callers still span the main C++ backend, generated C++ runtime, selfhost stage1/stage2, and related tests, so `S4-01` should treat "move callers toward `py_tid_*`" and "shrink `py_runtime.h` wrappers to thin delegates" as one slice.
- 2026-03-09: The `S1-02` contract is now fixed as follows: `numeric_ops/zip_ops/contains` are companion surfaces that must be explicitly included through `pytra/built_in/*.h`; `py_runtime.h` must not re-aggregate them. Typed dict access, tuple constant-index access, and typed mutation helpers should move back upstream or into typed lanes, leaving only object bridges and low-level primitives in `core`. Non-goals remain simultaneous cleanup of other target runtimes and any full boxing/unboxing redesign.
- 2026-03-09: Implemented `S2-01` by extending the helper-include collector in `src/backends/cpp/emitter/module.py`. It now collects `pytra/built_in/{numeric_ops,zip_ops,contains}.h` from `RuntimeSpecialOp(minmax)`, `runtime_call=zip/py_min/py_max`, direct `sum(...)` calls, and `Compare` nodes that lower to `In/NotIn` or `Contains`. Added regression coverage in `test_py2cpp_features.py` so transpiled C++ proves it can pull these helper headers without relying on `py_runtime.h`.
- 2026-03-09: Implemented `S2-02` by removing the re-aggregated `numeric_ops` / `zip_ops` / `contains` includes from `src/runtime/cpp/native/core/py_runtime.h`, then adding explicit `pytra/built_in/contains.h` includes to tracked generated callers (`generated/std/{re,json,argparse}.cpp`, `generated/built_in/type_id.cpp`). In `test_cpp_runtime_iterable.py`, the compile snippet now includes helper headers explicitly and the removed-include guard is inverted to `assertNotIn(...)`.
- 2026-03-09: Implemented `S3-01` by replacing the C++ emitter typed-dict subscript path with a lambda + `.at()` form, while routing string-key any/unknown access through the existing `py_at(dict, key)` primitive. The tracked generated callers in `generated/std/argparse.cpp` and `generated/built_in/type_id.cpp` now use `.at()`, the generic `py_dict_get` helper is removed from `src/runtime/cpp/native/core/py_runtime.h`, and the bridge/runtime inventory tests were updated so tracked `py_dict_get(` callsites do not reappear.
