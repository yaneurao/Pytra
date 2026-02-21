# TODO (Open)

<a href="../docs/todo.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>


Last updated: 2026-02-21

## P0: Selfhost Stabilization

1. [ ] Complete staged recovery of the selfhost `.py` path.
2. [ ] Stabilize the minimal execution path of `selfhost/py2cpp.out` (ensure input/generation/execution can always be reproduced end-to-end).
3. [ ] Reduce selfhost compile errors to zero in stages (including immediate re-detection procedures on regression).
4. [ ] Continue cleanup of selfhost-only stubs in `tools/prepare_selfhost_source.py`.

## P1: CodeEmitter / Hooks Migration

1. [ ] Implement hook injection (`EmitterHooks`).
2. [ ] Gradually split the large branches in `render_expr(Call/BinOp/Compare)` into hooks + helpers.
3. [ ] Move only profile-hard-to-express cases to hooks (leave no condition branches in `py2cpp.py`).

## P1: py2cpp Reduction (Line Count Reduction)

1. [ ] Move remaining unmigrated logic from `src/py2cpp.py` into `CodeEmitter`, reducing line count in stages.
2. [ ] Split `render_expr` `Call` branches (builtin/module/method) by feature and migrate to `CodeEmitter` helpers.
3. [ ] Move `dict.get/list.* / set.*` call resolution to runtime-call map + hook, reducing direct hardcoding in `py2cpp.py`.
4. [ ] Split arithmetic/comparison/type-conversion branches in `render_expr` into independent functions, switchable via profile/hooks.
5. [ ] Move base rendering of `Constant(Name/Attribute)` to shared `CodeEmitter`.
6. [ ] Template control-flow branches in `emit_stmt` and move them to `CodeEmitter.syntax_*`.
7. [ ] Override only C++-specific differences (brace omission, range-mode, etc.) in hooks.
8. [ ] Move shared templates for `FunctionDef` / `ClassDef` (`open/body/close`) into `CodeEmitter`.
9. [ ] Continue cleaning up unused functions (move detailed tasks into higher-priority sections as needed).

## P2: Any/object Boundary Cleanup

1. [ ] Gradually migrate `CodeEmitter` `Any/dict` boundaries to implementations that stay stable under selfhost.
2. [ ] Minimize fallback to `object` in `cpp_type` and expression rendering.
3. [ ] Separate routes where `Any -> object` is required from routes where it is not, and reduce excessive `make_object(...)` insertion.
4. [ ] Clean up places where default arguments for `py_dict_get_default` / `dict_get_node` become `object`-mandatory.
5. [ ] Identify places in `py2cpp.py` that pass `nullopt` as default values and replace them with type-specific defaults.
6. [ ] Log and list routes that go through `std::any` (from selfhost conversion), then remove them incrementally.
7. [ ] Improve in patches grouped per top 3 functions, and run `check_py2cpp_transpile.py` each time.

## Notes

- Completed tasks and historical logs have been moved to `docs/todo-old.md`.
- Going forward, `docs/todo.md` keeps only unfinished tasks.

