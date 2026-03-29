<a href="../../../ja/plans/archive/20260313-p0-link-facade-linked-program-module-import.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: align `LinkedProgramModule` imports to the `toolchain.link` facade

Last updated: 2026-03-13

Related TODO:
- `ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01` in `docs/en/todo/index.md`

Background:
- The `toolchain.link` facade already exports `LinkedProgramModule`.
- Even so, [`tools/unittest/tooling/test_py2x_cli.py`](/workspace/Pytra/tools/unittest/tooling/test_py2x_cli.py) still imports it directly from `src.toolchain.link.program_model`.
- The same consumer lane in [`src/ir2lang.py`](/workspace/Pytra/src/ir2lang.py) already uses the facade import, so the `py2x` tooling test is the remaining reach-through import.

Goal:
- Align the `LinkedProgramModule` import in `test_py2x_cli.py` to go through the `src.toolchain.link` facade.
- Add a source contract so a regression back to direct `program_model` imports fails fast.

In scope:
- `tools/unittest/tooling/test_py2x_cli.py`
- `tools/unittest/common/test_py2x_entrypoints_contract.py`
- `docs/en/todo/index.md` and the Japanese mirror

Out of scope:
- Changing the internals of `toolchain.link.program_model`
- Bulk-cleaning other exports such as `LinkedProgram` or `LINK_INPUT_SCHEMA`
- Reworking runtime or selfhost import graphs

Acceptance criteria:
- `test_py2x_cli.py` imports `LinkedProgramModule` from the `src.toolchain.link` facade.
- A source contract detects any re-entry of direct `src.toolchain.link.program_model` imports.
- The focused unit suite is green.

Verification commands:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/tools/unittest/common/test_py2x_entrypoints_contract.py`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/tools/unittest/tooling/test_py2x_cli.py`
- `python3 /workspace/Pytra/tools/check/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

Breakdown:
- [x] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01] Align the `LinkedProgramModule` import in `test_py2x_cli.py` to the `src.toolchain.link` facade so the tooling consumer no longer reaches through `program_model` directly.
- [x] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01-S1-01] Add the facade-import source contract plus TODO/plan baseline.
- [x] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01-S2-01] Switch the `test_py2x_cli.py` import to the facade path and bring the focused unit suite back to green.
- [x] [ID: P0-LINK-FACADE-LINKED-PROGRAM-MODULE-IMPORT-01-S3-01] Sync TODO / plan / archive and lock the close condition.

Decision log:
- 2026-03-13: Filed this follow-up P0 after TODO became empty, limiting scope to the direct `program_model` import that remains in the tooling test consumer lane.
- 2026-03-13: `S1-01/S2-01` switched `test_py2x_cli.py` to `from src.toolchain.link import LinkedProgramModule` and added a source contract in `test_py2x_entrypoints_contract.py` so a regression back to the direct `program_model` import fails fast.
- 2026-03-13: `S3-01` synchronized the active TODO, plan, and archive, and fixed the close condition as “`test_py2x_cli.py` imports `LinkedProgramModule` from the `src.toolchain.link` facade while both the source contract and the focused tooling unit stay green.” Any wider `program_model` export cleanup is deferred.
