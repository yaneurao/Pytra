# P2: upstream fallback shrink for C++ `py_runtime.h`

Last updated: 2026-03-14

Related TODO:
- `docs/ja/todo/index.md` `ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01`

Background:
- `docs/ja/plans/archive/20260312-p5-cpp-pyruntime-residual-thin-seam-shrink.md` already classified the residual seams in `py_runtime.h` into `py_append(object& ...)` plus the shared `type_id` thin seam, but it only fixed the shrink order and did not execute the next reduction pass.
- Even so, `src/runtime/cpp/native/core/py_runtime.h` is still 1287 lines as of 2026-03-14, with large blocks for object-bridge compatibility, generic `make_object` / `py_to`, and typed-collection fallback behavior.
- The current callers still show that residual shape: `sample/cpp` contains 41 `py_append(` sites, while `src/runtime/cpp/generated/**` still emits object-bridge patterns such as `py_at(values, py_to<int64>(i))`, `obj_to_list_ref_or_raise(out, "append")`, and `make_object(list<object>{})`.
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
- `python3 tools/check_cpp_pyruntime_header_surface.py`
- `git diff --check`

## Policy

- The main shrink work happens in callers, not by shuffling code around inside the runtime header.
- Treat `py_append(object&)` as an object-only compatibility seam; typed list append should be emitted as `py_list_append_mut` or direct append logic.
- Avoid `py_at(object, idx)` whenever a typed index plan exists; push those cases back into typed subscript, tuple destructure, and typed iteration.
- For dict key coercion and tuple/list boxing, use emitter/EAST3 narrowing when the type is known instead of falling back to generic runtime coercion.
- Leave the shared `type_id` thin seam mostly alone in this task and focus on stopping object-fallback caller growth.

## Breakdown

- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-01] Inventory the current bulk in `py_runtime.h` plus residual callers across `sample/cpp`, `generated/**`, and the C++ emitter, and classify which fallback paths can move upstream.
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S1-02] Freeze the boundary between `object-only compat` and `typed lane must not use` in docs/tooling as the shrink contract.
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-01] Improve typed list mutation, indexing, and tuple/list boxing emission so callers of `py_append(object&)` and `py_at(object, idx)` decrease.
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-02] Reduce object-bridge fallback in generated built_in/std runtime artifacts and representative samples, then refresh the baseline.
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S2-03] Collapse typed-path fallback in generic `make_object`, `py_to`, and dict-key coercion so it stays near real `Any/object` boundaries.
- [ ] [ID: P2-CPP-PYRUNTIME-UPSTREAM-FALLBACK-SHRINK-01-S3-01] Sync regressions, checkers, docs, and the English mirror, and close the current `py_runtime.h` shrink contract.

Decision log:
- 2026-03-14: Opened as a P2 task after the runtime audit confirmed that `py_runtime.h` can still shrink, but the next gain must come from pushing typed fallback upstream into EAST3, the emitter, and runtime SoT rather than physically splitting the header.
