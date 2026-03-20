# P0: C++ relative import function symbol contract

Last updated: 2026-03-12

Related TODO:
- `docs/en/todo/index.md` `ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01`

Background:
- The C++ multi-file lane already locks representative sibling relative-import smoke for constant-only, class-only, mixed constant+class, and aliased constant+class cases.
- However, the contract where an imported function symbol appears in the same sibling relative-import statement as constants and classes/types has not yet been locked with a representative case.
- Multi-file projects naturally import helper factories, constructor wrappers, and constants from the same sibling module together.

Goal:
- Lock the sibling relative-import contract that includes imported function symbols in C++ multi-file builds.
- Prove that the current contract still builds and runs when imported function origin, constant origin, class/type origin, and alias local names all coexist.

In scope:
- the sibling relative-import function lane in `py2x.py --target cpp --multi-file`
- a representative smoke containing a function, a constant, and a class/type
- the current alias-local-name contract
- syncing docs / TODO / regressions

Out of scope:
- wildcard relative import support
- rollout to non-C++ backends
- redesign of import semantics or callable lowering
- redesign of package-root or namespace-package handling

Acceptance criteria:
- A representative C++ multi-file smoke using `from .controller import (BUTTON_A as BUTTON, make_pad as make_pad_fn, Pad as ControllerPad)` must build and run.
- The generated consumer module must resolve imported function, constant, and class/type origins correctly.
- Existing sibling relative-import smoke tests without functions must keep passing.
- `python3 tools/check_todo_priority.py`, focused C++ regressions, `python3 tools/build_selfhost.py`, and `git diff --check` must pass.

Verification:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/toolchain/emit/cpp -p 'test_py2cpp_features.py' -k sibling_relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: This follow-up was opened as `P0` after the TODO list became empty. The target is the representative build/run contract for sibling relative imports that include imported function symbols.
- 2026-03-12: The representative smoke already includes the sibling module header in the generated consumer `.cpp`, so the redundant forward declaration block was unnecessary. Re-resolving function return types in the consumer emitter context produced broken declarations such as `Pad make_pad(...)`, so the multi-file writer was closed out by relying on header includes only for user-module dependencies.

## Breakdown

- [x] [ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01-S1-01] Lock the representative function-symbol contract in the plan / TODO.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01-S2-01] Add a representative sibling relative-import smoke containing a function, a constant, and a class/type, and validate the current lane.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01-S2-02] Only if a residual is found, fix the emitter / writer / schema.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-FUNCTION-SYMBOL-01-S3-01] Sync docs / TODO / regressions to the current contract and close the task.
