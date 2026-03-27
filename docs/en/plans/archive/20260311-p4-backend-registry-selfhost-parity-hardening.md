<a href="../../../ja/plans/archive/20260311-p4-backend-registry-selfhost-parity-hardening.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P4: Canonicalize Backend Registry Metadata and Strengthen Selfhost Parity Gates

Last updated: 2026-03-11

Related TODO:
- `ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01` in `docs/ja/todo/index.md`

Background:
- The host-side `toolchain/compiler/backend_registry.py` and the selfhost/static `toolchain/compiler/backend_registry_static.py` still duplicate a large amount of backend spec, runtime-copy, emitter-wiring, and option-schema logic.
- That duplication was useful during bootstrap, but it now makes backend-surface updates drift-prone because one side can be updated without the other.
- Selfhost verification tools already exist: `build_selfhost.py`, `build_selfhost_stage2.py`, `verify_selfhost_end_to_end.py`, `check_multilang_selfhost_suite.py`, and related scripts. But operationally they still behave more like auxiliary reports than stable gates for compiler-internal changes.
- The current selfhost path also mixes direct routes, host-Python bridges, preview lanes, and known blocks, so it is often unclear which failures are expected and which are true regressions.
- Even if P2/P3 improve typed boundaries and compiler contracts, host-vs-selfhost divergence will reappear unless backend-registry ownership and selfhost parity gates are hardened too.

Goal:
- Establish one source of truth for backend spec, runtime-copy rules, layer option schema, and writer metadata, and reduce drift between host and selfhost/static registries.
- Turn selfhost parity from "useful information" into a practical non-regression gate for compiler-internal work.
- Classify stage1 / stage2 / direct-route / multilang selfhost failures so expected blocks and real regressions are easy to distinguish.

Related report:
- [P4 Selfhost Parity Readiness Report](./p4-selfhost-parity-readiness-report.md)

Scope:
- `toolchain/compiler/backend_registry.py`
- `toolchain/compiler/backend_registry_static.py`
- Shared backend spec / runtime-copy / option-schema / writer metadata
- `tools/build_selfhost.py` / `build_selfhost_stage2.py` / `verify_selfhost_end_to_end.py`
- `tools/check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` / `check_multilang_selfhost_suite.py`
- Selfhost parity docs / reports / guards

Out of scope:
- Typed-carrier design itself
- Fully removing the host-Python bridge
- Forcing every backend to succeed at multistage selfhost immediately
- Adding new backend language features
- A full runtime redesign

Dependencies:
- The boundary-ownership policy from `P2-COMPILER-TYPED-BOUNDARY-01` must be fixed
- The validator/diagnostic policy from `P3-COMPILER-CONTRACT-HARDENING-01` should exist at least for representative lanes

## Mandatory Rules

These are requirements, not recommendations.

1. Backend capability, runtime-copy, option-schema, and writer-rule metadata must have exactly one source of truth. Host/static manual duplication is not acceptable as the canonical design.
2. If host and selfhost/static registries behave differently, each difference must be identified as either intentional or drift. Hidden divergence is not allowed.
3. Selfhost parity failures must be categorized explicitly (`known_block`, `not_implemented`, `regression`, etc.). Vague preview text alone is not enough.
4. Representative stage1 / stage2 / direct-route / multilang selfhost gates must be runnable as part of routine compiler-internal regression checks.
5. Unsupported targets and unsupported modes should report the same diagnostic category in registry code and parity reports.
6. Any runtime-copy-list or backend-spec update must update both the shared source of truth and the parity/reporting side.
7. Selfhost parity does not need to mean "every backend passes everything," but it must always distinguish expected blocks from regressions.

Acceptance criteria:
- Backend spec / runtime-copy / option-schema / writer metadata is shared, and hand-written duplication between host/static registries is reduced.
- A drift guard or diff test exists to catch one-sided backend-registry updates.
- The selfhost parity suite reports representative stage1 / stage2 / direct e2e / multilang lanes with stable failure categories.
- For representative compiler changes, it is possible to tell which selfhost failures are known blocks and which are regressions.
- Docs / reports / archive make selfhost readiness and known blocks traceable.

Planned verification commands:
- `python3 tools/check_todo_priority.py`
- `python3 tools/build_selfhost.py`
- `python3 tools/build_selfhost_stage2.py --skip-stage1-build`
- `python3 tools/verify_selfhost_end_to_end.py --skip-build`
- `python3 tools/check_multilang_selfhost_suite.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/selfhost -p 'test_*selfhost*.py'`
- `git diff --check`

## Implementation Order

Keep the order fixed: inventory drift sources first, fix the canonical source of truth second, then strengthen the parity gates.

1. Inventory registry drift and parity blind spots
2. Fix canonical backend spec / runtime metadata
3. Share host/static registry ownership
4. Strengthen selfhost parity gates / reports / failure categories
5. Refresh docs / archive / migration notes

## Breakdown

- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01] Inventory duplicated surfaces across `backend_registry.py` and `backend_registry_static.py` (backend spec, runtime copy, writer rules, option schema, direct-route behavior), then classify each difference as intentional or drift-prone.
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02] Inventory current gates and blind spots across `build_selfhost`, stage2, direct e2e verification, and multilang selfhost tools, then fix the known-block vs regression classification policy in the decision log.
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01] Define the canonical source of truth for backend capability, runtime-copy rules, option schema, and writer metadata so both host and static registries can be derived from it.
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-02] Fix the boundaries where intentional differences are allowed (for example host-only lazy imports or selfhost-only direct routes) together with their diagnostic contracts.
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-01] Move host/static registries toward shared metadata, a generator, or equivalent adapters and retire avoidable hand-written duplication.
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S3-02] Add a registry-drift guard or diff test so one-sided backend-surface updates fail fast.
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-01] Reorganize representative stage1 / stage2 / direct e2e / multilang selfhost parity suites so they report a stable shared summary and failure taxonomy.
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S4-02] Align unsupported / preview / known-block / regression diagnostics between registry code and parity reports so expected failures are explicitly managed.
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-01] Refresh docs / plan reports / archive so backend readiness, known blocks, and gate execution flow remain traceable.
- [x] [ID: P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S5-02] Verify that representative internal changes are checked through equivalent contracts on both host and selfhost lanes, then fix reintroduction guards.

## Expected Deliverables

### Deliverables for S1

- An inventory of host/static registry drift candidates
- An inventory of selfhost parity blind spots

### Deliverables for S2

- A design for the backend-registry source of truth
- A contract for intentional differences and their diagnostics

### Deliverables for S3

- Shared metadata / generator / adapters
- A drift guard

### Deliverables for S4

- Unified selfhost parity categories
- Representative gates for stage1 / stage2 / direct-route / multilang lanes

### Deliverables for S5

- Docs/reports that track readiness and known blocks
- Reintroduction guards against host/selfhost divergence

Decision log:
- 2026-03-09: Added this P4 in response to the user request to keep improving the compiler internals after the type/carrier work.
- 2026-03-09: Fixed the scope of this P4 to backend-registry source-of-truth cleanup and selfhost non-regression gates, not new backend language features.
- 2026-03-09: Fixed the policy that host/selfhost differences are not banned outright, but must always be classified as intentional differences or drift and tracked through guards/reports.
- 2026-03-11: For `P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-01`, the intentional-difference inventory was fixed to three surfaces only: lazy import on the host side (`importlib`, `_TARGET_LOADERS`, `_SPEC_CACHE`), eager import on the static side (`_BACKEND_SPECS`, `_BACKEND_RUNTIME_SPECS`), and the host/static split in `build_resolved_backend_spec(..., suppress_emit_exceptions=True/False)`.
- 2026-03-11: Drift candidates were classified into four groups: duplicated runtime-copy helpers (`_runtime_*`, `_copy_runtime_file`, `_copy_php_runtime`), backend metadata tables (`target_lang`, `extension`, `lower/optimizer/emit`, `runtime_hook`, and C++ `default_options` / `option_schema`), emit-wrapper duplication (host `_load_*_spec` / `_make_unary_emit` versus static `_emit_*`), and default-writer injection (lazy `_load_callable(...)` versus direct `write_single_file_program`).
- 2026-03-11: The execution surface itself (`resolve_layer_options_*`, `lower_ir_*`, `optimize_ir_*`, `emit_module_*`, `emit_source_*`, `get_program_writer_*`, `apply_runtime_hook_*`) is already largely shared through `typed_boundary` helpers, so P4 should focus on unifying backend-metadata construction and runtime/report paths rather than reworking the execute path again.
- 2026-03-11: For `P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02`, the blind-spot inventory fixed that `build_selfhost.py` is a fail-fast stage-boundary preflight + transpile + compile gate with no category output, `build_selfhost_stage2.py` only special-cases `[not_implemented]` fallback reuse, and `verify_selfhost_end_to_end.py` collapses direct-route parity into plain `[FAIL ...]` buckets plus `failures=N` with no expected-block category.
- 2026-03-11: The same inventory fixed that `check_multilang_selfhost_stage1.py` expresses preview/toolchain-missing only through `stage1/mode/stage2/note` without a category column, while `check_multilang_selfhost_multistage.py` already has a `category` column but `check_multilang_selfhost_suite.py` does not unify that category surface with stage1 or direct-route lanes.
- 2026-03-11: The classification policy was fixed so selfhost parity reporting must normalize at least `pass`, `known_block`, `preview_only`, `toolchain_missing`, `not_implemented`, and `regression`; build-only gates may still return raw exit codes internally, but the report layer must map them into the same category set.
- 2026-03-11: Representative gate ownership was fixed as: `build_selfhost.py` for stage1 preflight build, `build_selfhost_stage2.py` and `check_selfhost_stage2_cpp_diff.py` for stage2 build/drift, `verify_selfhost_end_to_end.py` for direct-route parity, and `check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` / `check_multilang_selfhost_suite.py` for multilang readiness summary. S4 should unify summary format and failure categories along those boundaries.
- 2026-03-11: `P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S1-02` fixed the representative gate inventory to four lanes: `build_selfhost.py` as the C++ stage1 build gate, `build_selfhost_stage2.py` plus `check_selfhost_stage2_cpp_diff.py` as the C++ stage2/self-diff gate, `verify_selfhost_end_to_end.py` as the C++ direct-route stdout-parity gate, and `check_multilang_selfhost_stage1.py` / `check_multilang_selfhost_multistage.py` / `check_multilang_selfhost_suite.py` as the non-C++ parity-report gate.
- 2026-03-11: Blind spots were classified into four groups: `build_selfhost.py` / `build_selfhost_stage2.py` still rely on raw exit codes and fallback warnings instead of structured categories; `verify_selfhost_end_to_end.py` is biased toward stdout parity on a small fixed case list and lacks artifact-diff and failure-taxonomy output; `check_selfhost_cpp_diff.py` and direct-route lanes still externalize expected blocks through modes such as `allow-not-implemented`; and the multilang suite already has categories like `preview_only` / `toolchain_missing` / `self_retranspile_fail`, but its summary vocabulary is not aligned with the C++ lane yet.
- 2026-03-11: Future parity reports should use `pass`, `known_block`, `toolchain_missing`, and `regression` as top-level categories, while preserving detail categories such as `preview_only`, `not_implemented`, `unsupported_by_design`, `self_retranspile_fail`, `stage2_compile_fail`, `sample_transpile_fail`, and `direct_parity_fail`. Intentional blocks normalize to `known_block`; failures on previously passing representative lanes, unexpected fallback, artifact/stdout diffs, and missing outputs are treated as `regression`.
- 2026-03-11: As the first `P4-BACKEND-REGISTRY-SELFHOST-PARITY-01-S2-01` slice, `toolchain/compiler/backend_registry_metadata.py` was added to hold shared backend target order, `target_lang` / `extension` / `runtime_mode` / `program_writer_kind`, and the C++ `default_options` / `option_schema` rows.
- 2026-03-11: Host `_load_*_spec()` and static `_BACKEND_SPECS` now derive backend spec rows through `build_backend_spec_row(...)`. This removes duplicated metadata tables, but runtime-copy function bodies and emit/runtime callable wiring are still separate host/static implementations, so S2-01 remains open and those seams stay in scope for S3-01 sharing.
- 2026-03-11: The next `S2-01` slice expanded the shared metadata from plain rows to canonical `lower_ref` / `optimizer_ref` / `emit_ref` / `emit_kind` / `runtime_hook_key` / `program_writer_key` fields plus runtime file descriptors. The host registry now keeps lazy imports while deriving `_load_backend_spec(target)` from that canonical metadata, and the static registry now resolves the same descriptors through `_build_backend_spec(target)` and `_STATIC_CALLABLES`. The remaining intentional differences are eager-vs-lazy import/evaluation and `suppress_emit_exceptions=True/False`.
- 2026-03-11: `S2-01` is now considered complete. The canonical source of truth lives in `backend_registry_metadata.py`, and both host/static registries derive backend target order, spec metadata rows, lower/optimizer/emit refs, runtime-hook descriptors, and program-writer refs from it. The next step is to pin the intentional-difference and diagnostics contract in `S2-02`.
- 2026-03-11: As the first `S2-02` contract, the only intentional host/static differences are now fixed to lazy import via `importlib + _SPEC_CACHE`, eager resolve via `_STATIC_CALLABLES + _BACKEND_RUNTIME_SPECS`, and `suppress_emit_exceptions=True/False`. Unsupported targets must still report the same `RuntimeError("unsupported target: ...")` on both lanes, while runtime-hook / program-writer / emit-ref mismatches are allowed to surface as canonical metadata key/ref resolution errors.
- 2026-03-11: The next `S2-02` slice also fixed the diagnostics contract itself: host-side backend symbol-ref failures are now normalized to the same `RuntimeError("unsupported backend symbol ref: ...")` used by the static lane, and runtime-hook keys, program-writer keys, and backend symbol refs must all surface the same canonical error text across both lanes.
- 2026-03-11: As part of the `S2-02` diagnostics contract, tests now pin canonical metadata failures for unknown `runtime_hook_key` / `program_writer_key` to `RuntimeError("unsupported ... key: ...")`. Registry layers are expected to expose those metadata errors directly instead of hiding them behind fallback behavior.
- 2026-03-11: Another `S2-02` slice also pins kind-level diagnostics: if metadata descriptors are corrupted so the resolved `runtime_hook kind` or `emit kind` becomes invalid, both host and static lanes must still raise the same `RuntimeError("unsupported ... kind: ...")`. These diagnostics are treated as shared contract outside the intentional eager-vs-lazy difference.
- 2026-03-11: `S2-02` is now considered complete. The only intentional differences are lazy import vs eager resolve and `suppress_emit_exceptions`, while unsupported target / metadata key / backend symbol ref / kind-level diagnostics are all locked to the same canonical error text across host and static lanes.
- 2026-03-11: As the first `S3-01` slice, the fully duplicated runtime-copy helpers, php-runtime copy helpers, default output-path helper, and no-op runtime hook were moved into `toolchain/compiler/backend_registry_shared.py`. The remaining intentional difference is the lazy-vs-eager callable resolution path; pure helper duplication should now collapse into shared modules.
- 2026-03-11: The next `S3-01` slice also moved the remaining duplicated `identity_ir` and `empty_emit` helpers into `backend_registry_shared.py`. Pure typed-boundary adapters are no longer treated as intentional differences, so only the registry-layer lazy/eager resolve path remains distinct.
- 2026-03-11: Another `S3-01` slice moved the shared parts of `_load_backend_spec` / `_build_backend_spec` and `_normalize_backend_runtime_spec` into `backend_registry_shared.py` as `build_runtime_bound_backend_spec` and `normalize_runtime_backend_spec`. Host/static differences are now reduced to resolver choice plus `suppress_emit_exceptions` and default-writer injection.
- 2026-03-11: The next `S3-01` cluster moved the duplicated emit-wrapper logic (`cpp/java/unary`) behind `backend_registry_shared.py` helpers (`build_cpp_emit`, `build_java_emit`, `build_unary_emit`, `build_emit_from_target`). After this cut, the remaining host/static difference on the emit side is only the callable resolver itself.
- 2026-03-11: The following `S3-01` cluster also moved the `runtime_hook key -> descriptor -> copy/js/php hook` wiring behind `backend_registry_shared.py::build_runtime_hook_from_key`. Host/static now only keep the js-shim implementation itself, while runtime file-copy descriptor resolution is centralized.
- 2026-03-11: The next `S3-01` cluster also moved the typed execution wrappers for `default_output_path`, `resolve_layer_options_*`, `lower/optimize/emit`, program-artifact assembly, program-writer lookup, and runtime-hook application behind `backend_registry_shared.py::*_with_backend_spec` helpers. The remaining large host/static differences are now mostly limited to eager-vs-lazy callable resolution, spec-cache shape, default-writer injection, and `suppress_emit_exceptions`.
- 2026-03-11: The following `S3-01` cluster removed unused direct `typed_boundary` execution imports and dead adapters from the host/static registries, and updated the contract test to treat shared execution wrappers as the canonical surface. Direct `typed_boundary` dependencies in registry code are now intended to stay limited to carrier types, `coerce_backend_spec`, and `export_resolved_backend_spec_any`.
- 2026-03-11: `S3-01` is now considered complete. The remaining host/static differences are limited to the intentional eager-vs-lazy callable-resolution path, `_SPEC_CACHE` vs `_BACKEND_RUNTIME_SPECS` cache shape, default-writer injection, and `suppress_emit_exceptions`; handwritten duplication for runtime copy, emit wrappers, backend-spec assembly, and typed execution wrappers has been pushed behind shared helpers.
- 2026-03-11: `S3-02` added `test_backend_registry_drift_guard.py`, which locks the host/static registry public function signatures, `backend_registry_shared` imports, `typed_boundary` imports, and the intentional private helper/state differences through AST snapshots. One-sided helper/import/cache updates now fail fast in unit tests.
- 2026-03-11: `S3-02` is considered complete. Existing metadata/contract tests cover canonical backend-spec parity, while the new drift guard covers source-topology parity so representative registry-surface drift is caught before parity suites run.
- 2026-03-11: As the first `S4-01` cluster, `tools/selfhost_parity_summary.py` was added and `check_multilang_selfhost_suite.py` now routes stage1/multistage summary rows through shared top-level/detail category helpers (`pass / known_block / toolchain_missing / regression`). The vocabulary is fixed on the multilang summary lane first, then expanded to direct/stage2 lanes in later clusters.
- 2026-03-11: The next `S4-01` cluster added direct parity summary helpers to `verify_selfhost_end_to_end.py`, normalizing `[not_implemented]` selfhost transpile failures to `known_block/not_implemented` and stdout mismatches to `regression/direct_parity_fail`. `check_selfhost_stage2_sample_parity.py` calls the same tool, so this cluster also moves the direct/stage2 lane onto the shared summary vocabulary.
- 2026-03-11: The same `S4-01` work also gave `check_selfhost_stage2_sample_parity.py` its own `stage2` summary lane, normalizing build failures, missing binaries, and verify exits into `stage2_build_fail`, `missing_output`, and `direct_parity_fail`. Direct e2e now also emits an explicit `subject=all category=pass` row on all-pass runs, so multilang, direct, and stage2-wrapper summaries share the same renderer surface.
- 2026-03-11: The following `S4-01` cluster added `stage2-diff` summary helpers to `check_selfhost_cpp_diff.py`, normalizing `allow-not-implemented` skips to `known_block/not_implemented`, mismatches listed in the expected-diff file to `known_block`, and unexpected C++ artifact diffs to `regression/stage2_diff_fail`. This puts the representative multilang, direct, and stage2-diff parity suites on the same top-level category vocabulary.
- 2026-03-11: `S4-01` is now considered complete. `check_multilang_selfhost_suite.py`, `verify_selfhost_end_to_end.py`, `check_selfhost_stage2_sample_parity.py`, `check_selfhost_cpp_diff.py`, and `check_selfhost_stage2_cpp_diff.py` now share the same summary helper and top-level category vocabulary, including explicit all-pass aggregation. The remaining work moves to `S4-02`, which aligns registry-side diagnostics with the parity-report categories.
- 2026-03-11: `build_stage2_summary_row()` was then added to `tools/selfhost_parity_summary.py` so `check_selfhost_stage2_sample_parity.py` also reports build / missing-binary / verify-fail cases through the shared `stage2` summary vocabulary. This gives the representative stage2 wrapper lane a stable summary block as well.
- 2026-03-11: The next `S4-01` cluster removed the local `_build/_print` summary wrappers from `check_selfhost_cpp_diff.py` and switched the stage2-diff lane to call `build_stage2_diff_summary_row()` and `render_summary_block()` directly. Summary mapping for that lane now lives only in the shared helper layer.
- 2026-03-11: The following `S4-01` cluster added `print_summary_block()` to `tools/selfhost_parity_summary.py` and moved direct e2e, stage2 sample, stage2 diff, and multilang-suite summary emission onto that shared printer. Representative parity lanes now share the render path as well as the summary vocabulary.
- 2026-03-11: As the first `S4-02` slice, `tools/selfhost_parity_summary.py` gained `classify_known_block_detail()`, and direct e2e / stage2-diff lanes now normalize `[unsupported_by_design]` plus registry-side `unsupported target:` diagnostics to `known_block/unsupported_by_design`. Expected unsupported failures can now be tracked through the shared parity vocabulary instead of falling through as regressions.
- 2026-03-11: The next `S4-02` cluster added `toolchain/compiler/backend_registry_diagnostics.py` to unify top-level category normalization and diagnostic-text inference across registry and parity lanes. `unsupported target/profile/non-cpp build target` is now classified as `unsupported_by_design -> known_block`, while `unsupported backend symbol ref/runtime hook key/emit kind` is classified as `regression`, and registry-side error text was moved onto the same message builders.
- 2026-03-11: The following `S4-02` cluster replaced the multistage selfhost raw category `runner_not_defined` with `unsupported_by_design`, so expected unsupported lanes are separated from regressions at the report-source level. `check_multilang_selfhost_suite.py` now locks that detail to `known_block` in unit tests.
- 2026-03-11: The next `S4-02` cluster aligned the parity-side known-block detail check with `backend_registry_diagnostics.py` by reusing `KNOWN_BLOCK_DETAIL_CATEGORIES` and `infer_diagnostic_detail_from_text()`. As a result, `preview backend ...` now normalizes to `known_block/preview_only` on direct e2e and stage2-diff lanes as well, and `classify_registry_diagnostic()` now preserves `preview_only` and `toolchain_missing` instead of collapsing them into `regression`.
- 2026-03-11: `S4-02` is now considered complete. Registry-side diagnostic helpers, direct e2e / stage2-diff parity summaries, and multilang selfhost summaries now treat `unsupported_by_design`, `preview_only`, `toolchain_missing`, and `regression` through the same shared vocabulary, so representative expected failures are tracked under one category contract.
- 2026-03-11: As the first `S5-01` slice, `docs/ja/plans/p4-selfhost-parity-readiness-report.md` was added to collect the representative gate order, shared category contract, and current known-block reading in one place. The P4 plan now links straight to that report, so gate procedures no longer depend on scanning the full decision log.
- 2026-03-11: In the next `S5-01` slice, the docs index and `plans/README.md` gained explicit readiness-report guidance. Reports are treated as supporting documents hanging off the main plan, and the P4 readiness entry can now be reached directly from `docs/ja/index.md`.
- 2026-03-11: In the final `S5-01` slice, the readiness report also gained an archive handoff section. It now states that the plan, report, and TODO archive updates must be tied to the same completion date, and it points to `archive/index.md` plus the dated archive note as the canonical completion trail.
- 2026-03-11: As the first `S5-02` slice, `test_backend_registry_selfhost_contract_guard.py` was added to lock representative shared-diagnostic cases (`unsupported_by_design`, `preview_only`, `toolchain_missing`) across the host registry plus direct e2e, stage2 diff, and multilang summary lanes in one guard.
- 2026-03-11: The next `S5-02` slice added `tools/check_selfhost_contract_reentry_guard.py`, bundling the representative host lane (`test_py2x_entrypoints_contract.py`) and selfhost lanes (`test_prepare_selfhost_source.py`, `test_selfhost_build_verify_tools.py`, `test_check_selfhost_cpp_diff.py`, `test_check_selfhost_stage2_cpp_diff.py`) behind one command. `run_local_ci.py` and the readiness report now point at the same command.
- 2026-03-11: The next `S5-02` slice folded `test_backend_registry_selfhost_contract_guard.py` into the host side of `check_selfhost_contract_reentry_guard.py`, and expanded coverage from known-block cases to representative regression cases (`unsupported backend symbol ref` / `unsupported runtime hook key`) across host registry, direct e2e, stage2 diff, and multilang summary lanes.
- 2026-03-11: The next `S5-02` slice extended representative regression coverage further to `unsupported program writer key` / `unsupported emit kind` / `unsupported runtime hook kind`. Shared registry diagnostic message-builder changes now trip the same host/selfhost guard on regression lanes as well as known-block lanes.
- 2026-03-11: The same `S5-02` line also expanded `unsupported_by_design` coverage beyond plain `unsupported target` to include `unsupported target profile` and `unsupported non-cpp build target`. Host-side message builders and selfhost parity-note normalization now fail together for profile/build-target drift as well.
- 2026-03-11: The next `S5-02` slice added `build_steps()` to `tools/run_local_ci.py` and `test_run_local_ci.py` to lock that `check_selfhost_contract_reentry_guard.py` remains immediately after the multilang suite and before the strict selfhost build/diff gates. The representative guard tool now fails fast if it drops out of the local-CI route.
- 2026-03-11: A follow-up `S5-01` slice re-ran the representative gates and fixed the `direct_e2e=pass` / `stage2_diff=pass` plus multilang `stage1_transpile_fail` snapshot into both the readiness report and `todo/archive/20260311.md`, so the current representative status is traceable from both the docs path and the archive path.
