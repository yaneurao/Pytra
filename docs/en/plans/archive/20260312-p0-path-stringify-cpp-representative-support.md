<a href="../../../ja/plans/archive/20260312-p0-path-stringify-cpp-representative-support.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

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
- Baseline drift of the minimal sample `path_stringify.py` is locked with focused regressions.
- In the representative C++ lane, `str(Path(...))` lowers through a `Path`-specific stringify path and compile smoke passes.
- Regressions lock that `Path` does not fall back to generic `py_to_string(T)`.
- Current support wording is synced in the plan, TODO, and C++ support docs.

Verification commands:
- `python3 tools/check/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_py2cpp_features.py' -k path_stringify`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/cpp -p 'test_cpp_runtime_iterable.py' -k path_stringify`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: Because `Path(raw)` construction already compiles in the current representative lane, this task is limited to the `str(Path(...))` stringify path.
- 2026-03-12: v1 is limited to representative `Path` stringification; a generic `str()` policy for user-defined classes remains a separate task.
- 2026-03-12: The baseline regression uses `test/fixtures/stdlib/path_stringify.py` as the representative sample and locks the current C++ output in the form that emits `return py_to_string(path);` and fails to compile on the `operator<<` path.
- 2026-03-12: In the representative C++ lane, v1 lowers only `Path` through `path.__str__()` and does not broaden the generic `py_to_string(T)` policy itself.
- 2026-03-12: The representative contract is now `return path.__str__();` with compile/run smoke; the old compile-failure baseline remains only as drift context.

## Breakdown

- [ ] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01] Lock the representative C++ stringify lane for `str(Path(...))` and remove the Pytra-NES blocker.
- [x] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01-S1-01] Lock the minimal-sample baseline and current compile failure with focused regressions, TODO, and plan.
- [x] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01-S2-01] Implement `Path`-specific stringify lowering in the representative C++ lane.
- [x] [ID: P0-PATH-STRINGIFY-CPP-REPRESENTATIVE-01-S3-01] Sync docs, support wording, and regressions with the current contract and close the task.
