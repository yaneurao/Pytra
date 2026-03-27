<a href="../../ja/plans/p1-rs-s18-quality-uplift.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: sample/18 Rust Output Quality Uplift (Readability + Hot-Path Degradation Reduction)

Last updated: 2026-03-02

Related TODO:
- `ID: P1-RS-S18-QUALITY-01` in `docs/ja/todo/index.md`

Background:
- `sample/rs/18_mini_language_interpreter.rs` still contains generic paths prioritized for semantic compatibility, mixing excessive `clone`, negative-index normalization expressions, `String`-based character scanning, and chained `to_string/format!` usage.
- Compared with C++ output for the same case, Rust output has many places that "fall back to generic expressions even though types are known."

Goal:
- Improve readability and runtime efficiency in Rust output for `sample/18` by prioritizing degradation to known-type paths.
- Prioritize highly reproducible local improvements first (borrow conversion / index fastpath / character scan / string construction).

Scope:
- Emitter implementations under `src/hooks/rust/` (expression/statement/type/utility rendering)
- Rust codegen regression tests under `test/unit`
- `sample/rs/18_mini_language_interpreter.rs` (regeneration verification)

Out of scope:
- Language spec changes (operator semantics, exception contract, integer division semantics)
- Large-scale redesign of Rust runtime APIs
- Immediate rollout to all samples (sample/18 first)

Acceptance criteria:
- In `sample/rs/18`, all of the following hold:
  - Unnecessary `clone` is reduced (borrow where read-only access is possible)
  - Negative-index normalization expressions are not emitted for indices guaranteed non-negative
  - Character scanning in the tokenize hot path is lightweight
  - Redundant `to_string/format!` chain fragments are reduced
- `check_py2rs_transpile.py`, Rust smoke tests, and `runtime_parity_check --targets rs` pass without regression.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_py2rs_transpile.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2rs*' -v`
- `python3 tools/regenerate_samples.py --langs rs --stems 18_mini_language_interpreter --force`
- `python3 tools/runtime_parity_check.py --case-root sample --targets rs --case 18_mini_language_interpreter`

Decision log:
- 2026-03-02: Filed sample/18 Rust output improvements as P1 based on user direction.
- 2026-03-02: In sample/18 inventory, fixed priority order as `clone reduction -> index fastpath -> scan lightweighting -> string construction simplification -> API type degradation (&Vec->&[T]) -> map review`.
- 2026-03-02: Fixed fail-closed boundary as "known type + stable value boundary + keep current output on mismatch." Optimizations are disabled for `unknown/object/union` and order-dependent paths.
- 2026-03-02: Extended borrowed-argument type resolution in Rust emitter and degraded list reference arguments from `&Vec<T>` to `&[T]` (`S2-06`).
- 2026-03-02: Confirmed slice signatures of `tokenize/eval_expr/execute` in `sample/rs/18`, and passed `check_py2rs_transpile` plus parity (case18).
- 2026-03-02: Implemented borrow-priority path for list-index initialization in `AnnAssign`, and degraded the leading `ExprNode` acquisition in `eval_expr` from clone to `&ExprNode` reference (`S2-01`).
- 2026-03-02: Introduced sign hints limited to `if` then-branches and omitted negative-index normalization under `single_tag > 0` indices (`S2-02`).
- 2026-03-02: Added non-negative-guaranteed path for string indexing branching to `py_str_at_nonneg`, reducing tokenize character fetch overhead (`S2-03`).
- 2026-03-02: Degraded `get` on small fixed `dict[str, const]` to `match`, reducing map dependency for token lookup (`S2-04`).
- 2026-03-02: Flattened `str` Add chains without cast and merged into a single `format!`, removing nested `format!` (`S2-05`).
- 2026-03-02: Added regression detection for sample/18 (`single_tag` index fastpath / `py_str_at_nonneg` / no nested `format!`) and re-passed regeneration + transpile/smoke/parity (`S3-01/S3-02`).
- 2026-03-02: Added order-dependency analysis (`items/keys/values`, dict iteration, external unknown calls), and degraded order-independent `dict[str,int64]` paths to `HashMap` (`S2-07`).

## Breakdown

- [x] [ID: P1-RS-S18-QUALITY-01-S1-01] Inventory redundant fragments in sample/18 Rust output (clone/index/scan/format) and fix improvement targets.
- [x] [ID: P1-RS-S18-QUALITY-01-S1-02] Finalize implementation order by expected effect/risk and define fail-closed applicability boundaries.
- [x] [ID: P1-RS-S18-QUALITY-01-S2-01] Add borrow-priority paths in `current_token/previous_token/eval_expr` and remove unnecessary `clone`.
- [x] [ID: P1-RS-S18-QUALITY-01-S2-02] Add fastpath to omit index normalization expressions where non-negative indices are guaranteed.
- [x] [ID: P1-RS-S18-QUALITY-01-S2-03] Degrade tokenize character scanning from generic `String` path to lightweight paths (bytes/chars).
- [x] [ID: P1-RS-S18-QUALITY-01-S2-04] Reduce map dependency in small fixed token decisions and simplify branching/lookup.
- [x] [ID: P1-RS-S18-QUALITY-01-S2-05] Simplify `to_string/format!` chains toward equivalent direct construction.
- [x] [ID: P1-RS-S18-QUALITY-01-S2-06] Implement paths that can degrade `&Vec<T>` inputs to `&[T]`.
- [x] [ID: P1-RS-S18-QUALITY-01-S2-07] Reevaluate necessity of `BTreeMap` usage and switch order-independent paths to lighter maps.
- [x] [ID: P1-RS-S18-QUALITY-01-S3-01] Add unit/golden regressions to detect recurrence of redundant output patterns.
- [x] [ID: P1-RS-S18-QUALITY-01-S3-02] Verify non-regression via sample/18 regeneration and transpile/smoke/parity.

## Inventory Results (S1-01)

- Excessive `clone`:
  - `current_token/previous_token` return `Token` by clone (`clone()` + index normalization).
  - Leading `ExprNode` in `eval_expr` is acquired by clone.
  - Caller-side clone in `Parser::new((tokens).clone())`.
- Index normalization expressions:
  - Many occurrences of `vec[((if idx < 0 { len + idx } else { idx }) as usize)]` (`expr_nodes/tokens`).
  - The same expression remains even for `pos/expr_index` paths where non-negativity is guaranteed.
- Scan/lookup:
  - `ch` in `tokenize` is stringified each time (`py_str_at(...).to_string()`).
  - Single-character token decisions perform `BTreeMap<String, i64>` lookup each time.
- String construction:
  - Deep nesting via `format!("{}{}", format!("{}{}", ...))` chains.
  - `to_string()` is widely attached even to short-lived values.
- API shape:
  - Function arguments are fixed to `&Vec<T>` and still have degradable spots to `&[T]`.

## Implementation Order / Boundaries (S1-02)

- Implementation order (expected effect/safety):
  1. `S2-01` borrow priority (clone reduction, easy semantic preservation)
  2. `S2-02` non-negative index fastpath (clear boundary)
  3. `S2-06` `&Vec<T> -> &[T]` (low risk)
  4. `S2-05` string construction simplification
  5. `S2-03` tokenize scan lightweighting
  6. `S2-04` token-decision map review
  7. `S2-07` map-structure reevaluation (broader impact)
- fail-closed rules:
  - Do not optimize when type/bounds cannot be determined.
  - Apply index fastpath only where `idx >= 0` is syntactically guaranteed.
  - Apply borrow conversion only where mutable aliasing cannot occur.
  - Apply lookup-structure changes only where output-order dependency is confirmed absent.
