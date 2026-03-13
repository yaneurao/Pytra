# P2: upstream fallback shrink for C++ `py_runtime.h`

Last updated: 2026-03-14

Related TODO:
- `docs/ja/todo/index.md` `ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01`

Background:
- `docs/ja/plans/archive/20260312-p5-cpp-pyruntime-residual-thin-seam-shrink.md` already classified the residual seams in `py_runtime.h` into `py_append(object& ...)` plus the shared `type_id` thin seam, but it only fixed the shrink order and did not execute the next reduction pass.
- Even so, `src/runtime/cpp/native/core/py_runtime.h` is still 1287 lines as of 2026-03-14, with large blocks for object-bridge compatibility, generic `make_object` / `py_to`, and typed-collection fallback behavior.
- The current callers still show the residual shape: the `sample/cpp` `py_append(` bucket is now retired, but `src/runtime/cpp/generated/**` still emits object-bridge patterns such as `py_at(values, py_to<int64>(i))` and `obj_to_list_ref_or_raise(out, "append")`, and the samples still retain a generic-index bucket.
- As `src/runtime/cpp/generated/core/README.md` already states, `generated/core` must not become a dump bucket for `py_runtime.h` bloat. The next shrink therefore has to happen by pushing typed fallback behavior upstream, not by splitting the header.

Objective:
- Shrink `py_runtime.h` through upstream responsibility cleanup instead of physical file splitting.
- Push typed list/dict/indexing/mutation and boxing/unboxing decisions back into EAST3, the C++ emitter, and the runtime SoT so `object` fallback becomes rarer.
- Keep generic helpers only at real `Any/object` boundaries, while typed lanes use direct typed expressions or narrower helpers.

In scope:
- `src/runtime/cpp/native/core/py_runtime.h`
- list/index/mutation/boxing/type-bridge logic under `src/backends/cpp/emitter/**`
- any EAST3 optimization/lowering needed to remove typed fallback before emit
- residual callers under `src/runtime/cpp/generated/built_in/**`, `src/runtime/cpp/generated/std/**`, and `sample/cpp/**`
- docs, tooling, and regressions that lock the shrink baseline for `py_runtime.h`

Out of scope:
- simple physical splitting of `py_runtime.h` or include shuffling
- redesigning the shared `type_id` thin seam across runtimes
- a full redesign of the `PyObj` object model itself
- semantic changes to `py_div`, `py_floordiv`, or `py_mod`

Acceptance criteria:
- typed lanes no longer rely on `py_append(object&)`, `py_at(object, idx)`, or `obj_to_list_ref_or_raise(...)` except for explicit object-only compatibility callers.
- the residual caller inventory in `sample/cpp/**` and `src/runtime/cpp/generated/**` drops below the current baseline, and the new baseline is fixed in docs/tooling.
- generic `make_object(const T&)` / `py_to<T>(object)` fallback moves toward true `Any/object` boundaries, while typed-known paths use direct typed expressions or narrower helpers.
- `py_runtime.h` shrinks in line count and/or source-wide caller inventory without turning `generated/core` into a bloat bucket.
- representative regressions, checkers, and the English mirror are synchronized to the updated shrink contract.

Validation commands (planned):
- `python3 tools/check_todo_priority.py`
- `rg -n "\\bpy_append\\(|\\bpy_at\\([^\\n]*object|obj_to_list_ref_or_raise\\(|make_object\\(list<object>\\{|py_to<[^>]+>\\(.*object" src/runtime/cpp src/backends/cpp sample/cpp test/unit/backends/cpp -S`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_codegen_issues.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_cpp_pyruntime_upstream_fallback_inventory.py'`
- `python3 tools/check_cpp_pyruntime_upstream_fallback_inventory.py`
- `python3 tools/check_cpp_pyruntime_header_surface.py`
- `git diff --check`

## Policy

- The main shrink work happens in callers, not by shuffling code around inside the runtime header.
- Treat `py_append(object&)` as an object-only compatibility seam; typed list append should be emitted as `py_list_append_mut` or direct append logic.
- Avoid `py_at(object, idx)` whenever a typed index plan exists; push those cases back into typed subscript, tuple destructure, and typed iteration.
- For dict key coercion and tuple/list boxing, use emitter/EAST3 narrowing when the type is known instead of falling back to generic runtime coercion.
- Leave the shared `type_id` thin seam mostly alone in this task and focus on stopping object-fallback caller growth.

## Breakdown

- [x] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-01] Inventory the current bulk in `py_runtime.h` plus residual callers across `sample/cpp`, `generated/**`, and the C++ emitter, and classify which fallback paths can move upstream.
- [x] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-02] Freeze the boundary between `object-only compat` and `typed lane must not use` in docs/tooling as the shrink contract.
- [x] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01] Improve typed list mutation, indexing, and tuple/list boxing emission so callers of `py_append(object&)` and `py_at(object, idx)` decrease.
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-02] Reduce object-bridge fallback in generated built_in/std runtime artifacts and representative samples, then refresh the baseline.
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03] Collapse typed-path fallback in generic `make_object`, `py_to`, and dict-key coercion so it stays near real `Any/object` boundaries.
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S3-01] Sync regressions, checkers, docs, and the English mirror, and close the current `py_runtime.h` shrink contract.

Decision log:
- 2026-03-14: Opened as a P2 task after the runtime audit confirmed that `py_runtime.h` can still shrink, but the next gain must come from pushing typed fallback upstream into EAST3, the emitter, and runtime SoT rather than physically splitting the header.
- 2026-03-14: The residual thin-seam checker stack still pointed at the archived `P5` plan as its active follow-up, so this `P2` was rebased as the current owner and the locked bundle order was synchronized to the active `S1-01..S3-01` shrink contract.
- 2026-03-14: Completed `S1-01` by adding `src/toolchain/compiler/cpp_pyruntime_upstream_fallback_inventory.py` and `tools/check_cpp_pyruntime_upstream_fallback_inventory.py`, locking 9 header bulk anchors, 2 C++ emitter residual categories, 3 generated runtime residual categories, and 2 sample residual categories in a machine-readable inventory plus unit test.
- 2026-03-14: The 2026-03-14 baseline is fixed as 1287 lines in `src/runtime/cpp/native/core/py_runtime.h`, 5 header `py_to<*>(...object...)` call sites, 2 `obj_to_list_ref_or_raise(` plus 3 `make_object(list<object>{})` sites under `src/backends/cpp/emitter/**`, 2 `obj_to_list_ref_or_raise(` plus 3 `make_object(list<object>{})` plus 46 `py_at(...py_to<int64>)` sites under `src/runtime/cpp/generated/**`, and 41 `py_append(` plus 39 `py_at(...py_to<int64>)` sites under `sample/cpp/**`.
- 2026-03-14: Completed `S1-02` by adding `src/toolchain/compiler/cpp_pyruntime_upstream_fallback_contract.py` and `tools/check_cpp_pyruntime_upstream_fallback_contract.py`, partitioning the header bulk into 4 `object_only_compat_header` entries, 5 `any_object_boundary_header` entries, and 7 `typed_lane_must_not_use` residual entries.
- 2026-03-14: The final handoff guard now includes the upstream fallback boundary checker/test so the active `P2` handoff references both the baseline inventory and the object-only versus typed-lane boundary contract.
- 2026-03-14: As the first `S2-01` bundle, switched empty pyobj runtime list seeds from generic `make_object(list<object>{})` boxing to direct `object_new<PyListObj>(list<object>{})`, which removes the `cpp_emitter_boxed_list_seed_sites` bucket from the emitter residual inventory. The only remaining emitter-side typed-lane residual is now the `obj_to_list_ref_or_raise(` helper bucket.
- 2026-03-14: As the second `S2-01` bundle, collapsed the inline `obj_to_list_ref_or_raise({boxed_value}, ...)` site in pyobj runtime list `extend` through the shared helper, reducing `cpp_emitter_object_list_bridge_sites` to the helper definition alone. The emitter-side residual is now helper-only even at the source-literal level.
- 2026-03-14: `S2-01` is now considered complete because the emitter-side residual has collapsed to the helper-only boundary.
- 2026-03-14: As the first `S2-02` bundle, regenerated `generated/built_in/iter_ops.cpp` via `src/py2x.py --target cpp src/pytra/built_in/iter_ops.py --emit-runtime-cpp` and `generated/utils/gif.{h,cpp}` via `src/py2x.py --target cpp src/pytra/utils/gif.py --emit-runtime-cpp`. That shrinks `generated_runtime_boxed_list_seed_sites` from `3 -> 1`, leaving only `bytes(make_object(list<object>{}))` in `generated/utils/gif.cpp`.
- 2026-03-14: As the second `S2-02` bundle, upstreamed the empty `bytes` seed in `src/pytra/utils/gif.py` to a typed `list[int]`, retiring the final `bytes(make_object(list<object>{}))` site from `generated/utils/gif.cpp`. The typed-lane residual inventory is now 1 emitter bucket plus 2 generated-runtime buckets and 2 sample buckets, and `generated_runtime_boxed_list_seed_sites` was removed from the inventory and contract.
- 2026-03-14: As the third `S2-02` bundle, regenerated representative samples `07_game_of_life_loop` and `12_sort_visualizer` onto direct typed append / size lanes, reducing the `sample_cpp_py_append_sites` baseline from `41 -> 34`. `18_mini_language_interpreter` exposed a separate sample/emitter regression and was therefore excluded from this bundle, so the remaining sample bucket still lives in the visualization-heavy sample set plus the parser/benchmark helpers inside `18_mini_language_interpreter`.
- 2026-03-14: As the fourth `S2-02` bundle, moved the token/parser/benchmark helpers in `18_mini_language_interpreter` onto direct typed append / size lanes, reducing the `sample_cpp_py_append_sites` baseline from `34 -> 7`. The remaining sample bucket now concentrates in the tuple/frame helper lane inside `13_maze_generation_steps`.
- 2026-03-14: As the fifth `S2-02` bundle, retired the last `py_append(` residuals from `sample/cpp` and removed `sample_cpp_py_append_sites` from the inventory. The sample-side typed residual now consists only of the generic-index `py_at(...py_to<int64>)` bucket.
- 2026-03-14: As the sixth `S2-02` bundle, rewrote `src/pytra/built_in/predicates.py` from object indexing loops onto the iterator lane, shrinking the `generated_runtime_generic_index_sites` baseline from `46 -> 44`. The remaining sites now concentrate in `iter_ops`, `type_id`, `std/*`, and `utils/png`.
