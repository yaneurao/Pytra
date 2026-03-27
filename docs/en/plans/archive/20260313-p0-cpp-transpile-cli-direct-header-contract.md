<a href="../../../ja/plans/archive/20260313-p0-cpp-transpile-cli-direct-header-contract.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: align the `transpile_cli` typed C++ contract to the direct-ownership header/source layout

Last updated: 2026-03-13

Related TODO:
- `ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01` in `docs/en/todo/index.md`

Background:
- `test_compiler_transpile_cli_typed_shim_skips_legacy_wrapper()` in `test/unit/common/test_py2x_entrypoints_contract.py` still tries to read `src/runtime/cpp/pytra/compiler/transpile_cli.h` as though a checked-in public wrapper still exists.
- In the live tree, that checked-in `src/runtime/cpp/pytra/compiler/transpile_cli.h` file is already gone, while `src/runtime/cpp/generated/compiler/transpile_cli.h` and `src/runtime/cpp/generated/compiler/transpile_cli.cpp` are the direct-ownership artifacts for the typed shim.
- `docs/ja/spec/spec-runtime.md` already fixes the C++ contract as `public_headers == compiler_headers` on the direct-ownership header, so this focused contract test is the stale assumption that remains behind.

Goal:
- Align the focused `transpile_cli` typed-shim C++ contract to the current `generated/native` direct-ownership layout.
- Stop requiring the deleted checked-in `cpp/pytra` wrapper in the source contract.

In scope:
- `test/unit/common/test_py2x_entrypoints_contract.py`
- Related plan / TODO / archive records if needed

Out of scope:
- Changing `transpile_cli.py` behavior itself
- Reworking the C++ runtime packaging design
- Bulk-reviewing other compiler modules such as `backend_registry_static`

Acceptance criteria:
- The focused contract test treats the absence of `src/runtime/cpp/pytra/compiler/transpile_cli.h` as the expected state.
- The same test validates the live contract for `src/runtime/cpp/generated/compiler/transpile_cli.h` and `src/runtime/cpp/generated/compiler/transpile_cli.cpp`.
- The typed shim still guards the direct call into `_front.load_east3_document_typed(...)`.

Verification commands:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 /workspace/Pytra/test/unit/common/test_py2x_entrypoints_contract.py -k typed_shim_skips_legacy_wrapper`
- `python3 /workspace/Pytra/tools/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

Breakdown:
- [x] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01] Remove the checked-in `cpp/pytra` wrapper assumption from the `transpile_cli` typed C++ contract and align it to the `generated/native` direct-ownership header/source layout.
- [x] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01-S1-01] Lock the stale contract surface and close condition in the plan / TODO.
- [x] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01-S2-01] Update the focused contract test to match the live tree and bring the targeted test back to green.
- [x] [ID: P0-CPP-TRANSPILE-CLI-DIRECT-HEADER-CONTRACT-01-S3-01] Sync TODO / plan / archive and lock the close condition.

Decision log:
- 2026-03-13: Filed this as the next follow-up P0 after TODO became empty. The live tree already owns `generated/compiler/transpile_cli.{h,cpp}` and no longer owns `cpp/pytra/compiler/transpile_cli.h`, so the task is limited to removing stale assumptions from the source contract instead of changing the runtime layout again.
- 2026-03-13: `S2-01` updated `test_compiler_transpile_cli_typed_shim_skips_legacy_wrapper()` so the deleted `src/runtime/cpp/pytra/compiler/transpile_cli.h` is treated as expected-missing. The test now validates the live ownership contract directly through `generated/compiler/transpile_cli.h` and `generated/compiler/transpile_cli.cpp`.
- 2026-03-13: `S3-01` synchronized the active TODO, plan, and archive, and fixed the close condition as “the typed shim still forwards directly to `_front.load_east3_document_typed(...)`, the checked-in `cpp/pytra/compiler/transpile_cli.h` wrapper stays absent, and `generated/compiler/transpile_cli.{h,cpp}` represent the live contract.”
