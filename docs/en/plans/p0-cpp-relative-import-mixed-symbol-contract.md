<a href="../../ja/plans/p0-cpp-relative-import-mixed-symbol-contract.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: C++ relative import mixed symbol contract

Last updated: 2026-03-12

Related TODO:
- `docs/en/todo/index.md` `ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01`

Background:
- The C++ multi-file lane already has representative smoke coverage for sibling relative-import constants/functions and for sibling relative-import classes/types, but those lanes are locked separately.
- The contract for a single statement such as `from .controller import (BUTTON_A, Pad)` that mixes constants and classes/types has not yet been locked with a representative case.
- Multi-file projects like Pytra-NES naturally group constants and helper classes from the same sibling module in one import statement.

Goal:
- Lock the mixed-symbol sibling relative-import lane in C++ multi-file builds with a representative smoke test.
- Prove that imported constants and imported classes/types from the same statement still build and run under the current contract.

In scope:
- the mixed sibling relative-import lane in `pytra-cli.py --target cpp --multi-file`
- a representative smoke that imports a constant and a class/type from one `ImportFrom` statement
- syncing docs / TODO / regressions

Out of scope:
- wildcard relative import support
- rollout to non-C++ backends
- redesign of alias import, nested package, or namespace package behavior
- semantic changes to the import system as a whole

Acceptance criteria:
- A representative C++ multi-file smoke using `from .controller import (BUTTON_A, Pad)` must build and run.
- The generated consumer module must render the imported constant and imported class/type correctly even when they come from the same statement.
- Existing constant-only and class-only sibling relative-import smoke tests must keep passing.
- `python3 tools/check_todo_priority.py`, focused C++ regressions, `python3 tools/build_selfhost.py`, and `git diff --check` must pass.

Verification:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p 'test_py2cpp_features.py' -k sibling_relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: This follow-up was opened as `P0` after the TODO list became empty. The target is not a semantic redesign, but locking the representative mixed-symbol contract for sibling relative imports.
- 2026-03-12: The representative smoke `from .controller import (BUTTON_A, Pad)` builds and runs on the current C++ multi-file lane without further code changes, so the mixed constant + class/type combination is now locked as a regression-only follow-up.

## Breakdown

- [x] [ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01-S1-01] Lock the representative mixed-symbol contract in the plan / TODO.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01-S2-01] Add a representative C++ multi-file smoke for mixed constant + class sibling relative imports and validate the current lane.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01-S2-02] Only if a residual is found, fix the emitter / writer / schema for the mixed-symbol lane.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-MIXED-SYMBOL-01-S3-01] Sync docs / TODO / regressions to the current contract and close the task.
