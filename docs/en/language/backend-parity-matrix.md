<a href="../../ja/language/backend-parity-matrix.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-2563EB?style=flat-square">
</a>

# Backend Parity Matrix

This page is the canonical publish target for feature × backend support-state reporting.

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
- Today `cpp` is `build_run_locked`, `rs/cs/go/js/nim/swift/ts` are `transpile_smoke_locked`, and the evidence lane for `go/nim/swift` is fixed as direct native-emitter function-body transpile smoke. `java/kotlin/lua/php/ruby/scala` remain `not_locked`.
- This section is a verification-coverage handoff, not a support claim. Even after representative smoke is locked, non-C++ lanes do not become fully supported automatically.
- The next rollout handoff lives in [p1-relative-import-jvm-package-bundle.md](../plans/p1-relative-import-jvm-package-bundle.md): the bundle order is fixed as `locked_js_ts_smoke_bundle -> native_path_bundle -> jvm_package_bundle`. `rs/cs/go/js/nim/swift/ts` stay fixed as the `transpile_smoke_locked` baseline, `java/kotlin/scala` move forward on the active `jvm_package_bundle_rollout`, and `lua/php/ruby` remain deferred behind `defer_until_jvm_package_bundle_complete`. The current non-C++ fail-closed lane stays explicitly `backend_specific_fail_closed`.
