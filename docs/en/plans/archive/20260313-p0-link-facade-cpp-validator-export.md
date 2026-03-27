<a href="../../../ja/plans/archive/20260313-p0-link-facade-cpp-validator-export.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: promote the C++ backend validator helpers onto the `toolchain.link` facade

Last updated: 2026-03-13

Related TODO:
- `ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01` in `docs/en/todo/index.md`

Background:
- The current `toolchain.link` package facade re-exports the main link loader / manifest / optimizer API surface, but it does not expose the C++-specific validator helpers `validate_cpp_backend_input_doc()` and `translate_cpp_backend_emit_error()`.
- Because of that, `src/toolchain/compiler/typed_boundary.py` and some tests still import through `toolchain.link.program_validator` directly.
- Those helpers are part of the canonical link-package validation seam, so keeping the public facade and the real import path split weakens the package boundary and leaves submodule-fixed dependencies behind future refactors.

Goal:
- Re-export the two C++ backend validator helpers from the `toolchain.link` facade.
- Align `typed_boundary` and the representative link test to import through the facade.
- Add source-contract coverage so any regression back to submodule reach-through fails fast.

In scope:
- `src/toolchain/link/__init__.py`
- `src/toolchain/compiler/typed_boundary.py`
- `test/unit/link/test_program_loader.py`
- `test/unit/common/test_py2x_entrypoints_contract.py` if needed

Out of scope:
- Changing validator behavior itself
- Bulk-exporting every non-C++ helper onto the facade
- Splitting or relocating `toolchain.link.program_validator`

Acceptance criteria:
- `from toolchain.link import validate_cpp_backend_input_doc` and `translate_cpp_backend_emit_error` works.
- `typed_boundary.py` stops importing `toolchain.link.program_validator` directly.
- Representative link tests / source-contract checks are green.

Verification commands:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 -m unittest discover -s /workspace/Pytra/test/unit/link -p 'test_program_loader.py'`
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 -m unittest discover -s /workspace/Pytra/test/unit/common -p 'test_py2x_entrypoints_contract.py'`
- `python3 /workspace/Pytra/tools/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

Breakdown:
- [x] [ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01] Re-export `validate_cpp_backend_input_doc()` and `translate_cpp_backend_emit_error()` from the `toolchain.link` package facade so `typed_boundary` and link tests no longer depend on submodule reach-through.
- [x] [ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01-S1-01] Add focused regression / source-contract coverage that requires the facade export and locks the current package-surface gap in fail-fast form.
- [x] [ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01-S2-01] Switch `toolchain.link.__init__` exports plus `typed_boundary` / link-test imports over to the facade path and bring the targeted unit suite back to green.
- [x] [ID: P0-LINK-FACADE-CPP-VALIDATOR-EXPORT-01-S3-01] Sync TODO / plan / decision log and lock the close condition.

Decision log:
- 2026-03-13: Filed this as the next follow-up P0 after TODO became empty, with scope limited to shrinking the mismatch between the link package facade and the real import paths for the two C++ backend validator helpers. Validator behavior itself stays unchanged.
- 2026-03-13: `S1-01/S2-01` split the contract in two places: a runtime regression in `test_program_loader.py` and a source contract in `test_py2x_entrypoints_contract.py`. The implementation itself stays narrow, limited to re-exporting from `toolchain.link.__init__` and switching `typed_boundary` to the facade path without changing `program_validator.py` behavior.
- 2026-03-13: `S3-01` synchronized the active TODO, plan, and archive, and fixed the close condition as “the `toolchain.link` facade exports the helpers, `typed_boundary` imports through the facade, and both the runtime regression and source contract stay green.” Any wider export cleanup is left for a separate follow-up.
