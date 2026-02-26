# P0: Sample Execution Infrastructure Recovery

## Background
The runtime table in `readme-ja.md` had long remained with many missing values due to overlapping issues:
- C++ comparison build failures caused unmeasured C++ entries.
- Missing runtime environments for Rust/C#/Go/Java/Swift/Kotlin caused unmeasured entries.

This task restored toolchains, re-ran sample benchmarks across languages, and updated README tables.

## Policy
- 0) Install/prepare toolchains required for all-language execution in this environment (or explicitly record alternatives if unavailable).
- 1) Reproduce and minimally fix C++ build failures until reproducible success.
- 2) Benchmark under baseline-update conditions (`tools/verify_sample_outputs.py`).
- 3) Reflect execution-time table updates in `readme-ja.md` and `readme.md`.

## Out of scope
- Quality/optimization improvements of sample implementations themselves.
- README link-structure changes beyond minimum wording updates.

## Acceptance criteria
- For all target languages (`cpp/rs/cs/js/ts/go/java/swift/kotlin`), either benchmark measurement is produced or execution feasibility is explicitly documented.
- `readme-ja.md` table reflects latest measured values and current explanation of any missing entries.
- A one-line progress update is recorded in `docs-ja/todo/index.md` at completion.

## Key decisions and outcomes (summary)

- 2026-02-25: Hardened parity foundation (`core.cpp` / `east_parts/core.py` compare-splitting robustness; non-C++ `-o` path alignment in `tools/runtime_parity_check.py`), and confirmed C++ pass for `math_extended` / `pathlib_extended`.
- 2026-02-25: Added stdio fallback in `src/pytra/std/sys.py` to avoid crashes when migrated runtimes require missing implementations.
- 2026-02-25: Established Swift route (`swiftc` install, parity script updates for `--output` and absolute `SWIFTC`).
- 2026-02-25: Java path reached execution by forcing `Main.java` output due to `public class Main` filename constraint; identified current Java stub-output mismatch at that stage.
- 2026-02-25: Re-ran full parity path (`cpp,rs,cs,js,ts,go,java,swift,kotlin`) and cataloged per-language failure categories (import resolution, syntax leakage, runtime mismatch, sidecar/stub state).
- 2026-02-25: Completed toolchain reachability setup and moved focus to language-specific conversion/runtime alignment.
- 2026-02-25: Extended `tools/runtime_parity_check.py` for `--case-root sample` and `--ignore-unstable-stdout`; confirmed `01_mandelbrot` C++ parity pass under sample-root mode.
- 2026-02-25: Refreshed `sample/golden/manifest.json` for all 18 sample cases under current baseline operation.

## Notes
- Detailed per-case/per-language failure and retry logs remain in the Japanese source (`docs-ja/plans/p0-sample-all-language-benchmark.md`).
- This English mirror keeps the operational summary and decision points used for downstream planning and README updates.
