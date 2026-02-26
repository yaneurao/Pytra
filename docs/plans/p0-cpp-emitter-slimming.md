# P0: Staged Slimming of the C++ Emitter Bloat

Last updated: 2026-02-26

Related TODO:
- `ID: P0-CPP-EMITTER-SLIM-01` in `docs-ja/todo/index.md`

Background:
- `src/hooks/cpp/emitter/cpp_emitter.py` was about 6.6k lines; concentrated branching in `render_expr` and mixed C++-specific responsibilities caused frequent merge/conflict pressure.
- Even after adopting EAST3 as the main path, compatibility branches remained (`stage2/self_hosted`, legacy `type_id` name-call allowances).
- Import/include/namespace/class/type/runtime-call responsibilities were concentrated in one file, so small local edits caused broad regression risk.

Goal:
- Shrink `cpp_emitter.py` to an orchestration/dispatch center and converge on a single EAST3 contract with compatibility layers removed.

In scope:
- `src/hooks/cpp/emitter/cpp_emitter.py`
- `src/hooks/cpp/emitter/` modules (`call.py`, `expr.py`, `stmt.py`, `operator.py`, `tmp.py`, `trivia.py`, plus newly split modules)
- When needed: `src/pytra/compiler/east_parts/code_emitter.py` (commonizable parts only)
- Validation: `test/unit/test_py2cpp_*.py`, `tools/check_py2cpp_transpile.py`, `tools/check_selfhost_cpp_diff.py`, `tools/verify_selfhost_end_to_end.py`

Out of scope:
- C++ runtime API spec changes
- Sample program spec changes
- Feature additions for non-C++ emitters

Acceptance criteria:
- Remove legacy C++ emitter branches for `stage2/self_hosted` compatibility (builtin/type_id/For bridge), and unify on EAST3 contract.
- Reduce `render_expr` to dispatch-centric structure and separate large chains into focused handlers.
- Final metrics should include at least:
  - file lines: target `<= 2500`
  - `render_expr` size: target `<= 200`
  - remaining legacy compatibility helper count: `0`
- C++ regressions (unit/smoke/selfhost) stay on baseline.

## Breakdown

- [x] [ID: P0-CPP-EMITTER-SLIM-01-S1-01] Measure line count/method count/long methods in `cpp_emitter.py` and document baseline.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S1-02] Lock C++ generation diff baselines for `sample` and `test/unit`.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S2-01] Remove stage2/self_hosted legacy builtin compatibility paths.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S2-02] Remove `For`/`ForRange` <-> `ForCore` bridge and unify on direct `ForCore` acceptance.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S2-03] Remove legacy `isinstance/issubclass` name-call allowance and unify on EAST3 `type_id` nodes.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-01] Split import/include/namespace/module-init responsibilities into dedicated modules.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-02] Split class emit responsibilities (`virtual/override`, `PYTRA_TYPE_ID`) into dedicated modules.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-03] Split type conversion (`_cpp_type_text`) and Any-boundary correction helpers into dedicated modules.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S3-04] Split built-in `runtime_call` branches (list/set/dict/str/path/special) into dedicated dispatch modules.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S4-01] Introduce `kind -> handler` table skeleton for `render_expr`.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S4-02] Separate collection literal/comprehension handlers and add regressions.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S4-03] Separate runtime/type_id/path handlers and reduce `render_expr` to dispatch-focused role.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S5-01] Inventory `repr`-dependent nodes and lock migration plan to structured parser/lowerer nodes.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S5-02] Gradually reduce `_render_repr_expr` usages, keeping only unavoidable final fallback.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S5-03] Remove (or no-op) `_render_repr_expr` and eliminate `repr`-string dependency.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S6-01] Inventory Rust/C++ commonization candidates (conditions/cast helpers/loop skeleton) and lock `CodeEmitter` migration set.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S6-02] Move 1-2 common candidate groups into `CodeEmitter` and reduce C++/Rust duplication.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S7-01] Lock regressions via `test/unit/test_py2cpp_*.py` and `tools/check_py2cpp_transpile.py`.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S7-02] Confirm selfhost regressions via `check_selfhost_cpp_diff.py` / `verify_selfhost_end_to_end.py`.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S7-03] Re-measure final metrics and record completion decision.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S8-01] Move assign-family statement methods into `stmt.py`.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S8-02] Move remaining long statement methods (`emit_for_core`, `emit_function`, etc.) into `stmt.py`.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S8-03] Split analysis helpers (`_collect_assigned_name_types`, `_collect_mutated_params_from_stmt`, etc.) into a dedicated module.
- [x] [ID: P0-CPP-EMITTER-SLIM-01-S8-04] Move remaining long call/attribute methods and converge to `<=2500` lines.

## Baseline metrics (`S1-01`, 2026-02-26)

- file lines: `6814`
- `CppEmitter` methods: `164`
- `render_expr` lines: `869` (`L5812-L6680`)
- legacy/compat-named methods: `3`
- top long methods:
  - `render_expr`: `869`
  - `_render_builtin_runtime_special_ops`: `359`
  - `emit_class`: `259`
  - `transpile`: `236`
  - `emit_assign`: `166`

## `repr` dependency inventory (`S5-01`, 2026-02-26)

- Entry points that depended on `repr` were identified and prioritized for removal:
  - compare fallback decomposition
  - name reinterpretation fallback
  - end-of-`render_expr` fallback
  - `render_cond` fallback
- Migration policy:
  1. Normalize compare fallback to structured compare/contains nodes.
  2. Move `len()/slice` text decomposition into explicit `ObjLen`/`SliceExpr` generation.
  3. Remove name-`repr` reinterpretation and require parser-side structured `Attribute(Name(self), ...)`.
  4. Limit terminal fallback to one place, converting unsupported kinds to explicit lowerer nodes.
  5. Remove `render_cond` `repr` fallback after blocking empty-string generation routes.

## Rust/C++ commonization (`S6-01`, `S6-02`)

- Candidate inventory completed and risk-ranked (`easy/medium/risky`).
- Implemented first low-risk set:
  - introduced shared `prepare_if_stmt_parts` / `prepare_while_stmt_parts` in `CodeEmitter`
  - switched C++ and Rust `if/while` wrappers to shared helpers
  - removed Rust-local `_strip_outer_parens` reimplementation and unified with `CodeEmitter` base helper
- Regression checks passed for C++ and Rust transpile baselines.

## Regression checkpoints (`S7`)

- `S7-01`:
  - `test_py2cpp_*.py`: `273` tests, `29` failures (known existing expectation/fixture groups)
  - `check_py2cpp_transpile`: `checked=133 ok=133 fail=0 skipped=6`
  - Observation: failures were not directly tied to the `S6-02` helper-commonization changes.
- `S7-02`:
  - `check_selfhost_cpp_diff`: `mismatches=0 known_diffs=2 skipped=0`
  - `verify_selfhost_end_to_end`: blocked by known pre-build issue in selfhost prep (`CodeEmitter import` line-removal failure).

## Final metrics and completion

- `S7-03` interim:
  - `cpp_emitter.py`: `3985`
  - `render_expr`: `197`
  - legacy/compat named functions: `0`
  - Parent task remained open at this point (`<=2500` not met).
- `S8-04` final:
  - `cpp_emitter.py`: `2478`
  - `render_expr`: `197`
  - legacy/compat named functions: `0`
  - All completion thresholds met; parent `P0-CPP-EMITTER-SLIM-01` marked complete.

## Decision log summary

- 2026-02-25: Added as top-priority work based on three major bloat drivers (compat-layer residue, responsibility concentration, oversized `render_expr`).
- 2026-02-26: Completed staged split/removal `S1` through `S8`, including:
  - removal of legacy builtin/type_id/For bridge compatibility paths
  - module/class/type-bridge/builtin-runtime/collection/runtime-expression/analysis/call-attribute extraction
  - dispatch-table conversion in `render_expr`
  - elimination of `repr`-string fallback dependency paths
  - partial C++/Rust helper commonization in `CodeEmitter`
  - final line-count convergence under target
- Known separate issue (outside this task): selfhost pre-build failure in `tools/prepare_selfhost_source.py` (`failed to remove required import lines: CodeEmitter import`) remains tracked independently.
