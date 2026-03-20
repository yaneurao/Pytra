# Development Operations Guide

This page collects day-to-day operational runbooks for parity, local CI, and backend health that are not included in [how-to-use.md](./how-to-use.md).

## Runtime Measurement Protocol (sample)

- Runtime measurements sourced from `sample/py` are taken after a fresh transpile.
- The default measurement count is `warmup=1` + `repeat=2`.
- The representative value is the **arithmetic mean (average)** of the two runs (not the median).
- Compile time is not included in the measurements.

## Runtime Parity Operations (sample, all targets)

- `tools/runtime_parity_check.py` compares not only stdout but also the `size` and `CRC32` of artifacts indicated by `output:`.
- On each parity run, stale artifacts under `sample/out`, `test/out`, `out`, and `test/transpile/<target>/<case>` are automatically deleted per case.
- Unstable lines such as `elapsed_sec` are excluded from comparison by default (`--ignore-unstable-stdout` is a compatibility flag).
- Canonical wrapper to verify all 14 targets at once:

```bash
python3 tools/check_all_target_sample_parity.py \
  --summary-dir work/logs/all_target_sample_parity
```

- Canonical group when using `runtime_parity_check.py` directly at the lower level:

```bash
python3 tools/runtime_parity_check.py \
  --targets cpp \
  --case-root sample \
  --all-samples \
  --east3-opt-level 2 \
  --cpp-codegen-opt 3

python3 tools/runtime_parity_check.py \
  --targets js,ts \
  --case-root sample \
  --all-samples \
  --ignore-unstable-stdout \
  --east3-opt-level 2

python3 tools/runtime_parity_check.py \
  --targets rs,cs,go,java,kotlin,swift,scala \
  --case-root sample \
  --all-samples \
  --ignore-unstable-stdout \
  --east3-opt-level 2

python3 tools/runtime_parity_check.py \
  --targets ruby,lua,php,nim \
  --case-root sample \
  --all-samples \
  --ignore-unstable-stdout \
  --east3-opt-level 2
```

- When splitting cases to reduce runtime (example groupings):
  - `01-03`: `01_mandelbrot 02_raytrace_spheres 03_julia_set`
  - `04-06`: `04_orbit_trap_julia 05_mandelbrot_zoom 06_julia_parameter_sweep`
  - `07-09`: `07_game_of_life_loop 08_langtons_ant 09_fire_simulation`
  - `10-12`: `10_plasma_effect 11_lissajous_particles 12_sort_visualizer`
  - `13-15`: `13_maze_generation_steps 14_raymarching_light_cycle 15_wave_interference_loop`
  - `16-18`: `16_glass_sculpture_chaos 17_monte_carlo_pi 18_mini_language_interpreter`

## Non-C++ Backend Health Check after linked-program

- The non-C++ backend gate after linked-program introduction uses `tools/check_noncpp_backend_health.py` as the canonical check.
- The minimal daily check is the single command below. `parity` depends on toolchains and is not run here.

```bash
python3 tools/check_noncpp_backend_health.py --family all --skip-parity
```

- To restrict to a family, use `wave1` / `wave2` / `wave3`:

```bash
python3 tools/check_noncpp_backend_health.py --family wave1 --skip-parity
python3 tools/check_noncpp_backend_health.py --family wave2 --skip-parity
python3 tools/check_noncpp_backend_health.py --family wave3 --skip-parity
```

- `toolchain_missing` is treated as a parity-environment baseline (not a backend bug).
- `tools/run_local_ci.py` embeds `python3 tools/check_noncpp_backend_health.py --family all --skip-parity`, so passing local CI simultaneously monitors the non-C++ backend smoke/transpile gate.
- `python3 tools/check_jsonvalue_decode_boundaries.py` is also embedded in local CI, so if raw `json.loads(...)` re-enters at JSON artifact boundaries in `py2x` / `ir2lang` / `east_io` / `toolchain/link/*`, local CI will fail.

## Required Guards when Changing Emitters (Stop-Ship)

- When modifying any `src/toolchain/emit/*/emitter/*.py`, always run the following before committing:
  - `python3 tools/check_emitter_runtimecall_guardrails.py`
  - `python3 tools/check_emitter_forbidden_runtime_symbols.py`
  - `python3 tools/check_noncpp_east3_contract.py`
- If any of the above returns `FAIL`, committing or pushing is prohibited (Stop-Ship).
- Runtime/stdlib call resolution must use only the authoritative EAST3 information (`runtime_call`, `resolved_runtime_call`, `resolved_runtime_source`). Do not add function-name or module-name branches or tables on the emitter side.
- The `java` backend is a strict target. No directly-written symbols for runtime dispatch are permitted via allowlist — maintain zero such entries.

## Non-C++ Backend Container Reference Management (v1)

- Target backends: `cs/js/ts/go/swift/ruby/lua/php` (Rust/Kotlin have pilot implementations).
- Common policy:
  - Boundaries flowing into `object/Any/unknown/union (including any)` are treated as reference-management boundaries (ref-boundary).
  - Paths that are type-known and locally non-escaping are treated as value-type paths (value-path), with shallow copies inserted.
  - When the determination is ambiguous, fail-closed to the ref-boundary side.
- Verifying generated output:
  - `python3 tools/check_py2cs_transpile.py`
  - `python3 tools/check_py2js_transpile.py`
  - `python3 tools/check_py2ts_transpile.py`
  - `python3 tools/check_py2go_transpile.py`
  - `python3 tools/check_py2swift_transpile.py`
  - `python3 tools/check_py2rb_transpile.py`
  - `python3 tools/check_py2lua_transpile.py`
  - `python3 tools/check_py2php_transpile.py`
  - `python3 tools/runtime_parity_check.py --case-root sample --targets cs,js,ts,go,swift,ruby,lua,php --ignore-unstable-stdout 18_mini_language_interpreter`
- Rollback approach (interim):
  - If value-type materialization causes a problem, move the local type annotation toward `object/Any` to force a ref-boundary.
  - Conversely, if you want to explicitly isolate an alias, write an explicit copy such as `list(...)` / `dict(...)` on the Python input side.

## Selfhost Verification Procedure (C++ backend → `py2cpp.cpp`)

Prerequisites:
- Run from the project root.
- `g++` must be available.
- `selfhost/` is treated as a working directory for verification (not tracked by Git).

```bash
# 0) Generate and build selfhost C++ (including runtime .cpp files in the link)
python3 tools/build_selfhost.py > selfhost/build.all.log 2>&1

# 1) Check build errors by category
rg "error:" selfhost/build.all.log
```

Comparison procedure after a successful compile:

```bash
# 2) Convert sample/py/01 from .py input using the selfhost binary
mkdir -p test/transpile/cpp2
./selfhost/py2cpp.out sample/py/01_mandelbrot.py --target cpp -o test/transpile/cpp2/01_mandelbrot.cpp

# 3) Convert the same input with the Python C++ backend
python3 src/py2x-selfhost.py sample/py/01_mandelbrot.py --target cpp -o test/transpile/cpp/01_mandelbrot.cpp

# 4) Verify the direct route passes -fsyntax-only for all samples
python3 tools/check_selfhost_direct_compile.py

# 5) Check output diff between Python version and selfhost version on representative cases
python3 tools/check_selfhost_cpp_diff.py --mode strict --show-diff

# 6) Verify representative e2e
python3 tools/verify_selfhost_end_to_end.py --skip-build \
  --cases sample/py/05_mandelbrot_zoom.py sample/py/18_mini_language_interpreter.py test/fixtures/core/add.py

# 7) Generate stage2 binary and check diff
python3 tools/build_selfhost_stage2.py
python3 tools/check_selfhost_stage2_cpp_diff.py --mode strict

# 8) Verify full sample parity with the stage2 binary
python3 tools/check_selfhost_stage2_sample_parity.py --skip-build
```

Notes:
- Direct `.py` input to `selfhost/py2cpp.out` is the current contract. The bridge path is treated as an investigation-only fallback.
- `tools/check_selfhost_cpp_diff.py` and `tools/check_selfhost_stage2_cpp_diff.py` treat strict mode as canonical.
- `tools/check_selfhost_stage2_sample_parity.py --skip-build` is the canonical command for full sample parity using `selfhost/py2cpp_stage2.out`. Unlike the representative diff, it checks transpile + compile + run parity for all `sample/py` cases.
- `tools/check_selfhost_direct_compile.py` is the shortest compile regression gate: it converts all `sample/py` cases with selfhost and checks up to `g++ -fsyntax-only`.

Failure checklist:
- First classify `error:` entries in `build.all.log`, separating type-system errors (`std::any` / `optional`) from syntax errors (unlowered constructs).
- For the relevant lines in `selfhost/py2cpp.cpp`, verify that the ABI value/ref-first contract in the original `src/toolchain/emit/cpp/cli.py` or the generated runtime (`src/runtime/cpp/generated/**`) has not been broken.
- Host/selfhost diffs like those in `sample/py/18_mini_language_interpreter.py` can also occur when only the runtime serializer is fixed without rebuilding the selfhost binary. If you modify `src/pytra/std/json.py` or generated runtime, re-run `python3 tools/build_selfhost.py`.

## Transpile Checks during CodeEmitter Work

When incrementally modifying `CodeEmitter`, run the following after each step:

```bash
python3 tools/check_py2cpp_transpile.py
python3 tools/check_py2rs_transpile.py
python3 tools/check_py2js_transpile.py
```

Notes:
- By default, known negative-case fixtures (`test/fixtures/signature/ng_*.py` and `test/fixtures/typing/any_class_alias.py`) are excluded from evaluation.
- To include negative cases as well, add `--include-expected-failures`.
