# P0: Representative C++ stringify support for `str(Path(...))`

Last updated: 2026-03-12

Related TODO:
- `ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01` in `docs/ja/todo/index.md`

Background:
- The Pytra-NES minimal sample [`materials/refs/from-Pytra-NES/path_stringify.py`](../../../materials/refs/from-Pytra-NES/path_stringify.py) uses `path = Path(raw); return str(path)`.
- In the current representative C++ lane, `str(path)` lowers to generic `py_to_string(path)`, which requires `std::ostringstream << Path` and fails to compile.
- `Path(raw)` itself already compiles, so the real issue is that `Path`-specific stringify falls through to the generic fallback.

Objective:
- Lower `str(Path(...))` through the correct stringify path in the representative C++ lane and remove the Pytra-NES blocker.
- Lock with focused regressions that `Path` must not fall back to generic `ostream << T`.

In scope:
- representative C++ lowering for `str(Path(...))`
- helper or method dispatch for `Path` stringification
- focused regressions, docs, and TODO sync

Out of scope:
- a redesign of the full `Path` API
- simultaneous rollout to all backends
- a generic `str()` policy for arbitrary user-defined classes
- a redesign of `repr(Path)` or path normalization

Acceptance criteria:
- The current compile failure of the minimal sample `path_stringify.py` is locked with a focused regression.
- In the representative C++ lane, `str(Path(...))` lowers through a `Path`-specific stringify path and compile smoke passes.
- Regressions lock that `Path` does not fall back to generic `py_to_string(T)`.
- Current support wording is synced in the plan and TODO.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k path_stringify`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_cpp_runtime_iterable.py' -k py_to_string`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: Because `Path(raw)` construction already compiles in the current representative lane, this task is limited to the `str(Path(...))` stringify path.
- 2026-03-12: v1 is limited to representative `Path` stringification; a generic `str()` policy for user-defined classes remains a separate task.

## Breakdown

- [ ] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01] Lock the representative C++ stringify lane for `str(Path(...))` and remove the Pytra-NES blocker.
- [ ] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01-S1-01] Lock the minimal-sample baseline and current compile failure with focused regressions, TODO, and plan.
- [ ] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01-S2-01] Implement `Path`-specific stringify lowering in the representative C++ lane.
- [ ] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01-S3-01] Sync docs, support wording, and regressions with the current contract and close the task.
