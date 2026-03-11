# P1: Decompose `east2_to_east3_lowering.py` by cluster

Last updated: 2026-03-11

Related TODO:
- `ID: P1-EAST23-LOWERING-DECOMPOSITION-01` in `docs/ja/todo/index.md`

Background:
- Decomposition around `toolchain.ir.core` and the expr/parser facades has largely removed the old `core.py` monolith.
- In contrast, `src/toolchain/ir/east2_to_east3_lowering.py` still exceeds 1800 lines and mixes `type summary`, `nominal ADT metadata`, `type_id predicate lowering`, `call metadata`, and statement lowering in one file.
- That makes nominal ADT and type-expr work expensive to review and obscures which helper groups belong to the same responsibility boundary.

Goal:
- Split `east2_to_east3_lowering.py` into dedicated modules by cluster so the main file is centered on orchestration and representative lowering.
- Lock the new split boundaries with source-contract tests and representative regressions.

In scope:
- `src/toolchain/ir/east2_to_east3_lowering.py`
- `src/toolchain/ir/east2_to_east3_*.py`
- `test/unit/ir/test_east2_to_east3_lowering.py`
- `test/unit/ir/test_east2_to_east3_source_contract.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-east23-lowering-decomposition.md` / `docs/en/plans/p1-east23-lowering-decomposition.md`

Out of scope:
- EAST2/EAST3 spec changes
- New language features for nominal ADT or JsonValue
- Backend feature work

Acceptance criteria:
- At least three clusters move out of `east2_to_east3_lowering.py`: `type summary`, `nominal ADT metadata`, and `type_id predicate lowering`.
- The main file primarily owns `lower_east2_to_east3()` and node-walk / representative lowering orchestration.
- Source-contract tests lock the split import surface.
- Representative regressions pass: `test_east2_to_east3_lowering.py`, `test_prepare_selfhost_source.py`, and `build_selfhost.py`.

Checks:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Breakdown:
- [x] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S1-01] Inventory helpers in `east2_to_east3_lowering.py` and lock split boundaries for `type_summary`, `type_id_predicate`, `nominal_adt_meta`, `call_metadata`, and `stmt_orchestration`.
- [x] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S1-02] Fix bundle-level progress-note rules for this task and avoid helper-by-helper progress logs.
- [x] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S2-01] Split the `type summary`, `nominal decl summary`, and `json receiver contract` cluster into a dedicated module.
- [ ] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S2-02] Split the `type_id predicate`, `isinstance`, and `issubclass` lowering cluster into a dedicated module.
- [ ] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S2-03] Split the `nominal ADT ctor/projection/match metadata` cluster into a dedicated module.
- [ ] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S3-01] Update source-contract tests and representative regressions to the split module layout.
- [ ] [ID: P1-EAST23-LOWERING-DECOMPOSITION-01-S4-01] Update docs / TODO / archive and move the task to archive when complete.

Decision log:
- 2026-03-11: Initial version. After `core.py` and expr facade decomposition, `east2_to_east3_lowering.py` is the next clear large monolith.
- 2026-03-11: The first wave targets three clusters first: `type summary`, `nominal ADT metadata`, and `type_id predicate lowering`. Assignment/call/statement orchestration remains in the main file for now.
- 2026-03-11: Progress notes for this task stay bundle-level; detailed helper names belong in the plan decision log or commit messages.
- 2026-03-11: The first `S2-01` bundle moved `type summary`, `nominal decl summary`, and `json receiver contract` helpers into `east2_to_east3_type_summary.py`. The main file now uses `_swap_nominal_adt_decl_summary_table()` for lifecycle management, and a dedicated `test_east2_to_east3_source_contract.py` locks the split surface.
