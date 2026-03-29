# Backend Coverage Matrix

<a href="../../ja/language/backend-coverage-matrix.md">
  <img alt="日本語で読む" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

This page is the canonical publish target for bundle-based verification coverage.

## Surface Split

- [backend-parity-matrix.md](./backend-parity-matrix.md) remains the canonical support-claim surface.
- [backend-test-matrix.md](./backend-test-matrix.md) remains the canonical backend-owned suite-health surface.
- This page publishes the `feature x required_lane x backend` contract-coverage seed together with its bundle/rule ownership.

## Source Of Truth

- inventory: [backend_contract_coverage_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_contract_coverage_inventory.py)
- lane seed contract: [backend_contract_coverage_matrix_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_contract_coverage_matrix_contract.py)
- suite attachment contract: [backend_contract_coverage_suite_attachment_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_contract_coverage_suite_attachment_contract.py)
- unpublished fixture contract: [backend_contract_coverage_unpublished_fixture_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_contract_coverage_unpublished_fixture_contract.py)
- exporter: [export_backend_contract_coverage_docs.py](/workspace/Pytra/tools/gen/export_backend_contract_coverage_docs.py)

## Coverage Bundle Taxonomy

<!-- BEGIN BACKEND COVERAGE TAXONOMY TABLE -->

| bundle | suite_ids | harness_kinds | source_roots |
| --- | --- | --- | --- |
| frontend | unit_common, unit_ir | frontend_parse_diagnostic, east_document_compare, east3_document_compare | tools/unittest/common<br>tools/unittest/ir |
| emit | unit_backends, unit_common | backend_emit_compare | tools/unittest/backends<br>tools/unittest/common/test_py2x_smoke_common.py |
| runtime | transpile_artifact | runtime_parity_compare | work/transpile<br>tools/check/runtime_parity_check.py |
| import_package | unit_backends, unit_common | package_graph_transpile | tools/unittest/emit/relative_import_native_path_smoke_support.py<br>tools/unittest/emit/relative_import_jvm_package_smoke_support.py<br>tools/check/check_relative_import_backend_coverage.py |
| east2x | ir_fixture | ir_json_emit_compare | test/ir<br>tools/check/check_east2x_smoke.py |
| integration | integration | native_compile_run | test/integration |

<!-- END BACKEND COVERAGE TAXONOMY TABLE -->

## Live Suite Attachment

<!-- BEGIN BACKEND COVERAGE SUITE ATTACHMENT TABLE -->

| suite_id | status | bundle_kind | bundle_id_or_reason | notes |
| --- | --- | --- | --- | --- |
| unit_common | attached | frontend | frontend_unit_contract_bundle | Shared parser/EAST/EAST3 unit tests feed the frontend bundle directly. |
| unit_common | attached | emit | emit_backend_smoke_bundle | Common backend smoke helpers are part of the emit bundle surface. |
| unit_common | attached | import_package | import_package_bundle | Relative-import semantics tests back the shared import/package coverage lane. |
| unit_backends | attached | emit | emit_backend_smoke_bundle | Backend smoke suites are the canonical emit coverage surface. |
| unit_backends | attached | import_package | import_package_bundle | Backend-specific package and relative-import smoke feeds the import/package bundle. |
| unit_ir | attached | frontend | frontend_unit_contract_bundle | IR-facing frontend unit tests stay attached to the frontend bundle. |
| ir_fixture | attached | east2x | east2x_smoke_bundle | Backend-only EAST3 fixture smoke owns the east2x bundle. |
| integration | attached | integration | integration_gc_bundle | Native compile/run integration coverage currently comes from the GC integration suite. |
| transpile_artifact | attached | runtime | runtime_parity_bundle | Staged runtime parity artifacts remain the canonical runtime bundle surface. |
| unit_backends | unmapped_candidate | runtime | runtime_rule_owned_seed | Runtime cells are still seeded as explicit case/module follow-up rules, so backend unit-runtime checks stay visible as an unmapped candidate until the runtime bundle absorbs them. |
| unit_link | supporting_only | - | linker_validation_sidecar | Linker tests validate bundle plumbing indirectly and do not own direct coverage cells. |
| unit_selfhost | supporting_only | - | selfhost_preparation_sidecar | Selfhost preparation tests guard the pipeline but are not direct coverage-matrix inputs. |
| unit_tooling | supporting_only | - | tooling_checker_sidecar | Tooling/checker tests police inventories and contracts rather than owning coverage cells. |

<!-- END BACKEND COVERAGE SUITE ATTACHMENT TABLE -->

## Required-Lane Seed Ownership

<!-- BEGIN BACKEND COVERAGE OWNERSHIP TABLE -->

| category | parse | east | east3_lowering | emit | runtime |
| --- | --- | --- | --- | --- | --- |
| syntax | frontend_unit_contract_bundle | frontend_unit_contract_bundle | frontend_unit_contract_bundle | emit_backend_smoke_bundle | case_runtime_followup |
| builtin | frontend_unit_contract_bundle | frontend_unit_contract_bundle | frontend_unit_contract_bundle | emit_backend_smoke_bundle | case_runtime_followup |
| stdlib | frontend_unit_contract_bundle | frontend_unit_contract_bundle | frontend_unit_contract_bundle | emit_backend_smoke_bundle | module_runtime_strategy_followup |

<!-- END BACKEND COVERAGE OWNERSHIP TABLE -->

## Unpublished Multi-Backend Fixtures

<!-- BEGIN BACKEND COVERAGE UNPUBLISHED FIXTURE TABLE -->

| fixture | status | target_surface | proposed_feature_id | notes |
| --- | --- | --- | --- | --- |
| property_method_call | support_matrix_promotion_candidate | support_matrix | syntax.oop.property_method_call | Already exercised across every backend smoke/runtime lane and is the next candidate to promote into the representative support matrix. |
| list_bool_index | coverage_only_representative | coverage_matrix_only | - | Already exercised across every backend smoke/runtime lane, but should stay coverage-only because it primarily locks runtime regression behavior. |

<!-- END BACKEND COVERAGE UNPUBLISHED FIXTURE TABLE -->
