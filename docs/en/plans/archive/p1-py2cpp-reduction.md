<a href="../../ja/plans/archive/p1-py2cpp-reduction.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# TASK GROUP: TG-P1-CPP-REDUCE

Last updated: 2026-02-22

Related TODO:
- `docs/ja/todo/index.md` `ID: P1-CPP-REDUCE-01`

Background:
- As `py2cpp.py` grows larger, change impact broadens and review/regression validation cost increases.

Objective:
- Incrementally reduce `py2cpp.py` to C++-specific responsibilities and move shared processing to shared layers.

In scope:
- Logic that can move to `CodeEmitter`
- Responsibility split of CLI layer

Out of scope:
- Large one-shot cleanup that sacrifices selfhost stability

Acceptance criteria:
- `py2cpp.py` line count and branch count decrease step by step
- Core tests and selfhost verification remain healthy

Validation commands:
- `python3 tools/check_py2cpp_transpile.py`
- `python3 tools/build_selfhost.py`

Decision log:
- 2026-02-22: Initial draft.
