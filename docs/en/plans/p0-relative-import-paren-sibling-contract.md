# P0: Lock the parenthesized sibling relative-import contract

Last updated: 2026-03-12

Related TODO:
- `ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01` in `docs/ja/todo/index.md`

Background:
- The first Pytra-NES blocker reported was a parenthesized sibling relative import such as `from .controller import (BUTTON_A, BUTTON_B, ...)`.
- In the current tree, the self-hosted parser already accepts this syntax, and the representative C++ multi-file smoke already builds and runs.
- However, the current support is still implicit across parser regression and C++ smoke; it is not explicitly locked in the CLI representative contract or the live docs/plan surface.
- Since the TODO list became empty, the next practical hardening step is to promote this lane to an explicit `P0` current-support contract.

Goal:
- Make `from .module import (...)` sibling relative imports an explicit current support lane.
- Add a Pytra-NES-like representative CLI regression so the parser, CLI, and C++ multi-file lanes all keep this behavior.
- Record clearly that this is contract hardening for an already-working lane, not a new language feature.

In scope:
- Lock parser behavior and a representative CLI smoke contract
- Sync TODO / plan and English mirror docs
- Add the smallest necessary regression coverage

Out of scope:
- Adding new relative-import semantics
- wildcard relative-import support
- extra hardening for parent relative imports (`..`)
- non-C++ backend rollout

Acceptance criteria:
- A parser regression continues to accept `from .controller import (...)`.
- A representative `py2x.py --target cpp` CLI test successfully transpiles a project that uses a parenthesized sibling relative import.
- Existing C++ multi-file build/run smoke continues to pass.
- The ja/en TODO + plan mirrors document this as a current support contract.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east_core_parser_behavior_types.py' -k parenthesized_symbol_list`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_py2x_cli.py' -k parenthesized`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k sibling_relative_import_constants_build_and_run`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: The current tree already passed both the parser and C++ smoke cases, so this task is filed as contract hardening rather than feature implementation.
- 2026-03-12: The representative case follows the Pytra-NES report and prioritizes `from .controller import (BUTTON_A, BUTTON_B)`.

## Breakdown

- [ ] [ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01] Lock parenthesized sibling relative imports as a current support contract.
- [x] [ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01-S1-01] Add the active plan / TODO entry and sync the English mirror.
- [x] [ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01-S2-01] Add a representative CLI regression that locks the `py2x.py --target cpp` lane.
- [ ] [ID: P0-RELATIVE-IMPORT-PAREN-SIBLING-CONTRACT-01-S2-02] Align parser / C++ smoke / docs handoff wording and close the task.
