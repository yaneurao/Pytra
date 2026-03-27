<a href="../../ja/plans/p0-php-s13-parity-investigation.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P0: Investigate `sample/13` PHP Parity Mismatch (`frames 147 -> 2`)

Last updated: 2026-03-04

Related TODO:
- `ID: P0-PHP-S13-PARITY-INVEST-01` in `docs/ja/todo/index.md`

Background:
- In the latest run of `tools/runtime_parity_check.py --case-root sample --all-samples --targets ruby,lua,scala,php`, only one failure remained: PHP on `sample/13`.
- The failure is stdout mismatch: expected Python value `frames: 147` vs observed PHP value `frames: 2`.
- PHP execution for `sample/16` / `sample/18` passes, so this is likely not a broad PHP backend outage but a conversion-path mismatch specific to `sample/13`.

Goal:
- Identify the root cause of why PHP output for `sample/13` becomes `frames: 2`.
- Isolate the responsible layer (`EAST3 / lower / emitter / runtime / sample side`).
- Finalize a minimal repro case and remediation policy to proceed to implementation.

In scope:
- `sample/py/13_maze_generation_steps.py`
- `sample/php/13_maze_generation_steps.php` (regenerate if needed)
- PHP backend (lower / emitter)
- PHP runtime (GIF output, array handling, loop-related helpers)
- Parity log (`work/logs/runtime_parity_sample_ruby_lua_scala_php_20260304.json`)

Out of scope:
- Redesigning parity across all 4 languages
- PHP performance optimization
- Updating README runtime table

Acceptance criteria:
- The direct cause of `frames: 147 -> 2` can be explained with code locations.
- The first divergence point from Python can be shown (data or control).
- A minimal repro case proposal is finalized.
- Findings are organized enough to open follow-up fix tasks (implementation IDs).

Verification commands (planned):
- `python3 tools/runtime_parity_check.py --case-root sample --targets php 13_maze_generation_steps`
- `python3 tools/regenerate_samples.py --langs php --stems 13_maze_generation_steps --force`
- `php sample/php/13_maze_generation_steps.php`
- `python3 sample/py/13_maze_generation_steps.py`

Decision log:
- 2026-03-04: Per user instruction, opened this as P0 root-cause investigation for `sample/13` PHP parity failure (`frames: 147 -> 2`).
- 2026-03-04: Reproduced `output mismatch (frames: 147 -> 2)` with `python3 tools/runtime_parity_check.py --case-root sample --targets php 13_maze_generation_steps`, and fixed the failure log at `work/logs/runtime_parity_sample_php_13_invest_20260304.json`.
- 2026-03-04: Compared generated PHP and identified first divergence as unsupported negative index for `stack[-1]` (emitted directly as `$stack[-1]`). Confirmed that `Undefined array key -1` occurs at PHP runtime, search is exhausted immediately, and `frames: 2` results.
- 2026-03-04: Also confirmed concurrent factor: unsupported `ListComp` (`_render_expr` fallback `null`). In minimal repro `/tmp/php_s13_min_repro.py`, `grid = [[1] * w for _ in range(h)]` degrades to `$grid = null`.
- 2026-03-04: Switched directly from repair policy to implementation: added `ListComp(range)` expansion to PHP emitter for `AnnAssign/Assign`, added list-repeat path (`__pytra_list_repeat`) for `BinOp Mult`, and added `__pytra_index` / `__pytra_list_repeat` in runtime.
- 2026-03-04: Confirmed `sample/13` parity `ok` for PHP-only (`work/logs/runtime_parity_sample_php_13_after_negindex_fix_20260304.json`) and also `ok` in side-by-side `ruby,lua,scala,php` (`work/logs/runtime_parity_sample_ruby_lua_scala_php_case13_after_php_fix_20260304.json`). No separate follow-up task is required (fixed within this ID).

## Breakdown

- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S1-01] Reproduce parity failure (stdout mismatch) in isolation, and collect minimal execution logs/artifacts.
- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S1-02] Compare `frames` calculation paths between Python and PHP, and identify the first divergence point.
- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S2-01] Pinpoint one responsible layer among `EAST3 / lower / emitter / runtime`.
- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S2-02] Draft a minimal repro case and decide regression-test granularity.
- [x] [ID: P0-PHP-S13-PARITY-INVEST-01-S3-01] Finalize fix policy (implementation points, out-of-scope items, verification viewpoints) and open follow-up fix tasks.
