<a href="../../ja/language/backend-parity-matrix.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Backend Parity Matrix

This page is the canonical publish target for feature × backend support-state reporting.

## Current Implementation Phase

- The current matrix is still at the `row_seed_scaffold` phase.
- Representative feature rows are already published, but the actual `feature × backend` cells are not populated yet.
- The per-cell schema is already fixed: required keys are `backend` / `support_state` / `evidence_kind`, and optional keys are `details` / `evidence_ref` / `diagnostic_kind`.
- The actual `feature × backend` cells are still not populated and will be filled row by row in the next matrix-fill task.

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

## Current Relative-Import Coverage

- The current relative-import coverage baseline is published canonically through [relative_import_backend_coverage.py](/workspace/Pytra/src/toolchain/compiler/relative_import_backend_coverage.py) and [check_relative_import_backend_coverage.py](/workspace/Pytra/tools/check_relative_import_backend_coverage.py).
- Today `cpp` is `build_run_locked`, while `rs/cs/go/java/js/kotlin/lua/nim/php/ruby/scala/swift/ts` are `transpile_smoke_locked`. The evidence lane stays fixed as direct native-emitter function-body transpile smoke for `go/nim/swift`, as `package_project_transpile` for the JVM package bundle on `java/kotlin/scala`, and as the representative relative-import alias-rewrite lane for `lua/php/ruby`.
- This section is a verification-coverage handoff, not a support claim. Even after representative smoke is locked, non-C++ lanes do not become fully supported automatically.
- The next rollout handoff lives in [20260312-p1-relative-import-longtail-support-implementation.md](../plans/archive/20260312-p1-relative-import-longtail-support-implementation.md): the historical bundle order remains fixed as `locked_js_ts_smoke_bundle -> native_path_bundle -> jvm_package_bundle`. `java/kotlin/scala` stay in the archived JVM bundle / `transpile_smoke_locked` baseline, and `longtail_relative_import_support_rollout` is now closed at `bundle_state=locked_representative_smoke`. `lua/php/ruby` are the representative `transpile_smoke_locked` lanes with `native_emitter_function_body_transpile` evidence, the backend-local focused smoke lanes stay fixed as `lua_relative_import_support_rollout_smoke` / `php_relative_import_support_rollout_smoke` / `ruby_relative_import_support_rollout_smoke`, and the remaining rollout backends / next rollout bundle / next verification lane / follow-up rollout bundle / follow-up verification lane are all `none`. Wildcard relative import remains `backend_specific_fail_closed`.
