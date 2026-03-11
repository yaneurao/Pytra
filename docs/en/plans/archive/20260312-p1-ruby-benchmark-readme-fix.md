# P1: Ruby Benchmark Re-Measurement and README Reflection Fix

Last updated: 2026-03-01

Related TODO:
- `ID: P1-RUBY-BENCH-FIX-01` in `docs/ja/todo/index.md`

Background:
- In the execution-speed comparison table of `docs/ja/README.md`, Ruby values had cases not matching actual measurement conditions (`sample/01`).
- Existing operations did not clearly formalize the order "re-measure -> parity verification -> README reflection," risking stale values remaining.

Objective:
- Lock the update procedure for Ruby measured values so unverified values cannot enter README.

Scope:
- `sample/ruby/*` (fresh regeneration)
- `tools/runtime_parity_check.py` (use existing flow)
- `docs/ja/README.md` (comparison table)

Out of scope:
- Re-measurement for other languages such as C++/Rust
- Ruby runtime optimization

Acceptance Criteria:
- Log Ruby actual measurement for `sample/01` (`ruby --yjit`, `warmup=1`, `repeat=5`, median).
- Re-verify Ruby parity and then reflect measured value into Ruby column of `docs/ja/README.md`.
- Work logs (measurement log/verification commands) are traceable via `work/logs` and context files.

Validation Commands (planned):
- `python3 tools/regenerate_samples.py --langs ruby --stems 01_mandelbrot --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 01_mandelbrot --ignore-unstable-stdout`
- `ruby --yjit sample/ruby/01_mandelbrot.rb`

## Breakdown

- [ ] [ID: P1-RUBY-BENCH-FIX-01] Make "fresh transpile -> parity verification -> README reflection" mandatory when updating Ruby measurements.
- [x] [ID: P1-RUBY-BENCH-FIX-01-S1-01] Re-measure `sample/01` with `ruby --yjit` (`warmup=1`, `repeat=5`) and save logs.
- [x] [ID: P1-RUBY-BENCH-FIX-01-S1-02] Verify Ruby parity of `sample/01` via `runtime_parity_check`.
- [x] [ID: P1-RUBY-BENCH-FIX-01-S1-03] Reflect measured value into Ruby column of `docs/ja/README.md` and lock diffs.

Decision Log:
- 2026-03-01: Per user instruction, filed `P1-RUBY-BENCH-FIX-01` to prevent recurrence of Ruby measurement reflection mistakes.
- 2026-03-01: Ran `python3 tools/regenerate_samples.py --langs ruby --stems 01_mandelbrot --force` and confirmed fresh regeneration (`summary: total=1 regen=1 fail=0`).
- 2026-03-01: Confirmed `SUMMARY cases=1 pass=1 fail=0` with `python3 tools/runtime_parity_check.py --case-root sample --targets ruby 01_mandelbrot --ignore-unstable-stdout` (`S1-02`).
- 2026-03-01: Ran `ruby --yjit` measurements with `warmup=1` / `repeat=5`, saved to `work/logs/bench_ruby_yjit_01_mandelbrot_20260301.json`; median was `18.954643653007224` seconds (`S1-01`).
- 2026-03-01: Updated Ruby value in `docs/ja/README.md` for `01_mandelbrot` from `18.682 -> 18.955` (`S1-03`).
