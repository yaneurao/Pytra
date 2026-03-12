# P0: Representative C++ support for `bytes` truthiness

Last updated: 2026-03-12

Related TODO:
- `ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01` in `docs/ja/todo/index.md`

Background:
- The minimal sample shared from Pytra-NES, [`materials/refs/from-Pytra-NES/bytes_truthiness.py`](../../../materials/refs/from-Pytra-NES/bytes_truthiness.py), uses `bytes` truthiness such as `if payload:`.
- In the current representative C++ lane, `bytes` lowers to `const list<unsigned char>`, but truthiness is still emitted as `if (payload)`, so the C++ build fails with `could not convert ... to bool`.
- This is not the same task as `~` support or `deque`; it is a missing lowering for `bytes` truthiness specifically.

Objective:
- Lower `bytes` truthiness correctly in the representative C++ lane and remove the Pytra-NES blocker.
- Eliminate the assumption that `bytes` can be implicitly converted to `bool`, and lock the truthiness contract with focused regressions and inventory.

In scope:
- `bytes` truthiness in `if payload:`, `while payload:`, and conditional expressions
- representative C++ emitter/lowering
- focused regressions, docs, and TODO sync

Out of scope:
- a redesign of truthiness in general
- a redesign of the `bytes` runtime type itself
- simultaneous rollout to non-C++ backends
- automatic extension to `bytearray` or `memoryview`

Acceptance criteria:
- The current failure of the minimal sample `bytes_truthiness.py` is locked with a focused regression.
- In the representative C++ lane, `bytes` truthiness lowers through a helper or `len`-based path, and compile smoke passes.
- Support wording for `bytes` truthiness is recorded in the plan and TODO.
- The task remains granular enough that `bytearray` and similar follow-ups can be split later.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k bytes_truthiness`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_east3_cpp_bridge.py' -k truthy`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: The Pytra-NES blocker is a compile failure, so we remove it first in representative C++ lowering rather than a larger runtime redesign.
- 2026-03-12: v1 is limited to `bytes`; extensions such as `bytearray` are deferred.

## Breakdown

- [ ] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01] Lock the representative C++ lane for `bytes` truthiness and remove the Pytra-NES blocker.
- [ ] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01-S1-01] Lock the minimal-sample baseline and current C++ failure with focused regressions, TODO, and plan.
- [ ] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01-S2-01] Lower `bytes` truthiness in the representative C++ lane through a helper or `len`-based path.
- [ ] [ID: P0-BYTES-TRUTHINESS-CPP-REPRESENTATIVE-01-S3-01] Sync docs, support wording, and regressions with the current contract and close the task.
