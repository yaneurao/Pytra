<a href="../../docs-ja/plans/archive/p1-codeemitter-dispatch-redesign.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P1-CED

Last updated: 2026-02-22

Related TODO:
- `docs-ja/todo/index.md` `ID: P1-CED-*`

Background:
- Selfhost strongly depends on static-binding assumptions, and commonization can create paths that fail to reach derived implementations.

Objective:
- Redesign `render_expr` / `emit_stmt` around hook-first dispatch, balancing commonization and selfhost stability.

In scope:
- Kind-level hook injection
- Two-stage structure in `CppEmitter`: hook-first + fallback
- Gradual reduction of fallback usage
- Organizing commonization candidates across py2cpp/py2rs

Out of scope:
- Full one-shot rewrite

Acceptance criteria:
- Generated output matches existing behavior when hooks are enabled
- `mismatches=0` in selfhost diff
- Branching inside `py2cpp.py` is reduced incrementally

Validation commands:
- `python3 tools/check_selfhost_cpp_diff.py`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-02-22: Initial draft.
