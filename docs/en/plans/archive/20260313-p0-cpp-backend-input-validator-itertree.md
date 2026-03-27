<a href="../../../ja/plans/archive/20260313-p0-cpp-backend-input-validator-itertree.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: fix the C++ backend input validator drift against the object-tree iterator API

Last updated: 2026-03-13

Related TODO:
- `ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01` in `docs/en/todo/archive/20260313.md`

Background:
- `_iter_object_tree()` in `src/toolchain/link/program_validator.py` was extended so raw object-tree walks now yield `parent_key` as well.
- The raw EAST3 validator was updated to the new API, but `validate_cpp_backend_input_doc()` still kept the old two-value unpack.
- As a result, even a minimal valid module can stop immediately with `too many values to unpack` before the C++ backend-input validation reaches its real checks. This sits directly under the typed-boundary path that validates C++ backend carrier input.

Goal:
- Bring `validate_cpp_backend_input_doc()` in sync with the current `_iter_object_tree()` API.
- Lock the current crash surface in a focused regression so future iterator-signature drift fails fast in link-stage validation.
- Preserve the existing `ForCore.iter_plan` metadata guard and error wording.

In scope:
- `src/toolchain/link/program_validator.py`
- `test/unit/link/test_program_loader.py`
- TODO / plan progress sync

Out of scope:
- Redesigning the entire raw EAST3 validator
- Non-C++ backend-input validation
- Changing the `ForCore` metadata contract itself

Acceptance criteria:
- Passing a minimal valid raw EAST3 module into `validate_cpp_backend_input_doc()` no longer fails with a tuple-unpack error.
- `validate_cpp_backend_input_doc()` consumes `_iter_object_tree()` with `parent_key` while preserving the existing `ForCore` metadata validation behavior.
- The targeted link regression is green.

Verification commands:
- `PYTHONPATH=/workspace/Pytra:/workspace/Pytra/src python3 -m unittest discover -s /workspace/Pytra/test/unit/link -p 'test_program_loader.py'`
- `python3 /workspace/Pytra/tools/check_todo_priority.py`
- `git -C /workspace/Pytra diff --check`

Breakdown:
- [x] [ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01] Bring `validate_cpp_backend_input_doc()` in sync with the `_iter_object_tree()` API that now yields `parent_key`, so typed-boundary / backend-input validation no longer stops on tuple-unpack errors.
- [x] [ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01-S1-01] Add a focused regression around a minimal raw EAST3 module and lock the current C++ backend-input crash surface in fail-fast form.
- [x] [ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01-S2-01] Switch `validate_cpp_backend_input_doc()` to the `parent_key`-aware object-tree iteration while preserving the existing `ForCore` metadata guard, then bring the targeted link test back to green.
- [x] [ID: P0-CPP-BACKEND-INPUT-VALIDATOR-ITERTREE-01-S3-01] Sync TODO / plan / decision log and lock the close condition.

Decision log:
- 2026-03-13: Filed this as the next P0 after TODO became empty, keeping the scope narrowly on the converter-core regression where `validate_cpp_backend_input_doc()` failed to follow the `_iter_object_tree()` signature change instead of reopening raw-EAST3 validation as a whole.
- 2026-03-13: `S1-01/S2-01` placed a focused link-stage regression in `test_program_loader.py` by feeding a minimal `Module` input directly into `validate_cpp_backend_input_doc()`. The implementation change is intentionally narrow: accept `parent_key` from `_iter_object_tree()` and keep the existing `ForCore.iter_plan` validation and error wording intact.
- 2026-03-13: `S3-01` synchronized the live TODO, archive, and archived plan, and locked the close condition as “a minimal `Module` input reaches the real validator without tuple-unpack failure while the focused link regression and TODO-priority checks stay green.” No further validator behavior change was added beyond the existing `program_validator.py` fix.
