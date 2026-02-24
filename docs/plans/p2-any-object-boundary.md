<a href="../../docs-ja/plans/p2-any-object-boundary.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P2-ANY-OBJ

Last updated: 2026-02-22

Related TODO:
- `docs-ja/todo.md` `ID: P2-ANY-01` to `P2-ANY-07`

Background:
- Ambiguous `Any/object` boundaries reduce quality in both selfhost and generated code through excessive boxing and type collapse.

Objective:
- Clarify responsibility boundaries between `Any` and `object`, reducing conversions to only what is necessary.

In scope:
- Fallback optimization in `cpp_type` / expression rendering
- Type cleanup in dict default-value paths
- Visibility and reduction of `std::any` traversal paths

Out of scope:
- Redesign of the whole type system

Acceptance criteria:
- Unnecessary fallbacks to `object` are reduced
- `std::any` paths are reduced step by step
- No selfhost regressions

Validation commands:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/check_selfhost_cpp_diff.py --mode allow-not-implemented`

Decision log:
- 2026-02-22: Initial draft.
