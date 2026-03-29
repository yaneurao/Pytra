<a href="../../../ja/plans/archive/20260311-p2-compiler-typed-boundary.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: Typed Compiler Boundaries and Retreat of Internal Object Carriers

Last updated: 2026-03-11

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
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02] Retreat remaining `make_object` usage in generated compiler / selfhost runtime down to serialization/export seams only.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-A] Redefine the `S3-02` completion criteria and compress TODO/plan progress notes to cluster-level summaries.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-B] Split the postfix/suffix parser cluster out of `core.py` and move `call` / `attr` / `subscript` parsing into dedicated modules.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-C] Split the call-annotation cluster out of `core.py` and move `named-call` / `attr-call` / `callee-call` handling into dedicated modules.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-D] Finish the remaining `call-arg` / `suffix tail` / `subscript tail` helper extraction in bundles of 5-10 clusters.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S3-02-E] Rebaseline generated/selfhost residual guards and export seams, retreat `make_object` to serialization/export seams only, and close `S3-02`.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-01] Separate JSON, extern/hooks, and intentionally dynamic carriers from the compiler typed model behind `JsonValue` or explicit adapters.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S4-02] Label every remaining `make_object` / `py_to` / `obj_to_*` usage and add guards that reject uncategorized reintroduction.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-01] Refresh selfhost build/diff/prepare/bridge regressions and lock non-regression after the typed-boundary changes.
- [x] [ID: P2-COMPILER-TYPED-BOUNDARY-01-S5-02] Update docs / TODO / archive and record whether each remaining `make_object` usage is `user boundary only` or `explicit adapter only`.

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
- 2026-03-10: Close `S3-02-C` as complete. The `call_expr` / `callee_call` / `named-call` / `attr-call` annotation entrypoints now live in `core_expr_call_annotation.py`, and the remaining fine-grained helper extraction is pushed into `S3-02-D` bundle work.
- 2026-03-10: Start `S3-02-D` by splitting the `call-arg` parser cluster into `core_expr_call_args.py`, leaving `core_expr_call_suffix.py` with the `call suffix` flow itself. The next bundles should use the same granularity for `subscript tail` and `attr/suffix`.
- 2026-03-10: Close `S3-02-D` as complete. `call-arg` now lives in `core_expr_call_args.py`, `call suffix` in `core_expr_call_suffix.py`, and `attr/subscript suffix` in `core_expr_attr_subscript_suffix.py`, while the remaining helper extraction has been regrouped into bundle-sized work.
- 2026-03-10: As the first `S3-02-E` step, rebaseline generated selfhost-core `make_object` usage at function granularity. For now, `to_payload` is treated as the export seam and the rest is guarded explicitly as parser residual.
- 2026-03-10: Residual generated selfhost-core `make_object` guards were split into explicit `export_seam` and `parser_residual` scopes so the export seam classification is readable as a first-class contract instead of a set-difference convention.
- 2026-03-10: The parser residual scope was further split into `expr_parser`, `stmt_parser`, and `lookup` buckets. From here `S3-02-E` can reduce residuals bucket by bucket until only the export seam remains.
- 2026-03-10: The guard now also fixes that `expr_parser | stmt_parser | lookup == parser_residual` and that `export_seam` stays disjoint. From here progress can be measured simply by shrinking each bucket.
- 2026-03-10: Confirm that the source-of-truth compiler lane and native wrapper no longer use `make_object` outside export seams. Generated selfhost-core usage is now rebaselined as `export_seam=to_payload` plus explicit `parser_residual` guards, so `S3-02` is closed and the remaining labeling work moves to `S4-02`.
- 2026-03-10: Start `S4-01` by inventorying the current dynamic-carrier seams into four buckets: `JsonValue` raw carriers, extern-marked stdlib surfaces, the `typed_boundary.py` runtime-hook seam, and compiler-root JSON loading. Lock that inventory in contract tests.
- 2026-03-10: Route `runtime_hook` through `RuntimeHookAdapter` as an explicit seam. Typed specs no longer hold raw hook callables directly; only the export/apply helpers touch the underlying hook. Native compiler-root JSON loading also goes through `_unwrap_compiler_root_json_doc()` / `_coerce_compiler_root_json_doc()` so raw `JsonObj` unwrapping stays inside named adapters.
- 2026-03-10: Add `toolchain/json_adapters.py` on the Python compiler lane and funnel frontend `load_east_document`, `east_io.load_east_from_path`, link manifest/program loader/materializer, and runtime symbol index `loads_obj(...).raw` unwrapping through `load_json_object_doc()` / `export_json_object_dict()` / `unwrap_east_root_json_doc()`.
- 2026-03-10: Toolchain JSON loader seams are now centralized in `toolchain.json_adapters`. `frontends/transpile_cli`, `ir/east_io`, `link_manifest_io`, `materializer`, `program_loader`, and `runtime_symbol_index` no longer keep raw `json.loads_obj(...).raw`; they receive `JsonObj` or exported dicts through named adapters.
- 2026-03-10: The CLI root loaders in `py2x` and `ir2lang` now also use `load_json_object_doc_or_none()`. Outer JSON-root reads are aligned with the same adapter seam, and direct `json.loads_obj(...)` usage retreats into `toolchain.json_adapters`.
- 2026-03-10: The remaining `JsonObj/JsonArr/JsonValue` raw access in `program_validator.py` also moved behind `toolchain.json_adapters`. The validator now uses `coerce_json_object_doc()`, `export_json_object_dict()`, `json_array_length()`, and `export_json_value_raw()` instead of touching raw carrier fields directly.
- 2026-03-10: `extern_var_v1` also moves behind an explicit adapter seam. `toolchain/frontends/extern_var.py` no longer returns raw `dict[str, str]` binding lists and instead validates ambient extern variables through the `AmbientExternBinding` carrier.
- 2026-03-10: `ir2lang` EAST JSON unwrap now also goes through `unwrap_east_root_json_doc()` / `export_json_object_dict()`. The remaining direct `.raw` reads on the outer toolchain CLI lane are now confined to `toolchain.json_adapters`.
- 2026-03-10: Empty `JsonObj` fallbacks and default `JsonValue -> JsonObj` coercion also moved into `toolchain.json_adapters`. `empty_json_object_doc()` / `json_value_as_object_doc_or_empty()` now remove direct `json.JsonObj({})` construction from `py2x`, `ir2lang`, and `program_validator`.
- 2026-03-10: `program_loader` now coerces in-memory module docs through `coerce_json_object_dict()` instead of a `JsonObj` special case, and `typed_boundary.py` keeps compiler-root `raw_module_doc/meta` access behind `export_compiler_root_module_doc()` / `compiler_root_meta_dict()`.
- 2026-03-10: `S4-01` is now closed. Dynamic carriers are confined to the explicit seams in `toolchain.json_adapters`, `RuntimeHookAdapter`, `AmbientExternBinding`, and `pytra.std.json`, so generic raw access has retreated out of the compiler/toolchain core.
- 2026-03-11: `S4-02` re-inventoried the remaining compiler/toolchain `make_object` / `py_to` / `obj_to_*` usage and confirmed that actual usage is now limited to three `obj_to_int64` / `obj_to_dict` sites in native `transpile_cli.cpp`. Those lines are labeled with `P2-object-bridge: legacy_migration_adapter`, and `tools/check/check_compiler_object_bridge_labels.py` plus unit tests fail fast on any unlabeled reintroduction.
- 2026-03-11: As the first `S5-01` slice, `tools/build_selfhost_stage2.py` and `tools/check/check_selfhost_stage2_cpp_diff.py` gained pure helpers, and unit tests now lock the stage2 build command, the stage1 fallback condition, and the stage2 diff command. Typed-boundary regressions should now be caught in selfhost `build/diff`, not only in `prepare`.
- 2026-03-11: The next `S5-01` slice added contract tests for `tools/verify_selfhost_end_to_end.py` and `tools/build_selfhost_stage2.py`. Unit tests now lock the `py2x-selfhost.py -> py2cpp_stage2.cpp` stage2 build command, the `[not_implemented]` fallback copy path, auto-target resolution in verify, sample stdout normalization, and whether the transpile command carries `--target`.
- 2026-03-11: `S5-01` also adds pure command helpers to `tools/check/check_selfhost_cpp_diff.py` and locks the host `py2x-selfhost` command, selfhost direct/bridge commands, and auto-target resolution with unit tests. The diff lane now carries an explicit typed-boundary regression contract alongside build/prepare.
- 2026-03-11: `S5-01` also adds a generated selfhost-core residual bucket category map and union invariants in `test_prepare_selfhost_source.py`. If `serialization_export_seam` drifts into the expr/stmt/lookup parser residual buckets, the regression now fails fast as a selfhost guard.
- 2026-03-11: As part of the bridge lane, `tools/selfhost_transpile.py` also gained helperized env/cmd builders, and unit tests now lock both JSON passthrough and the `.py -> EAST JSON -> selfhost` flow through `main()`.
- 2026-03-11: The next `S5-01` bundle added `main()` regressions to `test_check_selfhost_stage2_cpp_diff.py`, fixing stage2 build failure, missing-binary under `--skip-build`, and build-to-diff flow with an existing stage2 binary. The stage2 diff lane is now guarded at the CLI orchestration level, not only through helper command tests.
- 2026-03-11: The next `S5-01` bundle added command/env helpers to `tools/selfhost_transpile.py` and fixed `.json` passthrough, `.py -> EAST JSON -> selfhost` bridging, `PYTHONPATH` injection, and `--target` propagation in `test_selfhost_transpile_tool.py`. The bridge-driver lane is now also covered by typed-boundary regressions.
- 2026-03-11: The next `S5-01` bundle also added command helpers to `tools/build_selfhost.py`, and `test_build_selfhost_tool.py` now fixes the stage1 transpile command, compile command, runtime-source resolution, and the `main()` transpile-to-compile flow. The stage1 build lane is now guarded as a typed-boundary selfhost regression too.
- 2026-03-11: `S5-01` is now complete. Unit tests lock the command/helper/main flows for `build_selfhost.py`, `build_selfhost_stage2.py`, `verify_selfhost_end_to_end.py`, `check_selfhost_cpp_diff.py`, `check_selfhost_stage2_cpp_diff.py`, and `selfhost_transpile.py`, and they also pin the generated selfhost-core residual bucket invariants.
- 2026-03-11: `S5-02` closes the plan by recording the end state in docs/TODO/archive: tracked compiler/toolchain object bridges are limited to the three `legacy_migration_adapter` sites in native `transpile_cli.cpp`, while generated selfhost-core `make_object` residuals remain confined to `serialization_export_seam` plus explicit parser-residual guards. User-facing `Any/object` boundaries remain out of scope for P2 and stay on the runtime side.
