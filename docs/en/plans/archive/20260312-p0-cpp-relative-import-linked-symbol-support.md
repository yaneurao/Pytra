# P0: C++ relative import linked symbol support

Last updated: 2026-03-12

Related TODO:
- `docs/en/todo/index.md` `ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01`

Background:
- Relative import syntax itself is already supported, and the parser accepts parenthesized symbol lists such as `from .controller import (...)`.
- However, the C++ multi-file build still emits imported module-level symbols as plain names. A generated consumer like `ppu.cpp` then fails with `BUTTON_A was not declared in this scope`.
- Existing regressions already lock build/run for function alias and module alias cases, but there is no representative smoke for imported module-level constants or globals.
- Pytra-NES hits exactly this case first with `ppu.py -> from .controller import (BUTTON_A, BUTTON_B, ...)`, so this lane needs to be fixed early.

Goal:
- Make C++ multi-file linked builds correctly reference user-module symbols imported via relative import from plain expressions and bitwise expressions.
- Lock the current compile/run contract with a representative smoke, rather than only proving parser acceptance.

In scope:
- `py2x.py --target cpp --multi-file` relative-import symbol build/run lane
- `Name` rendering for imported user-module symbols
- forward declarations for imported module-level symbols in the multi-file writer
- syncing representative regressions, inventory, and docs

Out of scope:
- wildcard relative import support
- rollout to non-C++ backends
- redesign of namespace-package or package-root inference
- full rework of mutable module-global semantics

Acceptance criteria:
- A representative C++ multi-file smoke using `from .controller import (BUTTON_A, BUTTON_B)` must build and run.
- The generated consumer module must reference imported user-module symbols via namespace-qualified names.
- The generated consumer module must include enough forward declarations to compile imported user-module functions and module-level globals.
- Existing relative-import function alias and module alias build/run smokes must keep passing.
- `python3 tools/check_todo_priority.py`, focused C++ regressions, `python3 tools/build_selfhost.py`, and `git diff --check` must pass.

Verification:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: The TODO list was effectively empty, so this follow-up was opened as `P0`. The blocker is not parsing; it is the C++ multi-file linked build where imported module-level constants are not namespace-qualified and fail to compile.
- 2026-03-12: v1 is limited to user-module symbols in the `module-level constant/global + function` lane. It does not expand to imported classes/types or wider cross-runtime import contracts yet.
- 2026-03-12: The representative smoke is `ppu.py -> from .controller import (BUTTON_A, BUTTON_B)`, and the contract is locked so generated `ppu.cpp` renders `BUTTON_A | BUTTON_B` as `pytra_mod_controller::BUTTON_A | pytra_mod_controller::BUTTON_B`.
- 2026-03-12: The multi-file writer now includes imported user-module globals as well as functions in forward declarations. v1 carries this through a new `globals` section in `build_module_type_schema()`.
- 2026-03-12: Focused C++ relative-import regressions and the selfhost build now pass, so `S1-01` / `S2-01` / `S2-02` are complete and `S3-01` is reduced to alias-regression and docs closeout only.
- 2026-03-12: The existing relative-import function-alias and module-alias regressions still pass while the sibling relative symbol-list constants smoke now builds and runs, so the task is closed and moved to archive.

## Breakdown

- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01-S1-01] Lock the current compile failure and representative smoke contract in the plan, TODO, and focused regression.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01-S2-01] Rewrite imported user-module symbol `Name` rendering to namespace-qualified user symbols.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01-S2-02] Add forward declarations for imported module-level symbols in the multi-file writer.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-SYMBOL-01-S3-01] Sync relative-import function alias / module alias regressions and docs to the current contract and close the task.
