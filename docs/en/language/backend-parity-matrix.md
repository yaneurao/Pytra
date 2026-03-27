<a href="../../ja/language/backend-parity-matrix.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# Backend Parity Matrix

This page is the canonical publish target for feature × backend support-state reporting.

## Support Matrix vs Coverage Surface

- This page is the canonical support-matrix publish target, not the bundle-based coverage matrix itself.
- [backend-coverage-matrix.md](./backend-coverage-matrix.md) publishes the `feature x required_lane x backend` contract-coverage seed and ownership on the separate coverage surface, while `backend-test-matrix.md` remains the backend-owned suite-health publish target.
- The live bundle-based coverage surface is [backend-coverage-matrix.md](./backend-coverage-matrix.md).
- Coverage at 100% is defined as contract coverage for `feature x required_lane x backend`, not line or branch coverage.

## Canonical Source and Drill-Down

- Treat this page as the canonical source, and keep the C++ table as a drill-down at [./cpp/spec-support.md](./cpp/spec-support.md).
- The C++ support matrix only refines the cpp lane and does not redefine the cross-backend taxonomy.
- Update this page and the tooling contract first, then sync the C++ drill-down table.
- Cells are filled in representative -> secondary -> long_tail order.

## Current Implementation Phase

- The current matrix is at the `cell_seed_manifest` phase.
- The tooling manifest now carries row-level `backend_cells` seeds: `cpp` is emitted as `supported/build_run_smoke`, reviewed representative, secondary, and long-tail cells are promoted to `supported/transpile_smoke`, and the remaining backends stay on the conservative `not_started/not_started_placeholder` seed.
- The per-cell schema is fixed: required keys are `backend` / `support_state` / `evidence_kind`, and optional keys are `details` / `evidence_ref` / `diagnostic_kind`.
- The docs page now renders the seeded 2D table, but that table is still a seed-manifest view rather than a final support claim.
- The reviewed backend-by-backend states will be filled in follow-up bundles.

## Source Of Truth

- matrix contract: [backend_parity_matrix_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_matrix_contract.py)
- conformance summary handoff: [backend_conformance_summary_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_summary_handoff_contract.py)
- parity review contract: [backend_parity_review_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_review_contract.py)
- rollout tier contract: [backend_parity_rollout_tier_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_rollout_tier_contract.py)
- docs / release note / tooling handoff: [backend_parity_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_handoff_contract.py)

## Maintenance Rule

- Backend support status is published canonically through this page and the tooling manifests; release notes should only summarize the change and link back here.
- Unsupported lanes must be recorded as `fail_closed`, `not_started`, or `experimental`, with silent fallback forbidden.
- Representative / secondary / long-tail rollout order follows the rollout-tier contract.

## Tooling Export

- matrix manifest: [export_backend_parity_matrix_manifest.py](/workspace/Pytra/tools/export_backend_parity_matrix_manifest.py)
- conformance summary manifest: [export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/export_backend_conformance_summary_handoff_manifest.py)
- parity review manifest: [export_backend_parity_review_manifest.py](/workspace/Pytra/tools/export_backend_parity_review_manifest.py)
- handoff manifest: [export_backend_parity_handoff_manifest.py](/workspace/Pytra/tools/export_backend_parity_handoff_manifest.py)

## Representative Seed Matrix

- Cells are rendered as a plain Markdown table with emoji and compact status codes.
- At this stage `cpp` plus direct fixture-backed representative, secondary, and long-tail cells are reviewed seeds; the remaining backends are conservative placeholders.
- `🟩 BR`: supported / build_run_smoke
- `🟦 TS`: supported / transpile_smoke
- `⬜ NS`: not_started / not_started_placeholder
- `🟥 FC`: fail_closed / contract_guard or diagnostic_guard
- `🟨 EX`: experimental / preview_guard
- GitHub markdown rendering sanitizes `<style>` and inline style attributes, so this page uses a CSS-free table.

<!-- BEGIN BACKEND PARITY MATRIX TABLE -->

| feature_id | fixture | cpp | rs | cs | js | ts | go | java | swift | kt | rb | lua | scala | php | nim |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| syntax.assign.tuple_destructure | test/fixtures/core/tuple_assign.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.expr.lambda | test/fixtures/core/lambda_basic.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.expr.list_comprehension | test/fixtures/collections/comprehension.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.control.for_range | test/fixtures/control/for_range.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.control.try_raise | test/fixtures/control/try_raise.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| syntax.oop.virtual_dispatch | test/fixtures/oop/inheritance_virtual_dispatch_multilang.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.iter.range | test/fixtures/control/for_range.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.iter.enumerate | test/fixtures/strings/enumerate_basic.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.iter.zip | test/fixtures/signature/ok_generator_tuple_target.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.type.isinstance | test/fixtures/oop/is_instance.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| builtin.bit.invert_and_mask | test/fixtures/typing/bitwise_invert_basic.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.json.loads_dumps | test/fixtures/stdlib/json_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.pathlib.path_ops | test/fixtures/stdlib/pathlib_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.enum.enum_and_intflag | test/fixtures/stdlib/enum_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.argparse.parse_args | test/fixtures/stdlib/argparse_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.math.imported_symbols | test/fixtures/stdlib/pytra_std_import_math.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |
| stdlib.re.sub | test/fixtures/stdlib/re_extended.py | 🟩 `BR` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` | 🟦 `TS` |

<!-- END BACKEND PARITY MATRIX TABLE -->

## Current Relative-Import Coverage

- The current relative-import coverage baseline is published canonically through [relative_import_backend_coverage.py](/workspace/Pytra/src/toolchain/compiler/relative_import_backend_coverage.py) and [check_relative_import_backend_coverage.py](/workspace/Pytra/tools/check_relative_import_backend_coverage.py).
- Today `cpp` is `build_run_locked`, while `rs/cs/go/java/js/kotlin/lua/nim/php/ruby/scala/swift/ts` are `transpile_smoke_locked`. The evidence lane stays fixed as direct native-emitter function-body transpile smoke for `go/nim/swift`, as `package_project_transpile` for the JVM package bundle on `java/kotlin/scala`, and as the representative relative-import alias-rewrite lane for `lua/php/ruby`.
- This section is a verification-coverage handoff, not a support claim. Even after representative smoke is locked, non-C++ lanes do not become fully supported automatically.
- The historical handoff for ordinary relative imports lives in [20260312-p1-relative-import-longtail-support-implementation.md](../plans/archive/20260312-p1-relative-import-longtail-support-implementation.md): the bundle order stays fixed as `locked_js_ts_smoke_bundle -> native_path_bundle -> jvm_package_bundle`, with `java/kotlin/scala` archived as the JVM bundle and `lua/php/ruby` archived as the long-tail representative lane under the `transpile_smoke_locked` baseline.

## Current Relative-Wildcard-Import Coverage

- The final handoff for relative wildcard imports is published canonically through [relative_wildcard_import_native_rollout_contract.py](/workspace/Pytra/src/toolchain/compiler/relative_wildcard_import_native_rollout_contract.py) and [check_relative_wildcard_import_native_rollout_contract.py](/workspace/Pytra/tools/check_relative_wildcard_import_native_rollout_contract.py).
- `cpp` keeps the representative `from .helper import *` lane fixed at `build_run_locked + multi_file_build_run`, while non-C++ native backends lock `go/java/kotlin/lua/nim/php/ruby/scala/swift` at `transpile_smoke_locked + module_graph_bundle_transpile` on the representative module-graph bundle. The focused smoke lanes stay fixed as `go_relative_wildcard_import_rollout_smoke` / `java_relative_wildcard_import_rollout_smoke` / `kotlin_relative_wildcard_import_rollout_smoke` / `lua_relative_wildcard_import_rollout_smoke` / `nim_relative_wildcard_import_rollout_smoke` / `php_relative_wildcard_import_rollout_smoke` / `ruby_relative_wildcard_import_rollout_smoke` / `scala_relative_wildcard_import_rollout_smoke` / `swift_relative_wildcard_import_rollout_smoke`.
- The rollout bundle order is archived as `native_path_bundle -> jvm_package_bundle -> longtail_native_bundle`, while the single-file `load_east3_document(...)` direct lane and unresolved / duplicate / root-escape wildcard cases remain `backend_specific_fail_closed`.
- This section is also a verification-coverage handoff rather than a support claim, and it does not promote the out-of-scope `rs/cs/js/ts` backends to full support.
