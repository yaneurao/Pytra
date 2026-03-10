# P2: Typed Compiler Boundaries and Retreat of Internal Object Carriers

Last updated: 2026-03-10

Related TODO:
- `ID: P2-COMPILER-TYPED-BOUNDARY-01` in `docs/ja/todo/index.md`

Background:
- Pytra mainly targets typed Python, but compiler/selfhost internal boundaries still widely rely on `dict[str, object]`, `list[object]`, and `make_object(...)`.
- `transpile_cli`, `backend_registry_static`, selfhost parser artifacts, and generated compiler runtime still move compiler roots, backend specs, layer options, and AST nodes through object carriers in multiple lanes.
- That was useful during bootstrap, but it no longer matches the typed-Python implementation philosophy and now blocks retreating `make_object` out of compiler internals.
- Until the compiler boundary itself becomes typed, aggressive `make_object` removal would break the selfhost/compiler path.

Goal:
- Move known-schema compiler/selfhost payloads onto nominal typed carriers and push internal `dict[str, object]`, `list[object]`, and `make_object(...)` usage back to explicit adapter seams.
- Restrict `make_object`, `py_to`, and `obj_to_*` to user-facing `Any/object` boundaries, JSON seams, and legacy export seams, rather than known-schema compiler internals.
- Make the "typed Python is the source of truth" policy consistent across selfhost/compiler implementation boundaries.

Scope:
- `src/toolchain/frontends/transpile_cli.py` and its selfhost-expanded artifacts
- `src/runtime/cpp/native/compiler/{transpile_cli,backend_registry_static}.{h,cpp}`
- `src/runtime/cpp/generated/compiler/*` and `selfhost/runtime/cpp/pytra-gen/compiler/*`
- Selfhost parser / EAST builder paths, mainly `src/toolchain/ir/core.py` and the modules split out of it
- Docs, guards, and regression tests around compiler boundaries

Out of scope:
- Removing user-facing `Any/object` functionality itself
- Deleting the entire `make_object` overload family from `py_runtime.h` in one shot
- Fully removing the stage1 selfhost host-Python bridge in this plan alone
- Redesigning the entire C++ runtime

## Mandatory Rules

1. Any compiler-internal payload with a known schema must use a nominal typed carrier rather than `dict[str, object]`.
2. `dict[str, object]` and `list[object]` are allowed only at explicit seams such as JSON decode, extern/hooks, and legacy adapters.
3. The selfhost parser / EAST builder must not keep raw `dict<str, object>{{...}}` assembly as the canonical path; typed node constructors or builder helpers must be the source of truth.
4. Dynamic JSON values used inside the compiler must be isolated behind a dedicated nominal type such as `JsonValue`, not expanded generic object helpers.
5. Compiler-side `make_object`, `py_to`, and `obj_to_*` usage may remain only when it is explicitly classified as `user_boundary`, `json_adapter`, or `legacy_migration_adapter`.
6. Do not add new generic carriers during the migration. If a temporary legacy adapter remains, its removal step must be fixed in the plan / decision log.
7. Backends/runtimes must not paper over typed-boundary gaps by adding more object fallback helpers.

## Acceptance Criteria

- Canonical compiler entrypoints such as `load_east3_document` treat typed root carriers as the source of truth.
- `backend_registry_static` passes backend specs, layer options, and IR through typed carriers plus explicit adapters.
- Checked-in selfhost parser / generated compiler paths no longer assemble AST nodes directly through `dict<str, object>{{... make_object(...) ...}}`.
- Remaining compiler-lane `make_object` / `py_to` usage is explicitly classified and limited to user-facing `Any/object` boundaries or adapter seams.
- Guards exist so typed-boundary regressions fail fast.

## S3-02 Redefinition

`S3-02` is no longer "keep extracting one helper at a time." It closes only when all of the following are true.

1. The `postfix/suffix parser` cluster has been split out of `core.py`, so `call` / `attr` / `subscript` parsing no longer sits in one giant file.
2. The `call annotation` cluster has been split out of `core.py`, so `named-call` / `attr-call` / `callee-call` handling no longer sits in one giant file.
3. Remaining `call-arg` / `suffix tail` / `subscript tail` helper extraction is handled in bundles of 5-10 clusters instead of one-helper commits.
4. Generated/selfhost residual guards and export seams are rebaselined so `make_object` is confined to serialization/export seams.
5. TODO and plan progress notes stay at cluster-summary level; fine-grained helper history lives in git history instead.

## Implementation Order

1. Inventory and classification
2. Lock the typed end state
3. Introduce typed carriers in the Python source of truth
4. Mirror them into generated/native compiler interfaces
5. Retire raw object assembly from the selfhost parser / EAST builder
6. Isolate JSON / hook / legacy adapters
7. Add guards / regressions / archive updates

## Breakdown

- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-01] Inventory remaining `dict[str, object]`, `list[object]`, `make_object`, and `py_to` usage across `transpile_cli`, `backend_registry_static`, selfhost parser paths, and generated compiler runtime, then classify each usage as `compiler_internal`, `json_adapter`, `extern_hook`, or `legacy_bridge`.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S1-02] Lock the typed-boundary contract and non-goals so they stay consistent with `spec-dev`, `spec-runtime`, and `spec-boxing`.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-01] Define typed carrier specs for compiler root payloads: EAST document, backend spec, layer options, and emit request/result.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-02] Introduce typed carriers and thin legacy adapters in the Python source of truth.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S2-03] Introduce typed carrier mirrors or typed wrapper APIs in the C++ selfhost/native compiler interfaces and reduce raw `dict<str, object>` exchange.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-01] Move selfhost parser / EAST builder node construction onto typed constructors / builder helpers and gradually retire direct `dict<str, object>{{...}}` assembly.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Retreat remaining `make_object` usage in generated compiler / selfhost runtime down to serialization/export seams only.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-A] Redefine the `S3-02` completion criteria and compress TODO/plan progress notes to cluster-level summaries.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-B] Split the postfix/suffix parser cluster out of `core.py` and move `call` / `attr` / `subscript` parsing into dedicated modules.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-C] Split the call-annotation cluster out of `core.py` and move `named-call` / `attr-call` / `callee-call` handling into dedicated modules.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-D] Finish the remaining `call-arg` / `suffix tail` / `subscript tail` helper extraction in bundles of 5-10 clusters.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-E] Rebaseline generated/selfhost residual guards and export seams, retreat `make_object` to serialization/export seams only, and close `S3-02`.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] Separate JSON, extern/hooks, and intentionally dynamic carriers from the compiler typed model behind `JsonValue` or explicit adapters.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] Label every remaining `make_object` / `py_to` / `obj_to_*` usage and add guards that reject uncategorized reintroduction.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] Refresh selfhost build/diff/prepare/bridge regressions and lock non-regression after the typed-boundary changes.
- [ ] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-02] Update docs / TODO / archive and record whether each remaining `make_object` usage is `user boundary only` or `explicit adapter only`.

## `core.py` Split Policy

- `core.py` should ultimately keep orchestration and shared helpers only.
- The `postfix/suffix parser` cluster should be split into dedicated modules for `call` / `attr` / `subscript`.
- The `call annotation` cluster should be split into dedicated modules for `named-call` / `attr-call` / `callee-call`.
- Small `call-arg` / `suffix tail` / `subscript tail` helper work should then be processed in bundle-sized batches inside those split modules.
- `test_east_core.py` should also be regrouped around cluster-level guards instead of one-assert-per-helper growth.

## Expected Deliverables

### S2

- `transpile_cli` and `backend_registry_static` use typed payloads as their canonical path.
- Legacy `dict[str, object]` APIs survive only as thin adapters.

### S3

- The selfhost parser / EAST builder uses nominal node builders.
- `core.py` is no longer a single giant file that only grows via more helper extraction.
- Generated/selfhost runtime `make_object` usage is pushed back toward export seams.

### S4

- Only genuinely dynamic lanes such as `JsonValue` or extern/hook adapters keep object carriers.
- Remaining compiler-internal generic carriers are all justified and classifiable.

### S5

- Selfhost regressions and audits detect any collapse back to generic compiler carriers.
- The end state remains traceable in docs/TODO/archive.

Decision log:
- 2026-03-09: Added P2 in response to the user request to prioritize typed compiler boundaries over trying to delete `make_object` directly.
- 2026-03-09: Fixed the policy that user-facing `Any/object` boundaries remain part of the current contract; P2 focuses on compiler/selfhost internal dynamic-carrier cleanup instead.
- 2026-03-09: Moved the canonical typed carrier contract into `typed_boundary.py`, host/static registries, and native C++ wrappers, while shrinking raw dict surfaces to thin legacy adapters.
- 2026-03-10: Closed `S3-01`. Checked-in source-of-truth node construction is now largely on `_sh_make_*` helper contracts, and module root / import / expr / stmt / comprehension / f-string / trivia / span carriers are guarded there.
- 2026-03-10: Early `S3-02` work centralized typed export seams around `typed_boundary.py`, moved the selfhost entrypoint onto the direct typed path, and expanded generated/selfhost residual guards plus source-of-truth fail-fast checks across module root, import, expr, stmt, literal, comprehension, and f-string lanes.
- 2026-03-10: However, `core.py` grew beyond 11k lines and `test_east_core.py` beyond 4k lines, while one-helper commits and one-helper progress notes became too fine-grained for the actual amount of progress.
- 2026-03-10: From this point on, `S3-02` proceeds only through `S3-02-B` to `S3-02-E` cluster units. TODO keeps only cluster summaries, and helper-level history is compressed into git history plus minimal decision-log summaries.
- 2026-03-10: `core.py` splitting is now an explicit deliverable. The first split targets are the `postfix/suffix parser` cluster and the `call annotation` cluster; only after that do the remaining `call-arg` / `suffix tail` / `subscript tail` bundles continue.
- 2026-03-10: The first `S3-02-B` batch moved the `call-arg` / `call-suffix` parser cluster into `core_expr_call_suffix.py`, leaving `core.py` with mixin import plus postfix-dispatch orchestration. Source guards also switched from per-helper assertions to split-cluster assertions.
- 2026-03-10: The `attr/subscript suffix` parser cluster also moved into `core_expr_attr_subscript_suffix.py`, so the `call` / `attr` / `subscript` suffix parser family is now split out of `core.py`. `S3-02-B` is considered complete and the next target is the `call annotation` cluster split.
- 2026-03-10: The first `S3-02-C` batch moves `call_expr` / `callee_call` orchestration into `core_expr_call_annotation.py`, while lower-level `named-call` / `attr-call` apply paths and shared helpers remain in `core.py` for now. Source guards are updated around the split-cluster boundary instead of per-helper locations.
