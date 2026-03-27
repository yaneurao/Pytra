<a href="../../ja/plans/p1-nim-sample-parity-complete.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: Complete Nim sample parity and integrate it formally into `runtime_parity_check`

Last updated: 2026-03-04

Related TODO:
- `ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01` in `docs/ja/todo/index.md`

Background:
- Nim previously had a record of passing sample parity, but the current `build_targets()` in `tools/runtime_parity_check.py` does not contain a `nim` target, so Nim has dropped out of continuous regression coverage.
- The source of truth for PNG and GIF support is `src/pytra/utils/png.py` and `src/pytra/utils/gif.py`. The project does not allow adding handwritten implementations to per-language runtimes.
- A handwritten PNG/GIF implementation was recently added to the Nim runtime, which violates the source-of-truth policy and must be corrected.
- `tools/regenerate_samples.py` also lacks Nim support, so the regeneration path for `sample/nim` is not fixed.

Goal:
- Restore Nim as an official target in `runtime_parity_check` and make all 18 samples pass with matching stdout and artifacts, size plus CRC32.
- Fix Nim regeneration and verification paths in tooling so future regressions are detected automatically.

Scope:
- `tools/runtime_parity_check.py`, add the Nim target
- `tools/regenerate_samples.py`, add Nim support
- `src/runtime/nim/pytra/py_runtime.nim`, remove handwritten code and switch to source-of-truth-derived generation
- `src/pytra/utils/png.py` and `src/pytra/utils/gif.py`, only the smallest Nim-compat fixes if needed
- `src/toolchain/emit/nim/emitter/nim_native_emitter.py`, only the parts needed to connect runtime contracts
- `test/unit/test_runtime_parity_check_cli.py` and Nim-related smoke tests

Out of scope:
- Nim backend performance optimization
- Parity fixes for non-Nim backends
- Updating the runtime table in the README

Acceptance criteria:
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304.json` reports `case_pass=18` and `case_fail=0`.
- In that log, `category_counts` contains only `ok`, with `output_mismatch`, all `artifact_*`, `run_failed`, and `toolchain_missing` all at zero.
- `python3 tools/regenerate_samples.py --langs nim --force` succeeds, fixing Nim regeneration as an official path.
- After Nim is added, existing parity CLI tests and Nim transpile and smoke tests still pass without regression.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/regenerate_samples.py --langs nim --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_rebaseline_20260304.json`
- `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304.json`
- `python3 tools/check_py2nim_transpile.py`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_py2nim_smoke.py' -v`
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v`

Decision log:
- 2026-03-04: On user instruction, created this P1 plan for completing Nim parity.
- 2026-03-04: Completed `S1-01`. Added the `nim` target to `build_targets()` in `tools/runtime_parity_check.py` and added Nim entry verification to `test/unit/tooling/test_runtime_parity_check_cli.py`. To handle Nim's module-name restriction, no leading digits, parity runs now emit to `work/transpile/nim/case_<stem>.nim`.
- 2026-03-04: Completed `S1-02`. Added `nim` to `tools/regenerate_samples.py` and added `languages.nim` to `src/toolchain/misc/transpiler_versions.json`. `python3 tools/regenerate_samples.py --langs nim --force` confirmed `summary: total=18 skip=0 regen=18 fail=0`.
- 2026-03-04: Completed `S1-03`. Ran `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_rebaseline_20260304.json` and fixed the baseline as `case_pass=0/case_fail=18`, with categories `run_failed=16` and `output_mismatch=2`.
- 2026-03-04: Completed `S2-01`. Replaced the `write_rgb_png` stub in `src/runtime/nim/pytra/py_runtime.nim` with a pure Nim implementation, CRC32, Adler32, zlib stored block, and PNG chunk assembly. `work/logs/runtime_nim_png_crc_check_20260304.json` confirmed `size+crc32` match for the PNG artifact of `sample/01`, `artifact_match=true`.
- 2026-03-04: Completed `S2-02`. Added `grayscale_palette`, `save_gif`, and GIF-side LZW helpers to the Nim runtime, and `work/logs/runtime_nim_gif_crc_check_20260304.json` confirmed `size+crc32` match against the Python source-of-truth output, `artifact_match=true`.
- 2026-03-04: Operational correction. PNG and GIF are allowed only as outputs generated from the Python source of truth, so the above handwritten completion for `S2-01/S2-02` was invalidated. Those tasks were reopened as unfinished work to remove handwritten code and replace it with source-of-truth-derived output.
- 2026-03-04: Re-implemented and completed `S2-01/S2-02/S2-03/S2-04`. Added support in `nim_native_emitter` for `IfExp`, `RangeExpr`, `Unbox`, `ObjLen`, `ObjStr`, `ObjBool`, `In`, `NotIn`, tuple targets, `enumerate`, bit operations, `range(step)`, automatic class constructors and method forward declarations, and `declare` scope control. Added `py_range`, `py_isdigit`, and `py_isalpha` to `py_runtime.nim` to restore Python-compatible behavior.
- 2026-03-04: Completed `S3-01`. `python3 tools/runtime_parity_check.py --case-root sample --targets nim --all-samples --summary-json work/logs/runtime_parity_sample_nim_all_pass_20260304_after_emitter_fixes.json` confirmed `case_pass=18/case_fail=0`, `ok=18`.
- 2026-03-04: Completed `S3-02`. Re-ran `check_py2nim_transpile`, `test_py2nim_smoke`, and `test_runtime_parity_check_cli` to confirm non-regression.
- 2026-03-04: Completed `S3-03`. Added the final logs and correction policy to this plan and documented the closure conditions for Nim parity.

## Breakdown

- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-01] Add the Nim target to `runtime_parity_check`, transpile, run, and toolchain detection, so a baseline run is possible.
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-02] Add Nim to `regenerate_samples.py` and fix the regeneration path for `sample/nim`.
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S1-03] Run parity on all Nim samples and fix the failure categories, stdout, artifacts, and runtime execution.
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-01] Remove the handwritten PNG writer from the Nim runtime and replace it with generated output derived from `src/pytra/utils/png.py`.
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-02] Remove the handwritten GIF writer from the Nim runtime and replace it with generated output derived from `src/pytra/utils/gif.py`.
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-03] Align the Nim emitter and lowering image-output path with the runtime function contract, function names and argument types.
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S2-04] Isolate the remaining failing cases, for example `sample/18`, and fix them with the smallest possible language-feature adjustments.
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-01] Re-run `--targets nim --all-samples` and confirm `case_pass=18` and `case_fail=0`.
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-02] Update regression coverage for the Nim parity contract, CLI, smoke, and transpile, and fix recurrence prevention.
- [x] [ID: P1-NIM-SAMPLE-PARITY-COMPLETE-01-S3-03] Record verification logs and operating procedure in the plan and state the close conditions explicitly.
