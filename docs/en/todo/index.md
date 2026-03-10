# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-11

## Context Operation Rules

- Every task must include an `ID` and a context file (`docs/ja/plans/*.md`).
- To override priority, issue chat instructions in the format of `docs/ja/plans/instruction-template.md`; do not use `todo2.md`.
- The active target is fixed to the highest-priority unfinished ID (smallest `P<number>`, and the first one from the top when priorities are equal); do not move to lower priorities unless there is an explicit override instruction.
- If even one `P0` remains unfinished, do not start `P1` or lower.
- Before starting, check `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress memos and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memos in `docs/ja/todo/index.md` to a one-line summary only; details such as decisions and verification logs must be recorded in the `Decision log` of the context file (`docs/ja/plans/*.md`).
- If one `ID` is too large, you may split it into child tasks in `-S1` / `-S2` format in the context file, but keep the parent checkbox open until the parent `ID` is completed.
- If uncommitted changes remain due to interruptions, do not start a different `ID` until you complete the same `ID` or revert the diff.
- When updating `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and verify that each progress `ID` added in the diff matches the highest-priority unfinished `ID` or one of its child IDs.
- Append in-progress decisions to the context file `Decision log`.
- For temporary output, use existing `out/` or `/tmp` only when necessary, and do not add new temporary folders under the repository root.

## Notes

- This file keeps unfinished tasks only.
- Completed tasks are moved to history via `docs/ja/todo/archive/index.md`.
- `docs/ja/todo/archive/index.md` keeps only the index, and the history body is stored by date in `docs/ja/todo/archive/YYYYMMDD.md`.

## Unfinished Tasks


### P3: Harden compiler contracts and make stage/pass/backend handoff fail-closed

Context: [docs/ja/plans/p3-compiler-contract-hardening.md](../plans/p3-compiler-contract-hardening.md)

1. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01] Harden compiler contracts and make stage/pass/backend handoff fail-closed.
2. [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-01] Inventory the current `check_east_stage_boundary`, `validate_raw_east3_doc`, and backend-entry guards, then classify blind spots such as node shape, `type_expr` / `resolved_type`, `source_span`, and helper metadata.
3. [x] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-02] Fix the responsibility boundary between schema validators, invariant validators, and backend input validators so it does not conflict with `P1-EAST-TYPEEXPR-01` or `P2-COMPILER-TYPED-BOUNDARY-01`.
4. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-01] Add the required fields, allowed omissions, and diagnostic categories for EAST3, linked output, and backend input to `spec-dev` or an equivalent design document.
5. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-02] Fix consistency rules and fail-closed policy for `type_expr` / `resolved_type` mirrors, `dispatch_mode`, `source_span`, and helper metadata.
6. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-01] Add central validator primitives around `toolchain/link/program_validator.py` and extend coarse raw EAST3 / linked-output checks to node/meta invariants.
7. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-02] Introduce pre/post validation hooks at representative pass/lowering/linker entries and stop invalid nodes from flowing through silently.
8. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-01] Run representative backends, starting with C++, through compiler-contract validators at entry and replace backend-local crashes or silent fallbacks with structured diagnostics.
9. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-02] Extend `tools/check_east_stage_boundary.py` or its successor so it also detects stage semantic drift, not only stage-boundary violations.
10. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-01] Add representative unit/selfhost regressions so contract violations are reproducible as expected failures.
11. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-02] Update docs / TODO / archive / migration notes so validator updates become mandatory whenever node/meta contracts change.

### P4: Canonicalize `backend_registry` and strengthen selfhost parity gates

Context: [docs/ja/plans/p4-backend-registry-selfhost-parity-hardening.md](../plans/p4-backend-registry-selfhost-parity-hardening.md)

1. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01] Canonicalize `backend_registry` and strengthen selfhost parity gates.
2. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01] Inventory overlapping surfaces between `backend_registry.py` and `backend_registry_static.py` and classify intentional differences versus drift candidates.
3. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02] Inventory current gates and blind spots across `build_selfhost`, `stage2`, `verify_selfhost_end_to_end`, and multi-language selfhost flows, then fix the classification policy for known blocks and regressions in the decision log.
4. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01] Define a canonical source of truth for backend capability, runtime copy, option schema, and writer metadata, and move both host and static registries to derive from it.
5. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-02] Fix the boundary and diagnostics contract for intentional differences such as host-only lazy imports or selfhost-only direct routes.
6. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-01] Move host/static registries onto shared metadata or generation flow and retire handwritten duplication.
7. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-02] Add drift guards or diff tests so backend-surface changes made on only one side fail fast.
8. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-01] Reorganize representative parity suites for stage1, stage2, direct e2e, and multi-language selfhost, and unify failure categorization and summaries.
9. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-02] Align unsupported / preview / known-block / regression diagnostics between registry metadata and parity reports so expected failures are explicitly managed.
10. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-01] Update docs / plan reports / archive so backend readiness, known blocks, and gate execution procedures stay traceable.
11. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-02] Verify that representative internal changes are checked under the same contract in both host and selfhost lanes, then lock that re-entry guard.

### P5: Full rollout of nominal ADT as a language feature

Context: [docs/ja/plans/p5-nominal-adt-language-rollout.md](../plans/p5-nominal-adt-language-rollout.md)

1. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01] Perform the full rollout of nominal ADT as a language feature.
2. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-01] Inventory candidate language-surface designs for nominal ADT declarations, constructors, variant access, and `match`, then choose a selfhost-safe staged rollout.
3. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-02] Fix the boundary between type-system groundwork, narrowing groundwork, and full language-surface rollout so this plan does not conflict with `P1-EAST-TYPEEXPR-01`.
4. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-01] Extend `spec-east`, `spec-user`, and `spec-dev` with nominal-ADT declarations, pattern nodes, `match` nodes, and diagnostics contracts.
5. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-02] Fix the policy and error categories for exhaustiveness checks, duplicate patterns, and unreachable branches.
6. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-01] Update the frontend and selfhost parser so representative nominal-ADT syntax is accepted.
7. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-02] Introduce ADT constructors, variant tests, variant projections, and `match` lowering into EAST/EAST3.
8. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-01] Confirm through representative tests that the built-in `JsonValue` lane and user-defined nominal-ADT lane share the same IR category.
9. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-02] Implement the minimum representative backend support, starting with C++, for constructors, variant checks, destructuring, and `match`, and forbid silent fallbacks.
10. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-01] Define rollout order and fail-closed policy for other backends, and fix diagnostics for unsupported targets.
11. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-02] Update selfhost / docs / archive / migration notes and close the rollout as a formal language feature.
