# P0: Re-measure sample Ruby runtime and reflect in README-JA

Last updated: 2026-02-27

Related TODO:
- `ID: P0-SAMPLE-RUBY-BENCH-01` in `docs/ja/todo/index.md`

Background:
- The current "Execution speed comparison" table in `docs/ja/README.md` ends at `Kotlin`; the `Ruby` column is missing.
- `sample/ruby` already has generated outputs for all 18 `sample/py` cases, and each case has an execution path that outputs `elapsed_sec`.
- The existing comparison table uses the "fresh transpile + warmup/repeat + median" protocol, so Ruby addition must be measured under the same conditions.

Goal:
- Re-measure Ruby execution time for all 18 `sample/py` cases, then add Ruby as the rightmost column in the comparison table of `docs/ja/README.md`.

In scope:
- `docs/ja/README.md`
- `sample/ruby/*` (regenerate if needed)
- Measurement/verification scripts (under `tools/`)

Out of scope:
- Reflecting into `README.md` (English version)
- Re-measuring/re-updating other language columns
- Runtime implementation optimization

Acceptance criteria:
- Ruby execution medians are obtained for all 18 `sample/py` cases.
- A Ruby column is added at the right edge of the comparison table in `docs/ja/README.md`, with all 18 values filled.
- Measurement conditions (fresh transpile / warmup / repeat / median) are documented, and reproducible steps are retained.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/regenerate_samples.py --langs ruby --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets ruby --all-samples --ignore-unstable-stdout`
- `python3 -m unittest discover -s test/unit -p 'test_py2rb_smoke.py' -v`

Decision log:
- 2026-02-27: Based on user request, opened `P0-SAMPLE-RUBY-BENCH-01` to add Ruby sample runtime as a right-edge column in `docs/ja/README.md` comparison table.
- 2026-02-27: Measurement could not start because `ruby` was not installed, so Ruby 3.1.2 was installed in the environment and re-measurement was performed.
- 2026-02-27: Fixed an issue in Ruby execution of `sample/18` where `in/not in` comparison collapsed to `==` and a `main` call mismatch, then confirmed `test/unit/test_py2rb_smoke.py` passed (14 cases).
- 2026-02-27: Measured all 18 `sample/py` cases for Ruby with fresh transpile + `warmup=1` + `repeat=5`, and recorded medians in `work/logs/bench_ruby_sample_20260227.json`.
- 2026-02-27: Added rightmost Ruby column to the execution-speed comparison table in `docs/ja/README.md` and reflected all 18 medians. Also appended a note pointing to the Ruby re-measurement log.

## Breakdown

- [x] [ID: P0-SAMPLE-RUBY-BENCH-01-S1-01] Pin the measurement protocol and collect Ruby measured values (median) for all 18 `sample/py` cases.
- [x] [ID: P0-SAMPLE-RUBY-BENCH-01-S1-02] Add Ruby rightmost column to the comparison table in `docs/ja/README.md` and reflect all 18 values.
- [x] [ID: P0-SAMPLE-RUBY-BENCH-01-S1-03] Complete synchronization of measurement logs, reproducible steps, and notes to keep the process reproducible.
