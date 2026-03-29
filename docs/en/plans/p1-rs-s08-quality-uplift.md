<a href="../../ja/plans/p1-rs-s08-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: `sample/rs/08` Output Quality Uplift (Readability + Hot-Path Reduction)

Last updated: 2026-03-01

Related TODO:
- `ID: P1-RS-S08-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/rs/08_langtons_ant.rs` keeps behavior parity but generated code still has redundancy.
- In particular:
  - Long index-normalization expressions for negative-index support are repeated in hot loops.
  - `clone` remains on `capture` return path, potentially causing unnecessary copies.
  - `while + manual counter` / nested `if` / heavy `%` checks reduce readability and runtime efficiency.
  - Capacity reservation for `frames` and `println!` string handling are not optimized.

Objective:
- Improve generated code quality for `sample/rs/08` and raise readability and hot-path efficiency.

Scope:
- `src/hooks/rs/emitter/rs_emitter.py`
- `src/pytra/compiler/east_parts/east3_opt_passes/*` (if needed)
- `tools/unittest/test_py2rs_smoke.py`
- `tools/unittest/test_py2rs_codegen_issues.py` (add if needed)
- `sample/rs/08_langtons_ant.rs` (regeneration verification)

Out of scope:
- Algorithm changes for `sample/08`
- Breaking changes to Rust runtime APIs
- Bulk refactor across the Rust backend

Acceptance Criteria:
- Confirm the following 6 points in `sample/rs/08_langtons_ant.rs`.
  1. Remove `return (frame).clone();` from `capture`.
  2. Suppress over-generation of negative-index normalization expressions where non-negative indexes are provable.
  3. Reduce simple `range`-origin loops from `while + manual counter` to `for`.
  4. Simplify deep nested branching originating from `if/elif/elif/else`.
  5. Replace repeated `%` capture timing checks with a counter-based method.
  6. Introduce `reserve` equivalent for `frames` to reduce reallocations.
- Rust transpile/smoke/parity pass without regression.

Validation Commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_py2rs_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v`
- `python3 tools/gen/regenerate_samples.py --langs rs --force`
- `python3 tools/check/runtime_parity_check.py --case-root sample --targets rs 08_langtons_ant --ignore-unstable-stdout`

Breakdown:
- [x] [ID: P1-RS-S08-QUALITY-01-S1-01] Lock redundant points in `sample/rs/08` (clone/index normalization/loop/branch/capture condition/capacity) with code fragments.
- [x] [ID: P1-RS-S08-QUALITY-01-S2-01] Introduce output rules to reduce unnecessary `clone` in `capture` return.
- [x] [ID: P1-RS-S08-QUALITY-01-S2-02] Add fastpath to skip index-normalization expressions on paths that guarantee non-negative indexes.
- [x] [ID: P1-RS-S08-QUALITY-01-S2-03] Add fastpath that reduces simple `range`-origin loops to Rust `for`.
- [x] [ID: P1-RS-S08-QUALITY-01-S2-04] Add output rules that simplify `if/elif` chains to `else if` / `match` equivalents.
- [x] [ID: P1-RS-S08-QUALITY-01-S2-05] Add fastpath replacing capture `%` checks with a next-capture counter approach.
- [x] [ID: P1-RS-S08-QUALITY-01-S2-06] Add output rule for `reserve` on estimable `frames` size.
- [x] [ID: P1-RS-S08-QUALITY-01-S3-01] Add regression tests and lock regenerated diffs of `sample/rs/08`.
- [x] [ID: P1-RS-S08-QUALITY-01-S3-02] Run transpile/smoke/parity and confirm non-regression.

Decision Log:
- 2026-03-01: Per user instruction, we finalized the policy to plan output quality improvements for `sample/rs/08` under P1 and add them to TODO.
- 2026-03-02: [ID: P1-RS-S08-QUALITY-01-S1-01] Locked redundant fragments in `sample/rs/08` and fixed implementation priority as `clone -> index normalization -> loop reduction -> branch simplification -> capture check -> reserve`.
- 2026-03-02: [ID: P1-RS-S08-QUALITY-01-S2-01] On return expressions where `bytes()` receives `bytearray/bytes`, we now prefer move semantics, reducing `return (frame).clone();` in `sample/rs/08` to `return frame;`.
- 2026-03-02: [ID: P1-RS-S08-QUALITY-01-S2-02] Added lightweight non-negative analysis (variable tracking + range-origin) and reduced `grid[y][x]` paths in `sample/rs/08` to `((y) as usize)` / `((x) as usize)`.
- 2026-03-02: [ID: P1-RS-S08-QUALITY-01-S2-03] Added `for __for_i in start..stop` fastpath for ascending `step=1` `ForRange` with matching normalization conditions, reducing main loops in `sample/rs/08` from `while` to `for`.
- 2026-03-02: [ID: P1-RS-S08-QUALITY-01-S2-04] Added emit-side flattening from nested `if` to `else if` chains and simplified `d` branching in `sample/rs/08`.
- 2026-03-02: [ID: P1-RS-S08-QUALITY-01-S2-05] In the `ForRange` fastpath, replaced `if i % capture_every == 0` with `next_capture` compare+increment, reducing `%` use in capture checks for `sample/rs/08`.
- 2026-03-02: [ID: P1-RS-S08-QUALITY-01-S2-06] When capture checks are reduced and `frames.push(...)` is detected, added `frames.reserve(...)` using `ceil(stop/step)` estimation.
- 2026-03-02: [ID: P1-RS-S08-QUALITY-01-S3-01] Added regression detection fragments for `next_capture` / `frames.reserve` to smoke tests.
- 2026-03-02: [ID: P1-RS-S08-QUALITY-01-S3-02] Re-ran regeneration plus transpile/smoke/parity (`case08`) for `sample/rs/08` and passed.

## S1-01 Audit Results

Locked fragments (`sample/rs/08_langtons_ant.rs`):

- Unnecessary clone:
  - `return (frame).clone();`
- Over-expanded index normalization:
  - `if __idx_i64_3 < 0 { ... } else { ... }` repeats on `grid[y][x]`-equivalent sites.
  - Inside `capture`, this also expands heavily for both `grid[...]` and `frame[...]`.
- Loop degradation:
  - `let mut i: i64 = 0; while i < steps_total { ... i += 1; }`
- Nested branches:
  - `if d == 0 { ... } else { if d == 1 { ... } else { if d == 2 { ... } else { ... } } }`
- `%` capture checks:
  - `if i % capture_every == 0 { ... }`
- No `reserve`:
  - `let mut frames: Vec<Vec<u8>> = vec![];` (no capacity reservation)

Implementation priority:

1. `S2-01` reduce clone (small semantic risk, immediate win)
2. `S2-02` reduce index normalization (large hot-path impact)
3. `S2-03` reduce range loops (`while` -> `for`)
4. `S2-04` simplify branches (`else if` / `match`)
5. `S2-05` move capture checks to next-capture counters
6. `S2-06` add `frames.reserve`
