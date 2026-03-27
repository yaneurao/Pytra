<a href="../../ja/plans/p2-cpp-s18-value-container.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: sample/18 C++ AST Container Value-typing (`list<rc<T>>` -> `list<T>`)

Last updated: 2026-03-02

Related TODO:
- `ID: P2-CPP-S18-VALUE-CONTAINER-01` in `docs/ja/todo/index.md`

Background:
- In sample/18, AST storage is represented as `list<rc<ExprNode>>` / `list<rc<StmtNode>>`, so `rc` operations occur even on read-mostly paths.
- Local containers satisfying non-escape constraints have room to degrade to value storage, but current behavior is biased toward reference management for safety.
- This improvement involves ownership/lifetime judgment, so it requires design and staged rollout rather than immediate `P0` handling.

Goal:
- Use EAST3 non-escape information to establish a path for staged degradation of sample/18 AST containers to value types.

Scope:
- Coordination design between EAST3 non-escape metadata and container ownership hints
- C++ emitter container-type selection rules (branch between `rc` and value types)
- Sample/18-first rollout and regression locking

Out of scope:
- Simultaneous rollout to all backends
- Full replacement of `PyObj` / `rc` runtime model

Acceptance criteria:
- Value-typing conditions are specified for `expr_nodes` / `stmts` in sample/18.
- Paths that do not satisfy conditions keep `rc` as before, with fail-closed behavior and no fallback regression.
- After staged rollout, non-regression is confirmed via unit/transpile/parity checks.

Verification commands (planned):
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_east3_optimizer.py' -v`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit -p 'test_py2cpp_codegen_issues.py' -v`
- `python3 tools/check_py2cpp_transpile.py`

Decision log:
- 2026-03-01: Based on user direction, filed AST container value-typing for sample/18 as a `P2` plan.
- 2026-03-02: As S1-01, inventoried AST container usage in sample/18 and confirmed `expr_nodes`/`stmts` are used as append + read-only (index/for), with no element leakage to object/Any boundaries.
- 2026-03-02: As S1-02, designed the EAST3->CppEmitter coordination spec. Planned to add `container_ownership_hint_v1` (candidate name) at list type declaration points in `AnnAssign`/`FunctionDef`, choose `list<T>` only when value conditions are met, and fail-closed back to existing `list<rc<T>>` on deviation.
- 2026-03-02: As S2-01/S2-02, introduced conservative value-candidate judgment for dataclasses in `core.py`, and added a branch in `type_bridge.py` to keep `list[ValueClass]` as typed containers even with `cpp_list_model=pyobj`. In `sample/18`, `Token/ExprNode/StmtNode` degraded to `list<T>` output, while unsafe conditions kept existing `ref` fallback.
- 2026-03-02: As S3-01, updated `test_east_core.py` (dataclass value/ref boundary) and `test_py2cpp_codegen_issues.py` (sample18 value-type output fragments), and confirmed non-regression via `check_py2cpp_transpile` and parity (case18, cpp).

## S1-01 Inventory Results (sample/18)

- `Parser.expr_nodes`:
  - Declaration: `self.expr_nodes: list[ExprNode]`
  - Write: append-only in `add_expr()`
  - Read: index-only access in `eval_expr()`
  - Escape: retained as member of `Parser` instance; list itself is passed as argument in `execute()` call (no per-element objectization)
- `stmts`:
  - Declaration: `parse_program() -> list[StmtNode]`
  - Write: append-only in `parse_program()`
  - Read: for-each only in `execute()`
  - Escape: list itself is returned and used immediately (no per-element objectization)
- Non-value-type triggers (fail-closed conditions):
  - Element type includes `object/Any/union`
  - Elements are passed into object contexts (boxing/unboxing required)
  - List element references escape to external functions as mutable aliases
  - Declaration type and actual element type do not match

## S1-02 Coordination Spec (Design)

- EAST3 side:
  - Attach `container_ownership_hint_v1` at declaration points.
  - Minimum schema proposal:
    - `version`: `"1"`
    - `owner_name`: variable name
    - `container_type`: e.g. `list[ExprNode]`
    - `element_storage`: `"value" | "ref"`
    - `safe`: `true|false`
    - `reason`: judgment rationale (for debugging)
  - `safe=true` only for cases meeting non-escape conditions + type match.
- CppEmitter side:
  - Switch container declaration type to `list<T>` only when `safe=true` and `element_storage=value`.
  - If hint is absent/inconsistent or `safe=false`, revert to existing behavior (`list<rc<T>>`).
  - Judge function arguments/return values with the same hint contract; no one-sided value-typing.
- Staged rollout:
  - First target only `expr_nodes` / `stmts` in sample/18.
  - Generalize after accumulating regressions in S2/S3.

## Breakdown

- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-01] Inventory AST container usage in sample/18 and define non-escape conditions for value-typing.
- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S1-02] Design EAST3 metadata (ownership hints / non-escape) and C++ emitter coordination spec.
- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-01] Implement value-type output for `expr_nodes` / `stmts` in sample/18 first.
- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S2-02] Implement fail-closed conditions that auto-fallback to `rc` for deviation cases.
- [x] [ID: P2-CPP-S18-VALUE-CONTAINER-01-S3-01] Add regression tests (type-output fragments + execution consistency) and lock recurrence detection.
