<a href="../../ja/plans/p0-php-image-runtime-and-s16-repair.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Implement PHP Image Runtime and Repair `sample/16` Execution Failure

Last updated: 2026-03-04

Related TODO:
- `ID: P0-PHP-IMAGE-RUNTIME-S16-01` in `docs/ja/todo/index.md`

Background:
- The PHP backend image-output helpers are currently no-op and do not generate PNG/GIF artifacts.
- `sample/php/16_glass_sculpture_chaos.php` references unbound variables (`$fwd_x/$fwd_y/$fwd_z/$right_*`, etc.) and stops with `DivisionByZeroError`.
- In parity validation, we need to explicitly exclude stale artifact reuse possibility.

Goal:
- Make the PHP backend actually write PNG/GIF artifacts.
- Make `sample/16` run successfully in PHP and reach `elapsed_sec`.
- During parity validation, always delete existing artifacts before execution to prevent false positives.

In scope:
- `src/runtime/php/pytra/runtime/png.php`
- `src/runtime/php/pytra/runtime/gif.php`
- Image-save lowering in PHP backend (remove `__pytra_noop` path)
- Tuple/multi-return receive lowering in PHP backend (root cause of unbound vars in `sample/16`)
- Artifact cleanup in `tools/check/runtime_parity_check.py`

Out of scope:
- Overall PHP backend performance optimization
- Simultaneous runtime changes for other languages
- Refreshing README runtime table (handled in a separate task)

Acceptance criteria:
- In PHP execution, `sample/01` (PNG) and `sample/06` (GIF) actually generate artifacts.
- `sample/16` completes in PHP and outputs `output:` and `elapsed_sec:`.
- In parity, stale artifacts are always deleted before each sample case run (enforced in code).
- `runtime_parity_check --case-root sample --targets php --all-samples` is evaluated without artifact false positives at minimum.

Verification commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/gen/regenerate_samples.py --langs php --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets php --all-samples`
- `python3 tools/check/check_py2php_transpile.py`

Decision log:
- 2026-03-03: Per user instruction, opened this as P0 for missing PHP image runtime implementation and `sample/16` execution failure.
- 2026-03-03: Chose explicit implementation of "delete artifact every run" in `runtime_parity_check.py` to prevent parity false positives.
- 2026-03-03: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S1-01] Audited no-op dependencies and confirmed by execution reproduction the path `emitter -> __pytra_noop -> runtime stub(return null)` and tuple-receive breakage in `sample/16` (unbound vars -> `DivisionByZeroError`).
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-01] Added pure-PHP implementation to `src/runtime/php/pytra/runtime/png.php` (CRC32/Adler32/stored-deflate), and confirmed PNG byte-level match with Python implementation (SHA-256 match) on `1x1 RGB`.
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-02] Added GIF89a writer implementation to `src/runtime/php/pytra/runtime/gif.php` (Clear/Literal LZW, Netscape loop extension), and confirmed GIF byte-level match with Python implementation (SHA-256 match) on `2x1x2frames`.
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-03] Switched PHP emitter `save_gif` / `write_rgb_png` from `__pytra_noop` to `__pytra_save_gif` / `__pytra_write_rgb_png`, and confirmed image generation in regenerated outputs and execution of `sample/01` and `sample/06`.
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-04] Implemented tuple/list unpack assignment in PHP emitter `Assign`, resolving unbound-variable chain in `sample/16` (`fwd_*`, `right_*`, `dy`, etc.). Confirmed regenerated `sample/16` runs to completion with empty `stderr`.
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-01] Confirmed in actual code that `_purge_case_artifacts()` in `runtime_parity_check.py` is always called at case start and before each target run, verifying always-on artifact false-positive prevention.
- 2026-03-04: [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-02] Removed `ignore_artifacts=True` from PHP target in `runtime_parity_check.py`, and confirmed stdout/artifact parity passes for all `sample/01,06,16` (3/3) on `--targets php`.

## Breakdown

- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S1-01] Audit no-op dependency points in PHP image output path (runtime/emit).
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-01] Add Python-compatible PNG writer implementation to `png.php`.
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-02] Add Python-compatible GIF writer implementation to `gif.php`.
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-03] Switch PHP emitter/lower `save_gif` / `write_rgb_png` from `__pytra_noop` to real runtime calls.
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S2-04] Fix tuple receive in PHP emitter/lower and resolve unbound-variable references in `sample/16`.
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-01] Enforce artifact deletion before case execution in `runtime_parity_check.py` and close false-positive path.
- [x] [ID: P0-PHP-IMAGE-RUNTIME-S16-01-S3-02] Re-verify Python vs PHP stdout/artifact parity with focus on `sample/01,06,16`.

## S1-01 Inventory Results

- `src/toolchain/emit/php/emitter/php_native_emitter.py`:
  - `save_gif` / `write_rgb_png` calls are forcibly converted to `__pytra_noop(...)` (two locations: function-call path and attribute-call path).
- `src/runtime/php/pytra/runtime/png.php`:
  - `__pytra_write_rgb_png(...)` had no implementation and only `return null;`.
- `src/runtime/php/pytra/runtime/gif.php`:
  - `__pytra_save_gif(...)` had no implementation and only `return null;`.
- `src/runtime/php/pytra/py_runtime.php`:
  - `__pytra_noop(...$_args)` is defined and is the sink for image-save calls.
- Generated `sample/php`:
  - `sample/php/{01,03,04}` outputs `__pytra_noop(...)` at PNG output points.
  - `sample/php/{05..16}` outputs `__pytra_noop(...)` at GIF output points.
- `sample/php/16_glass_sculpture_chaos.php` execution result:
  - Running `php sample/php/16_glass_sculpture_chaos.php` produced chained unbound-variable warnings (`$fwd_x/$fwd_y/$fwd_z/$right_*`, etc.) and finally stopped with `DivisionByZeroError`.
  - Confirmed tuple-receive lowering breakage as a real runtime impact.
