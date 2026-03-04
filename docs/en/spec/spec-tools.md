<a href="../../ja/spec/spec-tools.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# `tools/` Script Index

`tools/` is a set of helper scripts that automates Pytra development operations.  
Its goals are:

- Enable quick, repeatable regression checks.
- Standardize selfhost investigation, comparison, and build workflows.
- Update and validate generated C++ runtime artifacts from the `src/pytra/` source of truth.

## 1. Daily Operations

- `tools/run_local_ci.py`
  - Purpose: Run minimal local CI in one pass (version gates + runtime boundary guards + non-C++ emitter runtime-call guardrail + emitter forbidden runtime-implementation symbol guardrail + transpile regressions + unit tests + selfhost build + diff).
- `tools/check_py2cpp_transpile.py`
  - Purpose: Batch-transpile `test/fixtures/` with `py2x.py --target cpp` and detect failures.
- `tools/check_py2scala_transpile.py`
  - Purpose: Batch-transpile `test/fixtures/` and `sample/py` with `py2x.py --target scala` and detect failures.
- `tools/verify_sample_outputs.py`
  - Purpose: Compare C++ execution results (`stdout`/artifacts) against the golden baseline in `sample/golden/manifest.json`, so normal verification does not run Python every time.
  - Main options: `--samples`, `--compile-flags`, `--ignore-stdout`, `--golden-manifest`, `--refresh-golden`, `--refresh-golden-only`
- `tools/sync_todo_history_translation.py`
  - Purpose: Use `docs/ja/todo/archive` as source of truth and synchronize `docs/en/todo/archive` date-file stubs and index; detect sync gaps with `--check`.
- `tools/verify_image_runtime_parity.py`
  - Purpose: Verify parity between Python source-of-truth image runtime (PNG/GIF) and C++ side.
- `tools/check_runtime_std_sot_guard.py`
  - Purpose: Enforce `src/pytra/std/*.py` and `src/pytra/utils/*.py` as source of truth, and fail on handwritten runtime implementations outside `pytra-gen` (currently guarded: `json/assertions/re/typing`). It also validates the full C++ `std/utils` runtime boundary (`pytra-gen` generated files + `pytra` forwarders + `pytra-core` split implementations).
- `tools/check_emitter_runtimecall_guardrails.py`
  - Purpose: Detect newly added direct `if/elif` string branching for runtime/stdlib symbols in non-C++ emitters, and fail on entries outside `tools/emitter_runtimecall_guardrails_allowlist.txt`.
- `tools/check_emitter_forbidden_runtime_symbols.py`
  - Purpose: Detect newly added forbidden runtime-implementation symbols in `src/backends/*/emitter/*.py` (`__pytra_write_rgb_png` / `__pytra_save_gif` / `__pytra_grayscale_palette`) and fail on entries outside `tools/emitter_forbidden_runtime_symbols_allowlist.txt`.

### 1.1 Mandatory Stop-Ship Checklist for Emitter Changes

- Scope: any commit that modifies `src/backends/*/emitter/*.py`.
- Before commit, always run these three commands:
  - `python3 tools/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check_noncpp_east3_contract.py`
- If any of the three commands returns `FAIL`, treat it as Stop-Ship and do not commit/push/request review.
- During review, use this checklist:
  - [ ] Logs for all three commands are attached.
  - [ ] No newly added forbidden runtime-implementation symbols exist in `src/backends/*/emitter/*.py`.
  - [ ] Runtime/stdlib call resolution uses EAST3 canonical fields only (`runtime_call` / `resolved_runtime_call` / `resolved_runtime_source`).

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
- `tools/check_selfhost_direct_compile.py`
  - Purpose: Batch-transpile direct selfhost `.py` inputs and run `g++ -fsyntax-only` to detect compile regressions quickly.
- `tools/summarize_selfhost_errors.py`
  - Purpose: Aggregate selfhost build errors by category.
- `tools/selfhost_error_hotspots.py`
  - Purpose: Aggregate error hotspots by function.
- `tools/selfhost_error_report.py`
  - Purpose: Format and output reports from selfhost error analyses.

## 3. Cross-Language Verification

- `tools/runtime_parity_check.py`
  - Purpose: Run runtime normalization/parity checks across multiple target languages.
  - Note: Unstable timing lines such as `elapsed_sec` / `elapsed` / `time_sec` are excluded from compare by default.
  - Note: Artifact parity requires all of `exists + size + CRC32` on the `output:` artifact path.
  - Note: Before each case run, stale artifacts with the same stem are purged from `sample/out`, `test/out`, and `out`.
  - Note: Timeout handling kills the whole process group so child runners (for example `*_swift.out`) cannot leak.
- `tools/check_scala_parity.py`
  - Purpose: Run Scala3 parity in one command for all `sample` cases and the positive fixture manifest.
  - Main options: `--skip-fixture`, `--fixture-manifest`, `--east3-opt-level`, `--summary-dir`

### 3.1 Smoke Test Operation (After `py2x` Unification)

- Keep shared smoke coverage (CLI success, `--east-stage 2` rejection, `load_east`, add-fixture transpile) in `test/unit/common/test_py2x_smoke_common.py`.
- Keep per-language suites (`test/unit/backends/<lang>/test_py2*_smoke.py`) focused on language-specific emitter/runtime contracts only.
- Require the responsibility-boundary comment (`Language-specific smoke suite...`) in each per-language smoke file, and enforce this via `tools/check_noncpp_east3_contract.py`.
- Recommended regression order:
- `PYTHONPATH=src:. python3 -m unittest discover -s test/unit/common -p 'test_py2x_smoke*.py'`
- `python3 tools/check_noncpp_east3_contract.py --skip-transpile`
- `python3 tools/check_py2<lang>_transpile.py` (for affected targets)

## 4. Update Rules

- When adding a new script under `tools/`, update this `docs/en/spec/spec-tools.md` at the same time.
- For each script, explicitly state in one line what automation purpose it serves.
- If there are breaking changes (argument changes, deprecations, consolidation), synchronize related command examples in `docs/en/how-to-use.md`.
- Place toolchain compatibility shims under `tools/shims/`; do not introduce root-level dedicated folders such as `.chain`.
