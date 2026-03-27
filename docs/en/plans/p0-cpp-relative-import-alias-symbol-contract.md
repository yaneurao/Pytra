<a href="../../ja/plans/p0-cpp-relative-import-alias-symbol-contract.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: C++ relative import alias symbol contract

Last updated: 2026-03-12

Related TODO:
- `docs/en/todo/index.md` `ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01`

Background:
- The C++ multi-file lane already has representative smoke coverage for sibling relative-import constant-only, class-only, and mixed constant+class statements.
- However, the alias-import contract for forms such as `from .controller import (BUTTON_A as BUTTON, Pad as ControllerPad)` is not yet locked with a representative case.
- Multi-file projects use `as` aliases for collision avoidance and clearer local naming, so practical relative-import support should also lock the alias lane.

Goal:
- Lock the sibling relative-import alias lane in C++ multi-file builds with a representative smoke test.
- Prove that the current contract both resolves imported origins correctly and lets the consumer use local alias names.

In scope:
- the sibling relative-import alias lane in `pytra-cli.py --target cpp --multi-file`
- a representative smoke that aliases a constant and a class/type
- syncing docs / TODO / regressions

Out of scope:
- wildcard relative import support
- rollout to non-C++ backends
- semantic changes to alias import behavior
- redesign of package-root or namespace-package handling

Acceptance criteria:
- A representative C++ multi-file smoke using `from .controller import (BUTTON_A as BUTTON, Pad as ControllerPad)` must build and run.
- The generated consumer module must accept alias local names while still resolving the imported origins correctly.
- Existing non-alias sibling relative-import smoke tests must keep passing.
- `python3 tools/check_todo_priority.py`, focused C++ regressions, `python3 tools/build_selfhost.py`, and `git diff --check` must pass.

Verification:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p 'test_py2cpp_features.py' -k sibling_relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: This follow-up was opened as `P0` after the TODO list became empty. The target is the representative build/run contract for the alias lane, not a redesign of import semantics.
- 2026-03-12: The representative smoke `from .controller import (BUTTON_A as BUTTON, Pad as ControllerPad)` builds and runs on the current C++ multi-file lane without code changes. The generated consumer resolves alias local names back to their imported origins instead of keeping the aliases in emitted C++.
- 2026-03-12: At close-out, no additional emitter / writer / schema changes were needed for the alias lane. The task completed as a regression lock plus docs sync only.

## Breakdown

- [x] [ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01-S1-01] Lock the representative alias contract in the plan / TODO.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01-S2-01] Add a representative C++ multi-file smoke for mixed-symbol sibling relative imports with aliases and validate the current lane.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01-S2-02] Only if a residual is found, fix the emitter / writer / schema for the alias lane.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-ALIAS-SYMBOL-01-S3-01] Sync docs / TODO / regressions to the current contract and close the task.
