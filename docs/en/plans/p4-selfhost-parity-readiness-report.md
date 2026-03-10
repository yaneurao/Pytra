# P4 Selfhost Parity Readiness Report

Last updated: 2026-03-11

Related plan:
- [P4 Canonicalize backend_registry and strengthen selfhost parity gates](./p4-backend-registry-selfhost-parity-hardening.md)

Purpose:
- Keep the representative selfhost gate entrypoints in one place.
- Make it easy to distinguish `known_block` from `regression` using the shared summary vocabulary.
- Track backend readiness as an operational gate sequence instead of scattered notes.

## Representative Gates

### 1. C++ stage1 build

- Command: `python3 tools/build_selfhost.py`
- Purpose: rebuild the C++ selfhost binary from the current Python implementation and keep the minimum stage1 build green.
- Main failures:
  - `regression/build_fail`
  - `known_block/not_implemented`

### 2. C++ stage2 build / diff

- Command: `python3 tools/build_selfhost_stage2.py`
- Command: `python3 tools/check_selfhost_cpp_diff.py`
- Purpose: build stage2 from the stage1 artifact and classify artifact diffs as expected blocks or regressions.
- Main failures:
  - `known_block/not_implemented`
  - `known_block/unsupported_by_design`
  - `regression/stage2_diff_fail`
  - `regression/stage2_transpile_fail`

### 3. C++ direct end-to-end parity

- Command: `python3 tools/verify_selfhost_end_to_end.py`
- Purpose: verify stdout parity for representative samples through the selfhost binary.
- Main failures:
  - `known_block/not_implemented`
  - `known_block/preview_only`
  - `known_block/unsupported_by_design`
  - `regression/direct_compile_fail`
  - `regression/direct_run_fail`
  - `regression/direct_parity_fail`

### 4. Multilang selfhost readiness

- Command: `python3 tools/check_multilang_selfhost_suite.py`
- Purpose: summarize non-C++ stage1 / multistage readiness through shared summary blocks.
- Main details:
  - `pass`
  - `known_block/preview_only`
  - `known_block/unsupported_by_design`
  - `toolchain_missing/toolchain_missing`
  - `regression/self_retranspile_fail`

## Shared Category Contract

Top-level categories:
- `pass`
- `known_block`
- `toolchain_missing`
- `regression`

Detail categories:
- `not_implemented`
- `preview_only`
- `unsupported_by_design`
- `known_block`
- `blocked`
- `toolchain_missing`
- `stage2_diff_fail`
- `stage2_transpile_fail`
- `direct_compile_fail`
- `direct_run_fail`
- `direct_parity_fail`
- `self_retranspile_fail`

Shared sources:
- [backend_registry_diagnostics.py](/workspace/Pytra/src/toolchain/compiler/backend_registry_diagnostics.py)
- [selfhost_parity_summary.py](/workspace/Pytra/tools/selfhost_parity_summary.py)

## Current Readiness Reading

- `known_block/not_implemented`: an implementation gap that is tracked explicitly and should not be misreported as a regression.
- `known_block/preview_only`: a lane that is intentionally still preview-only.
- `known_block/unsupported_by_design`: a currently unsupported lane, including multilang runners that are not defined yet and unsupported targets.
- `toolchain_missing/toolchain_missing`: a local environment issue, not a backend-quality regression.
- `regression/*`: a representative lane is failing under the same contract that previously passed and should be triaged first.

## Routine Check Order

1. `python3 tools/check_todo_priority.py`
2. `python3 tools/build_selfhost.py`
3. `python3 tools/build_selfhost_stage2.py`
4. `python3 tools/check_selfhost_cpp_diff.py`
5. `python3 tools/verify_selfhost_end_to_end.py`
6. `python3 tools/check_multilang_selfhost_suite.py`

Notes:
- Always run `python3 tools/check_transpiler_version_gate.py` when transpiler files change.
- For representative compiler-internal changes, run `test/unit/selfhost/*.py` and `test/unit/common/test_py2x_entrypoints_contract.py` early.
