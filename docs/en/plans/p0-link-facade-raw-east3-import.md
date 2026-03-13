# P0: align external `validate_raw_east3_doc` imports to the `toolchain.link` facade

Last updated: 2026-03-13

Related TODO:
- `ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01` in `docs/en/todo/index.md`

Background:
- The `toolchain.link` facade already exports `validate_raw_east3_doc`.
- Even so, `src/toolchain/ir/east3.py` and the focused regression in [`test/unit/common/test_frontend_type_expr.py`](/workspace/Pytra/test/unit/common/test_frontend_type_expr.py) still import `toolchain.link.program_validator` directly.
- Leaving those external consumers on submodule reach-through keeps unnecessary coupling to the internal location of `program_validator` and conflicts with the facade policy reinforced by the previous task.

Goal:
- Align the remaining external `validate_raw_east3_doc` consumers to import through the `toolchain.link` facade.
- Add runtime regression plus a source contract so a regression back to reach-through imports fails fast.

In scope:
- `src/toolchain/ir/east3.py`
- `test/unit/common/test_frontend_type_expr.py`
- `test/unit/common/test_py2x_entrypoints_contract.py` if needed

Out of scope:
- Reworking internal imports within the `toolchain.link` package
- Changing `validate_raw_east3_doc` behavior
- Bulk-cleaning every other validator helper import in one task

Acceptance criteria:
- `toolchain.ir.east3` imports `validate_raw_east3_doc` from the `toolchain.link` facade.
- The focused regression is green with the facade import path.
- A source contract detects any re-entry of direct `toolchain.link.program_validator` imports for this external lane.

Verification commands:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 test/unit/common/test_frontend_type_expr.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 test/unit/common/test_py2x_entrypoints_contract.py -k dynamic_carrier_seams_are_explicitly_isolated`
- `python3 /workspace/Pytra/tools/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

Breakdown:
- [ ] [ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01] Move `validate_raw_east3_doc` imports in `toolchain.ir.east3` and the focused tests over to the `toolchain.link` facade so external consumers stop reaching through `toolchain.link.program_validator` directly.
- [ ] [ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01-S1-01] Add focused regression / source-contract coverage that requires the facade import and locks the current reach-through surface in fail-fast form.
- [ ] [ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01-S2-01] Switch `toolchain.ir.east3` plus the focused test imports over to the facade path and bring the targeted unit suite back to green.
- [ ] [ID: P0-LINK-FACADE-RAW-EAST3-IMPORT-01-S3-01] Sync TODO / plan / decision log and lock the close condition.

Decision log:
- 2026-03-13: Filed this follow-up P0 after TODO became empty, keeping scope limited to the external `validate_raw_east3_doc` consumers. The task deliberately avoids reorganizing the internal imports inside `toolchain.link` itself.
