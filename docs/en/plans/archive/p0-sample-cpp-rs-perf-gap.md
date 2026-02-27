# P0: Correct C++/Rust Performance Gaps on Samples

Last updated: 2026-02-26

Related TODO:
- `ID: P0-SAMPLE-CPP-RS-PERF-01` in `docs/ja/todo/index.md`

Background:
- `readme.md` / `docs/ja/README.md` sample tables showed large C++ vs Rust runtime gaps in some cases (near 3x at worst).
- Inputs are the same Python sources; language-specific differences are expected, but extreme divergence suggests concentrated bottlenecks.
- At the 2026-02-26 baseline, both directions existed: Rust-slower outliers and C++-slower outliers.

Initial analysis (2026-02-26):
- Rust-slower outliers:
  - `09_fire_simulation`: `cpp=2.114s`, `rs=7.342s` (`rs/cpp=3.47`)
  - `18_mini_language_interpreter`: `cpp=0.424s`, `rs=1.216s` (`rs/cpp=2.87`)
  - `01_mandelbrot`: `cpp=0.277s`, `rs=0.735s` (`rs/cpp=2.65`)
- Rust-faster (C++-slower) outliers:
  - `11_lissajous_particles`, `12_sort_visualizer`, `13_maze_generation_steps`, `16_glass_sculpture_chaos` (around 3x)
- Suspected roots:
  - Rust emitter: ownership-safe implementation over-cloned in hot loops (`_clone_owned_call_args`, list-subscript read clones).
  - C++ runtime: GIF/PNG hot paths overused compatibility conversions (`py_to_int64`, `py_len`, `py_slice`).

Goal:
- Reduce C++/Rust gap until no outlier remains.
- Prioritize overhead reducible by code generation/runtime path improvements.
- Fix reproducible measurement protocol and make regression tracking repeatable.

In scope:
- Rust emitter: `src/hooks/rs/emitter/rs_emitter.py`
- C++ GIF/PNG runtime: `src/runtime/cpp/pytra-gen/utils/gif.cpp`, `src/runtime/cpp/pytra-gen/utils/png.cpp`
- C++ generated-code frame-copy hot paths in major sample cases
- Measurement protocol documentation + README table updates

Out of scope:
- Changing Python sample algorithms
- Optimizing non C++/Rust languages
- CPU-specific local tuning assumptions (`-march=native`, etc.)

Improvement policy:
1. Remove unnecessary Rust clone/to_string paths first.
2. Add typed fast paths to C++ GIF/PNG runtime and shrink compatibility-layer usage.
3. Fix measurement protocol and evaluate deltas numerically.

Acceptance criteria:
- Re-measure all 18 `sample/py` cases for C++/Rust and document both method and results.
- Shrink prior `>=2x` outliers (`01/09/11/12/13/16/18`) to `<=1.5x`.
- Preserve output parity (stdout + artifact hash/size).
- Update README tables (JA/EN) with latest values.

Reference commands:
- `python3 tools/runtime_parity_check.py --case-root sample --targets cpp,rs --all-samples --ignore-unstable-stdout`
- `python3 tools/verify_sample_outputs.py --targets cpp,rs`
- `python3 tools/benchmark_sample_cpp_rs.py --repeat 5 --warmup 1 --emit-json ...`

Measurement protocol (`S1-02`):
- fixed input scope (`sample/py` 18 cases, excluding `__init__`)
- fixed build flags (`g++ -std=c++20 -O2`, `rustc -O`)
- fresh transpile before measurement
- warmup 1 + repeat 5
- use program-reported `elapsed_sec` (compile time excluded)
- median per case
- outlier criterion: `max(cpp/rs, rs/cpp) > 1.5x`

## Breakdown

- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S1-01] Auto-extract C++/Rust gap table from README and lock outlier set.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S1-02] Document reproducible measurement protocol.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-01] Remove unnecessary clone in Rust `save_gif`/`write_rgb_png` paths.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-02] Suppress clone on Rust list-subscript reads for copyable scalar element types.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-03] Reduce `to_string()` chaining in Rust string-compare/tokenize paths.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S2-04] Re-benchmark `01/09/18` and record Rust-side contribution.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S3-01] Add C++ GIF typed fast path and reduce `py_slice`/`py_len`/`py_to_int64` dependency.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S3-02] Move C++ PNG scanline/chunk handling toward typed operations.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S3-03] Re-benchmark `11/12/13/16` and record C++-side contribution.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S4-01] Remove redundant frame double-copy in generated sample code.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S4-02] Confirm speedups while keeping parity via parity/output checks.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S5-01] Reflect C++/Rust 18-case remeasurement into READMEs.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S5-02] Document unresolved outliers and next actions.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S6-01] Optimize C++ runtime byte-copy paths (`list/bytearray` range insert).
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S6-02] Re-benchmark major divergence cases and record contribution.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S7-01] Reduce nested-subscript and enumerate clone overhead in Rust emitter.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S7-02] Re-benchmark `01/04/09/18` and record remaining outliers.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S8-01] Further reduce Rust clone and `to_string()` costs in case `18` hot path.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S8-02] Re-benchmark and update remaining issues.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S9-01] Add capacity inference (`with_capacity`) for Rust `bytearray()/bytes()` empty init.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S9-02] Re-benchmark and update remaining outliers.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S10-01] Unify C++ numeric `/` to `py_div` (Python true division) outside `Path /`.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S10-02] Re-benchmark and lock residual outlier set.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S11-01] Reduce list-wide clone in Rust list/enumerate iteration and dictionary key coercion ownership.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S11-02] Re-benchmark and update residual outlier set.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S12-01] Shift Rust class-method string args to `&str` where possible.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S12-02] Re-benchmark and update residual outlier set.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S13-01] Optimize C++ GIF little-endian write path and reserve strategy.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S13-02] Re-benchmark and update residual outlier set.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S14-01] Remove always-allocating `Vec<char>` in Rust `py_str_at/py_slice_str`, add ASCII fast path + non-ASCII fallback.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S14-02] Re-benchmark and converge residual outliers.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S15-01] Add C++ `PyFile::write(bytes)` contiguous bulk-write fast path.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S15-02] Re-benchmark targeted cases and confirm reproducibility.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S16-01] Re-benchmark all 18 and update README values.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S16-02] Recompute outliers and narrow to `16_glass_sculpture_chaos`.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S17-01] Improve C++ numeric type inference for if-join declarations and reduce object-degradation in `16` hot loop.
- [x] [ID: P0-SAMPLE-CPP-RS-PERF-01-S17-02] Re-benchmark `16` and all 18; update READMEs and plan.

## Final result

- 2026-02-26 final full remeasurement (`S17-02`) showed no `>1.5x` outlier remaining.
- Maximum divergence became `1.35x` (case `06`), below threshold.
- Representative latest medians reflected to README JA/EN included:
  - `01`: `cpp=0.751`, `rs=0.740`
  - `09`: `cpp=0.569`, `rs=0.612`
  - `16`: `cpp=0.260`, `rs=0.227`
  - `18`: `cpp=0.335`, `rs=0.386`
