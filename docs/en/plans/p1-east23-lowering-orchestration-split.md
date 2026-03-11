# P1: Split the remaining `east2_to_east3_lowering.py` clusters in a second wave

Last updated: 2026-03-11

Related TODO:
- `ID: P1-EAST23-LOWERING-ORCHESTRATION-01` in `docs/ja/todo/index.md`

Background:
- The first wave already moved `type summary`, `type_id predicate lowering`, and `nominal ADT metadata` into dedicated modules, shrinking the main file to 833 lines.
- Even so, `src/toolchain/ir/east2_to_east3_lowering.py` still owns `call metadata/json decode fastpath`, `Assign/For/ForRange` lowering, `Attribute/Match/ForCore` lowering, and node dispatch.
- Keeping those clusters together still makes JsonValue / nominal ADT / typed-boundary changes expensive to review and leaves the main-file end state unclear.

Goal:
- Move the remaining clusters out of `east2_to_east3_lowering.py` so the main file becomes centered on orchestration / dispatch / lifecycle.
- Lock the second-wave split boundaries with source-contract tests and representative regressions.

In scope:
- `src/toolchain/ir/east2_to_east3_lowering.py`
- `src/toolchain/ir/east2_to_east3_*.py`
- `test/unit/ir/test_east2_to_east3_lowering.py`
- `test/unit/ir/test_east2_to_east3_source_contract.py`
- `test/unit/ir/test_east2_to_east3_split_regressions.py`
- `docs/ja/todo/index.md` / `docs/en/todo/index.md`
- `docs/ja/plans/p1-east23-lowering-orchestration-split.md` / `docs/en/plans/p1-east23-lowering-orchestration-split.md`

Out of scope:
- EAST2/EAST3 spec changes
- New language features for nominal ADT or JsonValue
- Backend feature work

Acceptance criteria:
- The `call metadata/json decode fastpath` cluster moves into a dedicated module.
- At least one of the remaining `stmt lowering` or `dispatch/orchestration` clusters also moves into a dedicated module.
- The main file primarily owns `lower_east2_to_east3()`, dispatch-mode / legacy-bridge lifecycle, and node-dispatch orchestration.
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
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-01] Inventory the remaining clusters as `call_metadata`, `stmt_lowering`, and `dispatch_orchestration`, then lock the split order.
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S1-02] Keep progress notes bundle-level and fix the main-file end state as `dispatch + lifecycle`.
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-01] Split the `call metadata` / `json decode fastpath` cluster into a dedicated module.
- [x] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-02] Split the `Assign` / `For` / `ForRange` lowering cluster into a dedicated module.
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S2-03] Split `Attribute` / `Match` / `ForCore` lowering plus node-dispatch orchestration into dedicated modules.
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S3-01] Update source-contract tests and representative regressions to the second-wave split layout.
- [ ] [ID: P1-EAST23-LOWERING-ORCHESTRATION-01-S4-01] Update docs / TODO / archive and close the task.

Decision log:
- 2026-03-11: After the first-wave split, the remaining 833-line file was re-inventoried into three second-wave clusters: `call metadata/json decode`, `stmt lowering`, and `dispatch/orchestration`.
- 2026-03-11: The second wave starts with `call metadata/json decode fastpath` because JsonValue contract handling and object-bridge fallbacks still live together there, making it the highest-leverage reduction in main-file complexity.
- 2026-03-11: Progress notes remain bundle-level only; helper-level history stays in this decision log or in commit messages.
- 2026-03-11: `S2-01` moved `_infer_json_semantic_tag`, `_build_json_decode_meta`, `_lower_representative_json_decode_call`, and `_decorate_call_metadata` into `east2_to_east3_call_metadata.py`. Source-contract coverage now asserts dedicated ownership, and split regressions gained a representative `json.value.as_obj` lane.
- 2026-03-11: `S2-02` moved assign target planning plus `_lower_assignment_like_stmt`, `_lower_for_stmt`, `_lower_forrange_stmt`, and `_lower_forcore_stmt` into `east2_to_east3_stmt_lowering.py`. Source-contract coverage now asserts stmt-module ownership, and split regressions gained a representative `Box + StaticRangeForPlan` lane.
