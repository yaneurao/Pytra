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
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S2-01] Design how parse / EAST / EAST3 lowering / emit / runtime parity lanes connect into a shared harness.
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S2-02] Define a backend-selectable conformance runner, starting with representative lanes such as C++ / Rust / C#.
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S3-01] Fix the runtime parity strategy for representative `pytra.std.*` modules such as `json`, `pathlib`, `enum`, and `argparse`.
- [ ] [ID: P6-BACKEND-CONFORMANCE-SUITE-01-S4-01] Define how conformance summaries flow into support matrices, docs, and tooling.

## S1-01 Feature-To-Fixture Seed

- seed export:
  - manifest: `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()`
  - CLI/export seam: [export_backend_feature_contract_manifest.py](/workspace/Pytra/tools/export_backend_feature_contract_manifest.py)
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

## Decision log

- 2026-03-12: The conformance suite follows the `P5` feature contract, so it is placed at `P6` instead of trying to build a matrix before the contract exists.
- 2026-03-12: Existing smoke tests are not dropped immediately; shared conformance is introduced incrementally through representative lanes.
- 2026-03-12: `P6` consumes `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()["conformance_handoff"]` as the canonical representative fixture/lane/backend-order seed.
- 2026-03-12: `S1-01` adds `fixture_mapping` / `fixture_scope_order` / `fixture_bucket_order` to the manifest and fixes feature-to-fixture sharing through `build_feature_contract_handoff_manifest()` plus the CLI export seam.
