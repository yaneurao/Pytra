# P1: Split the remaining main-file clusters in `east2_to_east3_lowering.py` in a second wave

Last updated: 2026-03-11

Related TODO:
- `ID: P1-EAST23-LOWERING-ORCHESTRATION-01` in `docs/en/todo/index.md`

Background:
- `P1-EAST23-LOWERING-DECOMPOSITION-01` already moved `type_summary`, `type_id_predicate`, and `nominal_adt_meta` into dedicated modules, shrinking `east2_to_east3_lowering.py` to 833 lines.
- The main file still mixes `call metadata` / `json decode fastpath`, representative `assignment/for` lowering, `match/attribute/forcore` lowering, and `_lower_node` dispatch plus boundary helpers.
- That still makes small nominal ADT, type-expr, or decode-first changes expensive to review, and the main file is not yet close to a facade.

Goal:
- Run a second wave split for the remaining clusters in `east2_to_east3_lowering.py`, pushing the main file toward `lower_east2_to_east3()` plus lifecycle/orchestration.
- Align source-contract tests and representative regressions to the second-wave layout so follow-up work can proceed module by module.

In scope:
- `src/toolchain/ir/east2_to_east3_lowering.py`
- `src/toolchain/ir/east2_to_east3_*.py`
- `test/unit/ir/test_east2_to_east3_lowering.py`
- `test/unit/ir/test_east2_to_east3_source_contract.py`
- `test/unit/selfhost/test_prepare_selfhost_source.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-east23-lowering-orchestration-split.md` / `docs/en/plans/p1-east23-lowering-orchestration-split.md`

Out of scope:
- EAST2/EAST3 spec changes
- New nominal ADT or JsonValue language features
- Backend feature work

Acceptance criteria:
- The `call metadata` / `json decode fastpath` cluster moves into a dedicated module.
- The representative `assignment/for` lowering cluster and the `match/attribute/forcore` lowering cluster move into dedicated modules in bundle-sized slices.
- The main `east2_to_east3_lowering.py` file is reduced to `lower_east2_to_east3()`, node-walk orchestration, and table lifecycle.
- Source-contract and representative regressions pass: `test_east2_to_east3*.py`, `test_prepare_selfhost_source.py`, and `build_selfhost.py`.

Checks:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/ir -p 'test_east2_to_east3*.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_prepare_selfhost_source.py'`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_transpiler_version_gate.py`
- `python3 tools/run_regen_on_version_bump.py --dry-run`
- `git diff --check`

Breakdown:
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-01] Inventory the remaining clusters as `call_metadata`, `stmt_lowering`, `node_dispatch`, and `boundary_helpers`, then fix the split order.
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-02] Compress progress notes to bundle-level summaries and fix the end state as `orchestration + lifecycle`.
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-01] Split the `call metadata` / `json decode fastpath` cluster into a dedicated module.
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-02] Split the representative `assignment/for` statement-lowering cluster into a dedicated module.
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-03] Split the `match/attribute/forcore` lowering and node-dispatch orchestration into dedicated modules.
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S3-01] Update source-contract tests and representative regressions to the second-wave layout.
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S4-01] Update docs / TODO / archive and close the task.

Decision log:
- 2026-03-11: After the first wave, the remaining main-file clusters reduce cleanly to four groups: `call metadata + object fastpath`, `assignment/for lowering`, `match/attribute/forcore lowering`, and `_lower_node + lifecycle helpers`.
- 2026-03-11: The second wave will split `call metadata` first, statement lowering second, and node dispatch/orchestration last. It will stay on bundle-sized slices and will not return to one-helper commits.
