<a href="../../docs-ja/plans/p1-codeemitter-hooks-migration.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P1-CEH

Last updated: 2026-02-22

Related TODO:
- `docs-ja/todo.md` `ID: P1-CEH-01`

Background:
- If conditional logic remains in `py2cpp.py`, extensibility via profile/hook and cross-language consistency degrades.

Objective:
- Move only profile-hard-to-express differences into hooks and minimize `py2cpp.py`-side branching.

In scope:
- Clarifying `CodeEmitter` / hooks boundaries
- Removing branches from `py2cpp.py`

Out of scope:
- Large changes to runtime API specifications

Acceptance criteria:
- Language-specific differences are expressible through profile + hooks
- `py2cpp.py` conditionals are reduced

Validation commands:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 test/unit/test_code_emitter.py`

Decision log:
- 2026-02-22: Initial draft.
