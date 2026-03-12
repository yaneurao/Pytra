# P0: C++ relative import linked class/type support

Last updated: 2026-03-12

Related TODO:
- `docs/en/todo/index.md` `ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01`

Background:
- Relative-import syntax and the C++ multi-file lane for module-level constant / function symbols are already locked with representative smoke tests.
- However, imported class/type symbols such as `from .helper import Foo` still remain as plain `Foo` in type position, and the generated consumer emits C++ like `Foo foo = pytra_mod_helper::Foo(...)`, which fails to compile.
- The current multi-file writer already handles forward declarations for imported module-level functions / globals, but it has no declaration contract for imported classes/types.
- Multi-file projects like Pytra-NES naturally use imported classes and types, so the constant/function lane alone is not enough.

Goal:
- Make C++ multi-file builds handle user-module classes/types imported via relative import in type position as well.
- Raise the imported class/type lane to the same representative build/run contract level as the function/global lane.

In scope:
- the imported class/type lane in `py2x.py --target cpp --multi-file`
- class-storage information in the module type schema
- imported class declaration / include contract in the multi-file writer
- imported class/type rendering in C++ type position
- syncing representative regressions, docs, and inventory

Out of scope:
- wildcard relative import support
- rollout to non-C++ backends
- redesign of namespace-package or package-root inference
- full redesign of class layout or ref-vs-value semantics

Acceptance criteria:
- A representative C++ multi-file smoke using `from .helper import Foo` must build and run under the current class `storage_hint` contract.
- The generated consumer module must render imported classes/types as namespace-qualified C++ types in type position.
- The generated multi-file layout must include enough declaration/include surface to compile imported classes/types within the current storage contract.
- Existing imported function / global relative-import smoke tests must keep passing.
- `python3 tools/check_todo_priority.py`, focused C++ regressions, `python3 tools/build_selfhost.py`, and `git diff --check` must pass.

Verification:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/cpp -p 'test_py2cpp_features.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `git diff --check`

Decision log:
- 2026-03-12: This follow-up was opened as `P0` after the TODO list became empty. The representative repro is `nes/main.py -> from .helper import Foo`, where the current generated `main.cpp` emits `Foo foo = pytra_mod_helper::Foo(3);` and fails to compile.
- 2026-03-12: The first slice is groundwork, not full support. It adds imported-class `storage_hint` to the module type schema and gives the multi-file writer imported class forward declarations as the current contract.
- 2026-03-12: The final v1 target includes both value and ref classes for imported class/type build/run support, but the header/include contract is split into a separate slice.
- 2026-03-12: The multi-file writer now passes optimized user-module EAST as `user_module_east_map` into the emitter, so imported class-signature resolution no longer depends on runtime-only source-path lookup.
- 2026-03-12: The representative sibling relative-import class smoke is now locked on the current `storage_hint=ref` lane, which generates `rc<pytra_mod_controller::Pad>` and `::rc_new<pytra_mod_controller::Pad>(3)` and builds/runs successfully. Value-class redesign remains out of scope for this task.

## Breakdown

- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S1-01] Lock the representative compile failure and target contract in the plan / TODO.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S2-01] Add imported-class `storage_hint` to the module type schema and add imported class forward declarations to the multi-file writer.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S2-02] Render imported classes/types in type position as namespace-qualified C++ types.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S2-03] Establish the declaration/include contract required by the current imported-class storage contract and switch the representative smoke to build/run success.
- [x] [ID: P0-CPP-RELATIVE-IMPORT-LINKED-CLASS-TYPE-01-S3-01] Sync docs / TODO / representative regressions to the current contract and close the task.
