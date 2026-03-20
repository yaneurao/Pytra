# P0: Complete PHP Sample Parity (stdout + artifact CRC32)

Last updated: 2026-03-04

Related TODO:
- `ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01` in `docs/ja/todo/index.md`

Background:
- In the latest log as of 2026-03-04, `work/logs/runtime_parity_sample_php_all_after_s13_fix_20260304.json`, against 18 `sample` cases, `case_pass=10`, `case_fail=8`.
- All fails are `artifact_crc32_mismatch`, for cases `05,06,08,10,11,12,14,16`.
- In the previous combined log `work/logs/runtime_parity_sample_ruby_lua_scala_php_20260304.json`, PHP still had `stdout mismatch` on `sample/13`, so a fresh PHP-only baseline lock is required for full-completion judgment.
- User requirement prioritizes "complete PHP sample parity"; one task must close reproduce/fix/revalidate/regression-lock end-to-end.

Goal:
- Make PHP backend pass parity for all 18 `sample/py` cases (stdout + artifact size + CRC32).
- Isolate fail factors by ownership (`runtime / lower / emitter`) and lock a recurrence-safe regression path.

In scope:
- `src/runtime/php/pytra/runtime/png.php`
- `src/runtime/php/pytra/runtime/gif.php`
- `src/toolchain/emit/php/lower/**`
- `src/toolchain/emit/php/emitter/**`
- `tools/runtime_parity_check.py`
- `test/unit/test_runtime_parity_check_cli.py` (if needed)

Out of scope:
- PHP execution-speed optimization
- Updating README runtime table
- Backend changes outside PHP

Acceptance criteria:
- `python3 tools/runtime_parity_check.py --case-root sample --targets php --all-samples --summary-json work/logs/runtime_parity_sample_php_all_pass_20260304.json` yields `case_pass=18`, `case_fail=0`.
- In that log, `category_counts` contains only `ok` (`output_mismatch` / `artifact_*` / `run_failed` are 0).
- Minimal regression checks corresponding to the fixes (unit or parity path) are added so the same class of regression is detectable.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/regenerate_samples.py --langs php --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets php --all-samples --summary-json work/logs/runtime_parity_sample_php_rebaseline_20260304.json`
- `python3 tools/runtime_parity_check.py --case-root sample --targets php 05_mandelbrot_zoom 06_julia_parameter_sweep 08_langtons_ant 10_plasma_effect 11_lissajous_particles 12_sorting_visualization 14_simple_raymarching 16_glass_sculpture_chaos --summary-json work/logs/runtime_parity_sample_php_crc_focus_20260304.json`
- `python3 tools/runtime_parity_check.py --case-root sample --targets php --all-samples --summary-json work/logs/runtime_parity_sample_php_all_pass_20260304.json`

Decision log:
- 2026-03-04: Per user instruction, reopened as P0 to complete PHP parity for all samples. Adopted unmet items in existing logs (`artifact_crc32_mismatch` in 8 cases) as the baseline.

## Breakdown

- [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-01] Re-run full PHP `sample` parity and lock the latest single-target baseline (failed cases and categories).
- [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S1-02] Isolate artifact diffs for the 8 fail cases (`05,06,08,10,11,12,14,16`) per case, and classify whether root cause is `PNG/GIF runtime` or `lower/emitter`.
- [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-01] Align PHP GIF runtime (frame ordering/LZW/extension blocks) to Python implementation and resolve GIF-side CRC mismatches.
- [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-02] Revalidate PHP PNG runtime (chunk construction/compression path/CRC calculation) and fix necessary diffs.
- [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-03] Correct PHP lower/emitter image-output inputs (palette/frame/list/bytes path) and remove data diffs passed to runtime.
- [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S2-04] Verify whether `sample/13` stdout mismatch recurs; if unresolved, fix at root cause.
- [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-01] Re-run `--targets php --all-samples` and confirm `case_pass=18` / `case_fail=0`.
- [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-02] Add regression tests corresponding to fixes (unit or parity check) and lock recurrence prevention.
- [ ] [ID: P0-PHP-SAMPLE-PARITY-COMPLETE-01-S3-03] Record generated logs and decisions in this plan, and make completion criteria explicit so the TODO can be closed.
