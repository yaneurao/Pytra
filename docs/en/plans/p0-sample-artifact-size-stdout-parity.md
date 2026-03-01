# P0: Introduce `artifact_size` stdout parity for sample image artifacts

Last updated: 2026-02-28

Related TODO:
- `ID: P0-SAMPLE-ARTIFACT-SIZE-01` in `docs/ja/todo/index.md`

Background:
- Current `runtime_parity_check` mainly compares stdout and does not directly verify content equality of image artifacts (PNG/GIF).
- Full binary equality checks (CRC/sha) are useful long-term, but we want to avoid spec/implementation bloat at this stage.
- We tried adding `Path(...).stat().st_size` directly to sample code, but confirmed it breaks compatibility because some backends (C++/Ruby, etc.) do not support `Path.stat()`.

Goal:
- Enable `runtime_parity_check` to directly compare artifact sizes in image-output cases, so regressions that stdout-only checks miss can fail.

In scope:
- Artifact comparison spec in `tools/runtime_parity_check.py` (real file-size comparison from `output:`)
- Related smoke/parity tests

Out of scope:
- Full introduction of hash comparison such as CRC/sha
- Generalization to non-image artifacts
- Adding backend-incompatible `Path.stat()` dependent code into sample code

Acceptance criteria:
- Using actual artifact file size from Python execution `output:` as baseline, each backend can detect size mismatches.
- Cases with non-generated/missing artifacts or missing output lines can fail in `runtime_parity_check`.
- `runtime_parity_check --case-root sample --all-samples` remains non-regressive in existing pass scope.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_runtime_parity_check_cli.py' -v`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp 01_mandelbrot --ignore-unstable-stdout`

Decision log:
- 2026-02-28: Per user instruction, opened a P0 plan to introduce `artifact_size` stdout output as an alternative to full binary comparison.
- 2026-02-28: Rolled back the plan to add `Path(out_path).stat().st_size` to `sample/py` because execution fails on backends that do not support `Path.stat()` (C++/Ruby).
- 2026-02-28: Pivoted to resolving actual artifact files from `output:` within `runtime_parity_check` and comparing size (`presence/missing/size mismatch`).
- 2026-02-28: Added `artifact_size_mismatch` regression to `test_runtime_parity_check_cli.py` and confirmed non-regression via sample parity runs (ruby 18 cases, cpp 01).

## Breakdown

- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S1-01] Inventory image-output sample cases and pin artifact comparison targets (cases with `output:` lines).
- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S2-01] Add logic in `runtime_parity_check` to resolve Python-baseline artifacts and read actual file sizes.
- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S2-02] Add target-run artifact presence/size comparison (including stale-file guard).
- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S3-01] Update `runtime_parity_check` regression tests and pin `artifact_size_mismatch`.
- [x] [ID: P0-SAMPLE-ARTIFACT-SIZE-01-S3-02] Re-run sample parity and confirm non-regression with size-mismatch detection enabled.
