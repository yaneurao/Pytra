# TODO (Open)

> `docs/ja/` is the source of truth. `docs/en/` is its translation.

<a href="../../ja/todo/index.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

Last updated: 2026-03-09

## Context Operation Rules

- Every task must include an `ID` and a context file (`docs/ja/plans/*.md`).
- To override priority, issue chat instructions in the format of `docs/ja/plans/instruction-template.md`; do not use `todo2.md`.
- The active target is fixed to the highest-priority unfinished ID (smallest `P<number>`, and the first one from the top when priorities are equal); do not move to lower priorities unless there is an explicit override instruction.
- If even one `P0` remains unfinished, do not start `P1` or lower.
- Before starting, check `Background` / `Out of scope` / `Acceptance criteria` in the context file.
- Progress memos and commit messages must include the same `ID` (example: `[ID: P0-XXX-01] ...`).
- Keep progress memos in `docs/ja/todo/index.md` to a one-line summary only; details (decisions and verification logs) must be recorded in the `Decision log` of the context file (`docs/ja/plans/*.md`).
- If one `ID` is too large, you may split it into child tasks in `-S1` / `-S2` format in the context file (keep the parent checkbox open until the parent `ID` is completed).
- If uncommitted changes remain due to interruptions, do not start a different `ID` until you complete the same `ID` or revert the diff.
- When updating `docs/ja/todo/index.md` or `docs/ja/plans/*.md`, run `python3 tools/check_todo_priority.py` and verify that each progress `ID` added in the diff matches the highest-priority unfinished `ID` (or its child `ID`).
- Append in-progress decisions to the context file `Decision log`.
- For temporary output, use existing `out/` (or `/tmp` only when necessary), and do not add new temporary folders under the repository root.

## Notes

- This file keeps unfinished tasks only.
- Completed tasks are moved to history via `docs/ja/todo/archive/index.md`.
- `docs/ja/todo/archive/index.md` keeps only the index, and the history body is stored by date in `docs/ja/todo/archive/YYYYMMDD.md`.

## Unfinished Tasks

### P0: Realign the C++ `py_runtime.h` core boundary and move remaining helpers back upstream / to dedicated lanes

Context: [docs/ja/plans/p0-cpp-pyruntime-core-boundary-realign.md](../plans/p0-cpp-pyruntime-core-boundary-realign.md)

1. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01] Realign the `py_runtime.h` core boundary and move remaining helpers back upstream / to dedicated lanes.
2. [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-01] Inventory checked-in callers of `numeric_ops/zip_ops/contains`, typed helpers, tuple helpers, and `type_id` wrappers, then classify the end state.
3. [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S1-02] Record include ownership, upstream contracts, and non-goals in the decision log so they match `spec-runtime`.
4. [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-01] Extend helper-include collection in the C++ emitter / prelude / generated path so `zip`, `contains`, and numeric helpers are explicitly included.
5. [x] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S2-02] Remove transitive `numeric_ops` / `zip_ops` / `contains` includes from `py_runtime.h` and update the removed-include guards.
6. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-01] Switch typed dict subscripts to `.at()` and remove checked-in `py_dict_get` callers.
7. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-02] Move tuple constant-index access to `std::get<N>` even in generated/runtime paths, and slim or retire the tuple `py_at` helper.
8. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-03] Shrink typed list/dict mutation helpers down to object-bridge-only surface, prioritizing direct emitter lowering for typed lanes.
9. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-01] Move ownership of `type_id` registry / subtype / isinstance logic to `py_tid_*`, and slim the wrappers in `py_runtime.h`.
10. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S4-02] Update `test_cpp_runtime_type_id.py` and generated runtime callers, and add a guard so cyclic ownership does not reappear.
11. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-01] Clean up small remaining surfaces such as the `py_isinstance_of` fast path and the `PyFile` alias.
12. [ ] [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S5-02] Refresh representative tests / parity / docs / archive and close the task.
- Progress memo: [ID: P0-CPP-PYRUNTIME-CORE-BOUNDARY-01-S3-01] Completed `S2-02` by removing transitive `numeric_ops/zip_ops/contains` includes from `py_runtime.h` and updating checked-in callers plus removed-include guards to require explicit helper headers. Next, switch typed dict subscripts to `.at()` and remove checked-in `py_dict_get` callers.

### P1: Structure EAST type representation and lift union / nominal ADT / narrowing out of string processing

Context: [docs/ja/plans/p1-east-typeexpr-strengthening.md](../plans/p1-east-typeexpr-strengthening.md)

1. [ ] [ID: P1-EAST-TYPEEXPR-01] Structure EAST type representation and lift union / nominal ADT / narrowing out of string processing.
2. [ ] [ID: P1-EAST-TYPEEXPR-01-S1-01] Inventory `split_union` / `normalize_type_name` / `resolved_type` string dependencies across frontend, lowering, optimizer, and backends, then classify them into `optional`, `dynamic union`, `nominal ADT`, and `generic container` usage.
3. [ ] [ID: P1-EAST-TYPEEXPR-01-S1-02] Lock the end state, non-goals, and migration order in the decision log so they remain consistent with archived `EAST123` and `JsonValue` contracts.
4. [ ] [ID: P1-EAST-TYPEEXPR-01-S2-01] Extend `spec-east` / `spec-dev` with `TypeExpr` schema, the three-way union classification, and the authority relationship between `type_expr` and `resolved_type`.
5. [ ] [ID: P1-EAST-TYPEEXPR-01-S2-02] Fix the IR contract that treats `JsonValue` as a nominal closed ADT rather than a generic union, including decode/narrowing responsibility and backend fail-closed rules.
6. [ ] [ID: P1-EAST-TYPEEXPR-01-S3-01] Update frontend type-annotation parsing to build `TypeExpr` from `int | bool`, `T | None`, and nested generic unions.
7. [ ] [ID: P1-EAST-TYPEEXPR-01-S3-02] Keep a migration `resolved_type` string mirror temporarily, but add validators and mismatch guards that treat `type_expr` as the source of truth.
8. [ ] [ID: P1-EAST-TYPEEXPR-01-S4-01] In `EAST2 -> EAST3`, distinguish optionals, dynamic unions, and nominal ADTs, and introduce instructions or metadata for narrowing / variant checks / decode helpers.
9. [ ] [ID: P1-EAST-TYPEEXPR-01-S4-02] Connect a representative `JsonValue` narrowing path (`as_obj/as_arr/as_int/...` or equivalent decode operations) through IR-first lowering rather than backend-local special cases.
10. [ ] [ID: P1-EAST-TYPEEXPR-01-S5-01] Use C++ as the first target and replace at least part of the current `general union -> object` path with fail-closed behavior or structured lowering.
11. [ ] [ID: P1-EAST-TYPEEXPR-01-S5-02] Audit other backends for `String/object` union fallbacks and align unsupported `TypeExpr` unions to explicit errors or guarded compatibility paths.
12. [ ] [ID: P1-EAST-TYPEEXPR-01-S6-01] Put a representative `JsonValue` lane on top of the new `TypeExpr` / nominal-ADT contract and verify that future runtime work can proceed IR-contract-first.
13. [ ] [ID: P1-EAST-TYPEEXPR-01-S6-02] Refresh selfhost / unit / docs / archive and add guards against the reintroduction of stringly-typed union debt.

### P2: Move compiler boundaries to typed carriers and retreat internal object-carrier / `make_object` usage

Context: [docs/ja/plans/p2-compiler-typed-boundary.md](../plans/p2-compiler-typed-boundary.md)

1. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01] Move compiler boundaries to typed carriers and retreat internal object-carrier / `make_object` usage.
2. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01] Inventory remaining `dict[str, object]`, `list[object]`, `make_object`, and `py_to` usage across `transpile_cli`, `backend_registry_static`, selfhost parser paths, and generated compiler runtime, then classify each usage as `compiler_internal`, `json_adapter`, `extern_hook`, or `legacy_bridge`.
3. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02] Lock the typed-boundary contract and non-goals so they stay consistent with `spec-dev`, `spec-runtime`, and `spec-boxing`.
4. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-01] Define typed carrier specs for compiler root payloads (EAST document, backend spec, layer options, emit request/result).
5. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-02] Introduce typed carriers and thin legacy adapters in the Python source of truth.
6. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-03] Introduce typed carrier mirrors or typed wrapper APIs in the C++ selfhost/native compiler interfaces and reduce raw `dict<str, object>` exchange.
7. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Move selfhost parser / EAST builder node construction onto typed constructors / builder helpers and gradually retire direct `dict<str, object>{{...}}` assembly.
8. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Retreat remaining `make_object` usage in generated compiler / selfhost runtime down to serialization/export seams only.
9. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] Separate JSON, extern/hooks, and other intentionally dynamic carriers from the compiler typed model behind `JsonValue` or explicit adapters.
10. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] Label every remaining `make_object` / `py_to` / `obj_to_*` usage and add guards that reject uncategorized reintroduction.
11. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] Refresh selfhost build/diff/prepare/bridge regressions and lock non-regression after the typed-boundary changes.
12. [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-02] Update docs / TODO / archive and record whether each remaining `make_object` usage is `user boundary only` or `explicit adapter only`.

### P3: Harden compiler contracts and make stage / pass / backend handoffs fail closed

Context: [docs/ja/plans/p3-compiler-contract-hardening.md](../plans/p3-compiler-contract-hardening.md)

1. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01] Harden compiler contracts and make stage / pass / backend handoffs fail closed.
2. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-01] Inventory the current `check_east_stage_boundary`, `validate_raw_east3_doc`, and backend-entry guards, then classify blind spots that still go unchecked (`node shape`, `type_expr` / `resolved_type`, `source_span`, helper metadata).
3. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S1-02] Fix the responsibility boundary between schema validators, invariant validators, and backend-input validators so this plan does not overlap with `P1-EAST-TYPEEXPR-01` or `P2-COMPILER-TYPED-BOUNDARY-01`.
4. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-01] Extend `spec-dev` or equivalent design docs with required fields, allowed omissions, and diagnostic categories for EAST3 / linked output / backend input.
5. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S2-02] Fix the consistency rules and fail-closed policy for `type_expr` / `resolved_type` mirrors, `dispatch_mode`, `source_span`, and helper metadata.
6. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-01] Add central validator primitives around `toolchain/link/program_validator.py` and expand raw EAST3 / linked-output checks from coarse validation into node/meta invariant checks.
7. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S3-02] Add pre/post validation hooks to representative passes, lowering entrypoints, and linker entrypoints so malformed nodes stop propagating.
8. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-01] Run compiler-contract validators at representative backend entrypoints (first C++) and replace backend-local crashes or silent fallback with structured diagnostics.
9. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S4-02] Extend `tools/check_east_stage_boundary.py` or its successor guard so it can detect stage semantic-contract drift too.
10. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-01] Add representative unit/selfhost regressions so contract violations are reproducible as expected failures.
11. [ ] [ID: P3-COMPILER-CONTRACT-HARDENING-01-S5-02] Refresh docs / TODO / archive / migration notes and fix the rule that validator updates are mandatory when new nodes/meta are introduced.

### P4: Canonicalize backend-registry metadata and strengthen selfhost parity gates

Context: [docs/ja/plans/p4-backend-registry-selfhost-parity-hardening.md](../plans/p4-backend-registry-selfhost-parity-hardening.md)

1. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01] Canonicalize backend-registry metadata and strengthen selfhost parity gates.
2. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01] Inventory duplicated surfaces across `backend_registry.py` and `backend_registry_static.py` (backend spec, runtime copy, writer rules, option schema, direct-route behavior), then classify each difference as intentional or drift-prone.
3. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02] Inventory current gates and blind spots across `build_selfhost`, stage2, direct e2e verification, and multilang selfhost tools, then fix the known-block vs regression classification policy in the decision log.
4. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01] Define the canonical source of truth for backend capability, runtime-copy rules, option schema, and writer metadata so both host and static registries can be derived from it.
5. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-02] Fix the boundaries where intentional differences are allowed (for example host-only lazy imports or selfhost-only direct routes) together with their diagnostic contracts.
6. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-01] Move host/static registries toward shared metadata, a generator, or equivalent adapters and retire avoidable handwritten duplication.
7. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-02] Add a registry-drift guard or diff test so one-sided backend-surface updates fail fast.
8. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-01] Reorganize representative stage1 / stage2 / direct e2e / multilang selfhost parity suites so they report a stable shared summary and failure taxonomy.
9. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-02] Align unsupported / preview / known-block / regression diagnostics between registry code and parity reports so expected failures are explicitly managed.
10. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-01] Refresh docs / plan reports / archive so backend readiness, known blocks, and gate execution flow remain traceable.
11. [ ] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-02] Verify that representative internal changes are checked through equivalent contracts on both host and selfhost lanes, then fix reintroduction guards.

### P5: Full rollout of nominal ADTs as a language feature

Context: [docs/ja/plans/p5-nominal-adt-language-rollout.md](../plans/p5-nominal-adt-language-rollout.md)

1. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01] Carry out the full rollout of nominal ADTs as a language feature.
2. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-01] Inventory candidate language surfaces for nominal ADT declarations, constructors, variant access, and `match`, then decide on a selfhost-safe staged introduction path.
3. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S1-02] Fix the boundary between type-system base work, narrowing-base work, and full language-feature work so this plan does not overlap with `P1-EAST-TYPEEXPR-01`.
4. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-01] Extend `spec-east` / `spec-user` / `spec-dev` with nominal-ADT declaration surface, pattern nodes, match nodes, and diagnostic contracts.
5. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S2-02] Fix the static-check policy and error categories for exhaustiveness, duplicate patterns, and unreachable branches.
6. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-01] Update frontend and selfhost parser paths so they can accept representative nominal-ADT syntax.
7. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S3-02] Introduce ADT constructors, variant tests, variant projection, and `match` lowering into EAST/EAST3.
8. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-01] Verify through representative tests that built-in `JsonValue` and user-defined nominal ADTs use the same IR category.
9. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S4-02] Implement the minimal constructor / variant-check / destructuring / `match` path in a representative backend (first C++) and forbid silent fallback.
10. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-01] Organize rollout order and fail-closed policy for other backends, and fix diagnostics for unsupported targets.
11. [ ] [ID: P5-NOMINAL-ADT-ROLLOUT-01-S5-02] Refresh selfhost / docs / archive / migration notes and close the full nominal-ADT rollout plan.
