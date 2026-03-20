# P1: Complete Nim Sample Parity (Formal Integration into `runtime_parity_check`)

Last updated: 2026-03-04

Related TODO:
- `ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01` in `docs/ja/todo/index.md`

Background:
- Nim has historical records of passing `sample` parity, but current `tools/runtime_parity_check.py` `build_targets()` does not include `nim`, so it is excluded from continuous regression validation.
- `src/runtime/nim/pytra/py_runtime.nim` is minimal: `write_rgb_png` is still a stub and `save_gif` is unimplemented, which is insufficient to match artifact cases (PNG/GIF) up to CRC32.
- `tools/regenerate_samples.py` also does not support Nim yet, so the regeneration path for `sample/nim` is not fixed.

Goal:
- Restore Nim as an official target in `runtime_parity_check` and pass all 18 `sample` cases on stdout + artifacts (size + CRC32).
- Fix Nim regeneration and verification paths in tools so future regressions are detected automatically.

In scope:
- `tools/runtime_parity_check.py` (add Nim target)
- `tools/regenerate_samples.py` (Nim support)
- `src/runtime/nim/pytra/py_runtime.nim` (missing runtime implementations for PNG/GIF, etc.)
- `src/toolchain/emit/nim/emitter/nim_native_emitter.py` (only as needed for runtime contract connection)
- `test/unit/test_runtime_parity_check_cli.py` / Nim-related smoke

Out of scope:
- Nim backend performance optimization
- Parity fixes for non-Nim backends
- README runtime-table updates

Acceptance criteria:
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304.json` reports `case_pass=18` / `case_fail=0`.
- In the log above, `category_counts` contains only `ok` (`output_mismatch` / `artifact_*` / `run_failed` / `toolchain_missing` are all 0).
- `python3 tools/regenerate_samples.py --langs nim --force` succeeds and fixes the Nim regeneration path.
- After Nim addition, existing parity CLI tests and Nim transpile/smoke remain non-regressive.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/regenerate_samples.py --langs nim --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_rebaseline_20260304.json`
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304.json`
- `python3 tools/check_py2nim_transpile.py`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2nim_smoke.py' -v`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v`

Decision log:
- 2026-03-04: Per user instruction, opened a P1 plan for Nim parity completion.

## Breakdown

- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-01] Add Nim target (transpile/run/toolchain detection) to `runtime_parity_check` and enable baseline execution.
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-02] Add Nim to `regenerate_samples.py` and fix the `sample/nim` regeneration path.
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-03] Run parity across all Nim `sample` cases and lock failure categories (stdout / artifact / run).
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-01] Implement Nim runtime PNG writer as Python-compatible binary output (size + CRC32 match).
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-02] Implement Nim runtime GIF writer (including `grayscale_palette`) and resolve GIF artifact mismatches.
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-03] Align Nim emitter/lower image-output path with runtime function contracts (function names/argument types).
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-04] Isolate remaining failed cases (for example, `sample/18`) by language-feature differences and resolve with minimal changes.
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-01] Re-run `--targets nim --all-samples` and confirm `case_pass=18` / `case_fail=0`.
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-02] Update regression tests for Nim parity contracts (CLI/smoke/transpile) and lock recurrence prevention.
- [ ] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-03] Record verification logs and operating procedure in this plan and formalize close conditions.
