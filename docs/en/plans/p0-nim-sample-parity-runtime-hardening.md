<a href="../../ja/plans/p0-nim-sample-parity-runtime-hardening.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Harden Nim Runtime and Pass Full `sample/` Parity

Last updated: 2026-03-03

Related TODO:
- `ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01` in `docs/ja/todo/index.md`

Background:
- `py2nim.py` and minimal smoke tests are in place, but evidence for full parity pass across all `sample/` cases is not yet locked.
- Nim backend was introduced recently, so missing runtime APIs or call-contract mismatches are still likely.
- While `sample/` parity is unstable, we cannot proceed with README quality metrics or optimization planning for the Nim backend.

Goal:
- Convert and run `sample/py` with Nim, and pass parity for all cases under `--ignore-unstable-stdout`.
- Fill missing pieces required for pass, mainly on runtime side, and lock recurrence detection.

In scope:
- `src/runtime/nim/pytra/py_runtime.nim`
- `src/toolchain/emit/nim/emitter/nim_native_emitter.py` (only where required for runtime-contract wiring)
- `tools/check/runtime_parity_check.py` execution path (minimal fixes only if needed)
- `sample/nim/` (regenerated outputs)
- Required unit/transpile checks

Out of scope:
- Large-scale Nim backend optimization (full generated-code quality overhaul)
- Simultaneous runtime changes for other languages
- README benchmark value updates

Acceptance criteria:
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets nim --ignore-unstable-stdout` passes all cases.
- `python3 tools/check/check_py2nim_transpile.py` passes.
- Minimal regressions for added/updated runtime contracts are locked (unit or check).

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_py2nim_transpile.py`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets nim --ignore-unstable-stdout`
- `python3 src/py2nim.py sample/py/<case>.py -o sample/nim/<case>.nim` (`regenerate_samples.py` does not support Nim)

## Breakdown

- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S1-01] Capture Nim parity baseline for all `sample` cases and finalize failed-case list and failure categories (compile/runtime/output mismatch).
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S1-02] For each failed case, isolate runtime API gaps, contract mismatches, and emitter-side issues, then fix priority order.
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S2-01] Fill missing APIs in `py_runtime.nim` (type conversion/collections/string/time/image helpers) in fail-closed style.
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S2-02] Align emitter/runtime call contracts (function name, argument order, return type), and fix outputs where needed.
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S2-03] Resolve case-specific breakages (for example tokenizer/syntax elements corresponding to `sample/18`) with minimal fixes.
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-01] Regenerate `sample/nim` and resolve all errors in Nim execution (transpile/compile/runtime).
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-02] Verify all-case pass for `runtime_parity_check --targets nim --ignore-unstable-stdout` and record results.
- [x] [ID: P0-NIM-SAMPLE-PARITY-RUNTIME-01-S3-03] Run `check_py2nim_transpile` and related regressions to confirm no regressions.

Decision log:
- 2026-03-03: Per user instruction, opened this as P0 for Nim runtime hardening and full `sample/` parity pass.
- 2026-03-03: Baseline run of `runtime_parity_check --case-root sample --targets nim --ignore-unstable-stdout` confirmed `cases=18 pass=18 fail=0`, and finalized that failed-case categories (runtime gaps/contract mismatch/emitter issues) were empty.
- 2026-03-03: Since `tools/gen/regenerate_samples.py --langs nim --force` was unsupported with `unknown language(s): nim`, updated `sample/nim` via manual regeneration path `python3 src/py2nim.py sample/py/*.py -o sample/nim/*.nim` (18 cases + `py_runtime.nim`).
- 2026-03-03: Re-ran parity after regeneration and confirmed `cases=18 pass=18 fail=0`; `python3 tools/check/check_py2nim_transpile.py` also passed with `checked=7 ok=7 fail=0`. Acceptance criteria were met without additional code changes.
