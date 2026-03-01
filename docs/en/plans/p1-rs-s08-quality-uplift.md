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
- `test/unit/test_py2rs_smoke.py`
- `test/unit/test_py2rs_codegen_issues.py` (add if needed)
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
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rs_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs_smoke.py' -v`
- `python3 tools/regenerate_samples.py --langs rs --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets rs 08_langtons_ant --ignore-unstable-stdout`

Breakdown:
- [ ] [ID: P1-RS-S08-QUALITY-01-S1-01] Lock redundant points in `sample/rs/08` (clone/index normalization/loop/branch/capture condition/capacity) with code fragments.
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-01] Introduce output rules to reduce unnecessary `clone` in `capture` return.
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-02] Add fastpath to skip index-normalization expressions on paths that guarantee non-negative indexes.
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-03] Add fastpath that reduces simple `range`-origin loops to Rust `for`.
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-04] Add output rules that simplify `if/elif` chains to `else if` / `match` equivalents.
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-05] Add fastpath replacing capture `%` checks with a next-capture counter approach.
- [ ] [ID: P1-RS-S08-QUALITY-01-S2-06] Add output rule for `reserve` on estimable `frames` size.
- [ ] [ID: P1-RS-S08-QUALITY-01-S3-01] Add regression tests and lock regenerated diffs of `sample/rs/08`.
- [ ] [ID: P1-RS-S08-QUALITY-01-S3-02] Run transpile/smoke/parity and confirm non-regression.

Decision Log:
- 2026-03-01: Per user instruction, we finalized the policy to plan output quality improvements for `sample/rs/08` under P1 and add them to TODO.
