# TODO (Open)

<a href="../docs-jp/todo.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>



Last updated: 2026-02-22

## P0: Selfhost Stabilization

1. [ ] Continue organizing the selfhost-only stub remaining in `tools/prepare_selfhost_source.py`.
   - [x] Replaced `dump_codegen_options_text`'s selfhost fallback from a minimal `"options:\n"` stub to a selfhost-safe implementation that outputs a detailed line.
   - [x] `CodeEmitter.quote_string_literal` / `CodeEmitter.load_profile_with_includes` has been migrated to the main body `@staticmethod` implementation, and the corresponding replacement route on the `tools/prepare_selfhost_source.py` side has been deleted.
   - [x] Removed `dump_codegen_options_text` and `main guard` replacement passes from `tools/prepare_selfhost_source.py`, and switched to forwarding the source implementation directly into selfhost.
   - [x] Removed the exception/help replacement pass (`_patch_selfhost_exception_paths`) and helper (`is_help_requested`) from `tools/prepare_selfhost_source.py`, and switched to forwarding the source CLI branch as-is into selfhost.

## P1: CodeEmitter / Hooks Migration

1. [ ] Move only the cases that are difficult to express with profile to hooks, and leave no conditional branch on the `py2cpp.py` side.

## P1: py2cpp degeneracy (line count reduction)

1. [ ] Step by step transfer the unmigrated logic remaining in `src/py2cpp.py` to `CodeEmitter` and reduce the number of lines.

## P2: Any/object boundary arrangement

1. [ ] Gradually migrate the `Any/dict` boundary of `CodeEmitter` to an implementation that is stable even on selfhost.
2. [ ] Minimize fallback to `object` with `cpp_type` and expression drawing.
3. [ ] Separate routes that require `Any -> object` from those that do not, reducing excessive `make_object(...)` insertion.
4. [ ] Organize the places where the default value of `py_dict_get_default` / `dict_get_node` is required `object`.
5. [ ] Find out where `nullopt` is passed as the default value for `py2cpp.py` and replace it with the default value for each type.
6. [ ] Record and enumerate the routes passing through `std::any` with selfhost conversion and remove them step by step.
7. [ ] Separate patches to improve the top 3 most affected functions, and execute `check_py2cpp_transpile.py` every time.

## Note

- This file only holds unfinished tasks.
- Completed tasks are moved via `docs-jp/todo-history/index.md`.
