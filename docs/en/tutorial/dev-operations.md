<a href="../../ja/tutorial/dev-operations.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Development Operations Guide

This page consolidates day-to-day development procedures — parity, local CI, backend health, and more — that are not covered in [how-to-use.md](./how-to-use.md).

## Execution Time Measurement Protocol (sample)

- Execution time measurements derived from `sample/py` must be performed after a fresh transpile.
- Default measurement settings: `warmup=1` + `repeat=2`.
- The representative value is the **arithmetic mean (average)** of the 2 runs (not the median).
- Compile time is not included in the measurement.

## Runtime Parity Operations (sample, all targets)

- `tools/check/runtime_parity_check.py` is the canonical fast-backed parity entrypoint. It compares not only stdout but also the `size` and `CRC32` of the artifact indicated by `output:`.
- Before each parity run, stale artifacts in `sample/out`, `test/out`, `out`, and `work/transpile/<target>/<case>` are automatically deleted per case.
- Unstable lines such as `elapsed_sec` are excluded from comparison by default (`--ignore-unstable-stdout` is a compatibility flag).
- Canonical wrapper for validating all 14 targets at once:

```bash
python3 tools/check/check_all_target_sample_parity.py \
  --summary-dir work/logs/all_target_sample_parity
```

- Canonical groups when using `runtime_parity_check.py` at a lower level:

```bash
python3 tools/check/runtime_parity_check.py \
  --targets cpp \
  --case-root sample \
  --all-samples \
  --opt-level 2 \
  --cpp-codegen-opt 3

python3 tools/check/runtime_parity_check.py \
  --targets js,ts \
  --case-root sample \
  --all-samples \
  --ignore-unstable-stdout \
  --opt-level 2

python3 tools/check/runtime_parity_check.py \
  --targets rs,cs,go,java,kotlin,swift,scala \
  --case-root sample \
  --all-samples \
  --ignore-unstable-stdout \
  --opt-level 2

python3 tools/check/runtime_parity_check.py \
  --targets ruby,lua,php,nim \
  --case-root sample \
  --all-samples \
  --ignore-unstable-stdout \
  --opt-level 2
```

- Example case splits for reducing execution time:
  - `01-03`: `01_mandelbrot 02_raytrace_spheres 03_julia_set`
  - `04-06`: `04_orbit_trap_julia 05_mandelbrot_zoom 06_julia_parameter_sweep`
  - `07-09`: `07_game_of_life_loop 08_langtons_ant 09_fire_simulation`
  - `10-12`: `10_plasma_effect 11_lissajous_particles 12_sort_visualizer`
  - `13-15`: `13_maze_generation_steps 14_raymarching_light_cycle 15_wave_interference_loop`
  - `16-18`: `16_glass_sculpture_chaos 17_monte_carlo_pi 18_mini_language_interpreter`

## Non-C++ Backend Health Check After linked-program

- After introducing linked-program, the non-C++ backend gate is canonically `tools/check/check_noncpp_backend_health.py`.
- For the minimum daily check, run just this one command. Parity is toolchain-dependent and is not run here.

```bash
python3 tools/check/check_noncpp_backend_health.py --family all --skip-parity
```

- To narrow by family, use `wave1` / `wave2` / `wave3`.

```bash
python3 tools/check/check_noncpp_backend_health.py --family wave1 --skip-parity
python3 tools/check/check_noncpp_backend_health.py --family wave2 --skip-parity
python3 tools/check/check_noncpp_backend_health.py --family wave3 --skip-parity
```

- `toolchain_missing` is treated as a baseline — it means the parity execution environment is absent, not a backend bug.
- `tools/run/run_local_ci.py` already includes `python3 tools/check/check_noncpp_backend_health.py --family all --skip-parity`, so passing local CI also monitors the non-C++ backend smoke/transpile gate.
- Likewise, `python3 tools/check/check_jsonvalue_decode_boundaries.py` is also included, so if raw `json.loads(...)` re-enters the JSON artifact boundary of `pytra-cli` / `east_io` / `toolchain/link/*`, local CI will fail.

## Required Guards When Changing an Emitter (Stop-Ship)

- When modifying `src/toolchain/emit/*/emitter/*.py`, always run the following before committing:
  - `python3 tools/check/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check/check_noncpp_east3_contract.py`
- If any of the above returns `FAIL`, committing and pushing is prohibited (Stop-Ship).
- Runtime/stdlib call resolution must use only the canonical EAST3 information (`runtime_call`, `resolved_runtime_call`, `resolved_runtime_source`). Do not add function-name or module-name branches/tables on the emitter side.
- The `java` backend is a strict target. No direct-written dispatch symbols are permitted in the allowlist; the count must remain at 0.

## Non-C++ Backend Container Reference Management Operations (v1)

- Applicable backends: `cs/js/ts/go/swift/ruby/lua/php` (Rust/Kotlin have pilot implementations).
- Common policy:
  - Boundaries that flow into `object/Any/unknown/union(including any)` are treated as reference-management boundaries (ref-boundary).
  - Paths with a known type and a locally non-escaping route are treated as value-type paths (value-path), with a shallow copy inserted.
  - When the determination is ambiguous, fail-closed toward the ref-boundary side.
- Verifying generated output:
  - `python3 tools/check/check_py2cs_transpile.py`
  - `python3 tools/check/check_py2js_transpile.py`
  - `python3 tools/check/check_py2ts_transpile.py`
  - `python3 tools/check/check_py2go_transpile.py`
  - `python3 tools/check/check_py2swift_transpile.py`
  - `python3 tools/check/check_py2rb_transpile.py`
  - `python3 tools/check/check_py2lua_transpile.py`
  - `python3 tools/check/check_py2php_transpile.py`
  - `python3 tools/check/runtime_parity_check.py --case-root sample --targets cs,js,ts,go,swift,ruby,lua,php --ignore-unstable-stdout 18_mini_language_interpreter`
- Rollback approach (interim):
  - For locations where value-type materialization is problematic, shift the local type annotation toward `object/Any` to force a ref-boundary.
  - Conversely, to explicitly isolate an alias, write an explicit copy in the input Python using `list(...)` / `dict(...)` etc.

## Selfhost Verification Procedure (C++ backend → `py2cpp.cpp`)

Prerequisites:
- Run from the project root.
- `g++` must be available.
- `selfhost/` is treated as a working directory for verification (not tracked by Git).

```bash
# 0) Generate and build the selfhost C++ (including runtime .cpp files)
python3 tools/build_selfhost.py > selfhost/build.all.log 2>&1

# 1) Review build errors by category
rg "error:" selfhost/build.all.log
```

Comparison procedure on successful compilation:

```bash
# 2) Use the selfhost binary to transpile sample/py/01 from a .py file directly
mkdir -p work/transpile/cpp2
./selfhost/py2cpp.out sample/py/01_mandelbrot.py --target cpp -o work/transpile/cpp2/01_mandelbrot.cpp

# 3) Transpile the same input with the Python-based C++ backend
python3 src/pytra-cli.py sample/py/01_mandelbrot.py --target cpp -o work/transpile/cpp/01_mandelbrot.cpp

# 4) Verify that the direct route passes -fsyntax-only for all sample files
python3 tools/check/check_selfhost_direct_compile.py

# 5) Check output diffs between the Python version and the selfhost version for representative cases
python3 tools/check/check_selfhost_cpp_diff.py --mode strict --show-diff

# 6) Verify representative e2e
python3 tools/verify_selfhost_end_to_end.py --skip-build \
  --cases sample/py/05_mandelbrot_zoom.py sample/py/18_mini_language_interpreter.py test/fixtures/core/add.py

# 7) Generate stage2 binary and check diffs
python3 tools/build_selfhost_stage2.py
python3 tools/check/check_selfhost_stage2_cpp_diff.py --mode strict

# 8) Verify parity for all sample files using the stage2 binary
python3 tools/check/check_selfhost_stage2_sample_parity.py --skip-build
```

Notes:
- Direct `.py` input to `selfhost/py2cpp.out` is the current contract. The bridge route is treated only as a fallback for investigation.
- `tools/check/check_selfhost_cpp_diff.py` and `tools/check/check_selfhost_stage2_cpp_diff.py` treat strict mode as canonical.
- `tools/check/check_selfhost_stage2_sample_parity.py --skip-build` is the canonical command for full sample parity using `selfhost/py2cpp_stage2.out`. Unlike representative diffs, it checks transpile + compile + run parity for all files in `sample/py`.
- `tools/check/check_selfhost_direct_compile.py` is the shortest compile regression gate: it transpiles all files in `sample/py` with selfhost and checks through `g++ -fsyntax-only`.

Troubleshooting checklist:
- First categorize `error:` entries in `build.all.log`, separating type-system errors (`std::any` / `optional`) from syntax errors (not yet lowered).
- For the relevant line in `selfhost/py2cpp.cpp`, verify that the ABI of the original `src/toolchain/emit/cpp/cli.py` or the generated runtime (`src/runtime/cpp/generated/**`) has not broken the value/ref-first contract.
- Host/selfhost diffs like those in `sample/py/18_mini_language_interpreter.py` can also occur when only the runtime serializer is fixed without rebuilding the selfhost binary. After fixing `src/pytra/std/json.py` or the generated runtime, re-run `python3 tools/build_selfhost.py`.

## Transpile Check During CodeEmitter Work

When incrementally modifying `CodeEmitter`, run the following at each step:

```bash
python3 tools/check/check_py2cpp_transpile.py
python3 tools/check/check_py2rs_transpile.py
python3 tools/check/check_py2js_transpile.py
```

Notes:
- By default, known negative-example fixtures (`test/fixtures/signature/ng_*.py` and `test/fixtures/typing/any_class_alias.py`) are excluded from evaluation.
- To include negative examples in the check, add `--include-expected-failures`.
