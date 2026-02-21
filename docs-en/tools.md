# `tools/` Script Index

<a href="../docs/tools.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>


`tools/` is a set of helper scripts that automates Pytra development operations.  
Its goals are:

- Enable quick, repeatable regression checks.
- Standardize selfhost investigation, comparison, and build workflows.
- Update and validate generated C++ runtime artifacts from the `src/pytra/` source of truth.

## 1. Daily Operations

- `tools/run_local_ci.py`
  - Purpose: Run minimal local CI in one pass (transpile regressions + unit tests + selfhost build + diff).
- `tools/check_py2cpp_transpile.py`
  - Purpose: Batch-transpile `test/fixtures/` with `py2cpp.py` and detect failures.
- `tools/verify_sample_outputs.py`
  - Purpose: Compare Python and C++ execution results for `sample/py` (`stdout`/images).
  - Main options: `--samples`, `--compile-flags`, `--ignore-stdout`
- `tools/verify_image_runtime_parity.py`
  - Purpose: Verify parity between Python source-of-truth image runtime (PNG/GIF) and C++ side.

## 2. Selfhost Related

- `tools/build_selfhost.py`
  - Purpose: Build `selfhost/py2cpp.out` for selfhost.
- `tools/prepare_selfhost_source.py`
  - Purpose: Expand `CodeEmitter` and related pieces into selfhost-ready source for self-contained execution.
- `tools/selfhost_transpile.py`
  - Purpose: Run `.py -> EAST JSON -> selfhost` path as a temporary bridge.
- `tools/check_selfhost_cpp_diff.py`
  - Purpose: Compare generated C++ diffs between Python and selfhost versions.
  - Main options: `--mode allow-not-implemented`, `--show-diff`, `--selfhost-driver`
- `tools/summarize_selfhost_errors.py`
  - Purpose: Aggregate selfhost build errors by category.
- `tools/selfhost_error_hotspots.py`
  - Purpose: Aggregate error hotspots by function.
- `tools/selfhost_error_report.py`
  - Purpose: Format and output reports from selfhost error analyses.

## 3. Cross-Language Verification

- `tools/runtime_parity_check.py`
  - Purpose: Run runtime normalization/parity checks across multiple target languages.

## 4. Update Rules

- When adding a new script under `tools/`, update this `docs/tools.md` at the same time.
- For each script, explicitly state in one line what automation purpose it serves.
- If there are breaking changes (argument changes, deprecations, consolidation), synchronize related command examples in `docs/how-to-use.md`.

