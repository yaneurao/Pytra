<a href="../../../ja/plans/archive/20260312-p6-backend-conformance-suite.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P6 Backend Conformance Suite

Last updated: 2026-03-12

Purpose:
- Build a shared conformance suite that validates the same feature fixtures across multiple backends instead of relying only on backend-local smoke tests.
- Tie parse / EAST / EAST3 lowering / emit / runtime parity to the same feature IDs so backend differences can be tracked consistently.
- Turn parity progress into a feature-level testing system rather than “some backend-specific smoke tests happen to pass.”

Background:
- Backend tests are still mostly target-local smoke suites, so it is hard to see how far a given feature actually works across multiple backends.
- Even if `P5` fixes the feature contract, drift will remain hard to catch early without shared fixtures and a shared harness.
- If `P6` does not consume the `conformance_handoff` manifest from `P5`, representative fixture/lane/backend order will drift between tasks.
- With C++-first implementation flow, unsupported or degraded behavior in other backends can still hide in the gaps between backend-local tests.
- A conformance basis is needed so a future feature × backend matrix can be driven from test evidence rather than hand-edited status notes.

Out of scope:
- Reaching full runtime parity in every backend immediately.
- Replacing all existing smoke tests at once.
- Redesigning the entire CI system.

Acceptance criteria:
- There is a defined plan for connecting feature fixtures to parse / lowering / emit / runtime parity lanes through a shared harness.
- Representative backend lanes (initially C++ / Rust / C# and similar) are selected.
- A strategy exists for comparing representative `pytra.std.*` runtime behavior across backends.
- There is a defined handoff from conformance results into support-matrix/docs/tooling layers.
- The `docs/en/` mirror matches the Japanese source plan.

## Child tasks

- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S1-01] Fix the mapping rule between feature IDs and fixture paths, and classify representative syntax / builtin / `pytra.std.*` cases.
- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S2-01] Design how parse / EAST / EAST3 lowering / emit / runtime parity lanes connect into a shared harness.
- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S2-02] Define a backend-selectable conformance runner, starting with representative lanes such as C++ / Rust / C#.
- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S3-01] Fix the runtime parity strategy for representative `pytra.std.*` modules such as `json`, `pathlib`, `enum`, and `argparse`.
- [x] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S4-01] Define how conformance summaries flow into support matrices, docs, and tooling.

## S1-01 Feature-To-Fixture Seed

- seed export:
  - manifest: `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()`
  - CLI/export seam: [export_backend_feature_contract_manifest.py](/workspace/Pytra/tools/gen/export_backend_feature_contract_manifest.py)
- mapping rule:
  - Each `feature_id` has exactly one representative fixture path.
  - Multiple features may share the same fixture, but the sharing must be explicit in `fixture_mapping[*].shared_fixture_feature_ids`.
  - Fixture category is fixed separately from the feature category via `fixture_scope` (`syntax_case` / `builtin_case` / `stdlib_case`).
- fixture bucket taxonomy:
  - `syntax_case`: `core`, `collections`, `control`, `oop`
  - `builtin_case`: `core`, `control`, `oop`, `signature`, `strings`, `typing`
  - `stdlib_case`: `stdlib`
- representative rule:
  - `stdlib.*` features must use `test/fixtures/stdlib/*.py` as their representative fixture.
  - `syntax.*` and `builtin.*` may share a fixture, but the sharing must be tracked through the manifest export.

## S2-01 Shared Harness Lane Contract

- source of truth:
  - lane contract: [backend_conformance_harness_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_harness_contract.py)
  - runner seed manifest: [backend_conformance_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_inventory.py)
  - CLI/export seam: [export_backend_conformance_seed_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_seed_manifest.py)
  - validation: [check_backend_conformance_harness_contract.py](/workspace/Pytra/tools/check/check_backend_conformance_harness_contract.py), [test_check_backend_conformance_harness_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_conformance_harness_contract.py)
- stage order:
  - `frontend`: `parse`
  - `ir`: `east`, `east3_lowering`
  - `backend`: `emit`
  - `runtime`: `runtime`
- backend selection rule:
  - `parse/east/east3_lowering` stay backend-agnostic lanes.
  - `emit/runtime` stay backend-selectable lanes, seeded by the representative backend order `cpp -> rs -> cs`.
- result contract:
  - `parse`: `parse_result` / `parser_success_or_frontend_diagnostic`
  - `east`: `east_document` / `east_document_or_frontend_diagnostic`
  - `east3_lowering`: `east3_document` / `east3_document_or_lowering_diagnostic`
  - `emit`: `module_artifact` / `artifact_or_fail_closed_backend_diagnostic`
  - `runtime`: `runtime_execution` / `stdout_stderr_exit_or_fail_closed_backend_diagnostic`
- fixture binding rule:
  - representative fixture class order is fixed to `syntax`, `builtin`, `pytra_std`
  - every lane shares the same representative fixture inventory rather than inventing lane-local vocabularies
- the runner seed manifest includes `lane_harness` and `fixture_lane_policy`, so `S2-02` can read CLI / compare-unit / runtime strategy from a fixed source

## S2-02 Backend-Selectable Runner Seed

- source of truth:
  - runner contract: [backend_conformance_runner_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_runner_contract.py)
  - CLI/export seam: [export_backend_conformance_runner_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_runner_manifest.py)
  - validation: [check_backend_conformance_runner_contract.py](/workspace/Pytra/tools/check/check_backend_conformance_runner_contract.py), [test_check_backend_conformance_runner_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_conformance_runner_contract.py)
- representative backend order:
  - `cpp -> rs -> cs`
- backend-selectable lane rule:
  - the runner only switches backends on `emit/runtime`
  - `parse/east/east3_lowering` stay in the shared harness contract from `S2-01`, so the runner does not introduce a second vocabulary
- entrypoint rule:
  - `emit`: `src/pytra-cli.py`
  - `runtime`: `tools/check/runtime_parity_check.py`
- smoke binding rule:
  - `cpp`: `tools/unittest/emit/cpp/test_py2cpp_features.py`
  - `rs`: `tools/unittest/emit/rs/test_py2rs_smoke.py`
  - `cs`: `tools/unittest/emit/cs/test_py2cs_smoke.py`
- handoff rule:
  - the runner manifest fixes backend order / selectable lanes / lane entrypoints / smoke bindings, and `S3-01` plus `S4-01` consume only this manifest for runner-facing policy

## S3-01 Stdlib Runtime Parity Strategy

- source of truth:
  - runtime strategy contract: [backend_conformance_runtime_parity_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_runtime_parity_contract.py)
  - CLI/export seam: [export_backend_conformance_runtime_parity_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_runtime_parity_manifest.py)
  - validation: [check_backend_conformance_runtime_parity_contract.py](/workspace/Pytra/tools/check/check_backend_conformance_runtime_parity_contract.py), [test_check_backend_conformance_runtime_parity_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_conformance_runtime_parity_contract.py)
- representative module order:
  - `json`, `pathlib`, `enum`, `argparse`, `math`, `re`
- runtime strategy rule:
  - every `fixture_class=pytra_std` runtime lane stays on `stdlib_module_runtime_case`
  - case root stays `fixture`, runner lane stays `runtime`, and the entrypoint stays `tools/check/runtime_parity_check.py`
  - compare unit stays `normalized_stdout_exitcode_artifact_digest` and backend order stays `cpp -> rs -> cs`
- fixture binding rule:
  - `json`: `test/fixtures/stdlib/json_extended.py`
  - `pathlib`: `test/fixtures/stdlib/pathlib_extended.py`
  - `enum`: `test/fixtures/stdlib/enum_extended.py`
  - `argparse`: `test/fixtures/stdlib/argparse_extended.py`
  - `math`: `test/fixtures/stdlib/pytra_std_import_math.py`
  - `re`: `test/fixtures/stdlib/re_extended.py`
- handoff rule:
  - `S4-01` reads the representative stdlib runtime modules and compare unit only from this manifest.

## S4-01 Conformance Summary Handoff

- source of truth:
  - summary handoff contract: [backend_conformance_summary_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_summary_handoff_contract.py)
  - CLI/export seam: [export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_summary_handoff_manifest.py)
  - validation: [check_backend_conformance_summary_handoff_contract.py](/workspace/Pytra/tools/check/check_backend_conformance_summary_handoff_contract.py), [test_check_backend_conformance_summary_handoff_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_conformance_summary_handoff_contract.py), [test_export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/unittest/tooling/test_export_backend_conformance_summary_handoff_manifest.py)
- destination order:
  - `support_matrix -> docs -> tooling`
- required manifest rule:
  - `feature_matrix_seed`: `backend_feature_contract_inventory.build_feature_contract_handoff_manifest`
  - `conformance_seed`: `backend_conformance_inventory.build_backend_conformance_seed_manifest`
  - `runner_seed`: `backend_conformance_runner_contract.build_backend_conformance_runner_manifest`
  - `stdlib_runtime_seed`: `backend_conformance_runtime_parity_contract.build_backend_conformance_runtime_parity_manifest`
- summary handoff rule:
  - `support_matrix` hands off `feature_id/category/representative_fixture/backend_order/support_state_order`
  - `docs` hands off `module_name/case_stem/compare_unit/representative_backends`
  - `tooling` hands off `lane_order/lane_harness/fixture_lane_policy/backend_order/selectable_lanes`
- downstream rule:
  - the downstream task / plan are fixed to `P7-BACKEND-PARITY-ROLLOUT-MATRIX-01` and `docs/ja/plans/p7-backend-parity-rollout-and-matrix.md`

## Decision log

- 2026-03-12: The conformance suite follows the `P5` feature contract, so it is placed at `P6` instead of trying to build a matrix before the contract exists.
- 2026-03-12: Existing smoke tests are not dropped immediately; shared conformance is introduced incrementally through representative lanes.
- 2026-03-12: `P6` consumes `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()["conformance_handoff"]` as the canonical representative fixture/lane/backend-order seed.
- 2026-03-12: `S1-01` adds `fixture_mapping` / `fixture_scope_order` / `fixture_bucket_order` to the manifest and fixes feature-to-fixture sharing through `build_feature_contract_handoff_manifest()` plus the CLI export seam.
- 2026-03-12: `S2-01` fixes the shared harness contract in `backend_conformance_harness_contract.py`, with backend-agnostic `parse/east/east3_lowering` lanes and backend-selectable `emit/runtime` lanes.
- 2026-03-12: `S2-01` also adds `backend_conformance_inventory.build_backend_conformance_seed_manifest()` and `export_backend_conformance_seed_manifest.py` so the runner seed `lane_harness` / `fixture_lane_policy` stays fixed.
- 2026-03-12: `S2-02` adds `backend_conformance_runner_contract.py` and `export_backend_conformance_runner_manifest.py`, fixing the representative backend order to `cpp -> rs -> cs`, the backend-selectable lanes to `emit/runtime`, and the per-backend smoke bindings in one runner manifest.
- 2026-03-12: `S3-01` adds `backend_conformance_runtime_parity_contract.py` and `export_backend_conformance_runtime_parity_manifest.py`, fixing the `pytra_std` runtime lane as `stdlib_module_runtime_case` across `json/pathlib/enum/argparse/math/re`.
- 2026-03-12: `S4-01` fixes `backend_conformance_summary_handoff_contract.py` and `export_backend_conformance_summary_handoff_manifest.py` as the canonical summary handoff pair into `P7-BACKEND-PARITY-ROLLOUT-MATRIX-01` for support matrix/docs/tooling.
