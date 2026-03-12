# Backend Parity Matrix

<a href="../../en/language/backend-parity-matrix.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

このページは、feature × backend の support state を公開する canonical publish target です。

## Source Of Truth

- matrix contract: [backend_parity_matrix_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_matrix_contract.py)
- conformance summary handoff: [backend_conformance_summary_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_summary_handoff_contract.py)
- parity review contract: [backend_parity_review_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_review_contract.py)
- rollout tier contract: [backend_parity_rollout_tier_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_rollout_tier_contract.py)
- docs / release note / tooling handoff: [backend_parity_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_handoff_contract.py)

## Maintenance Rule

- backend support status はこのページと tooling manifest を正本とし、release note 側には要約とリンクだけを載せます。
- unsupported lane は `fail_closed` / `not_started` / `experimental` のいずれかで記録し、silent fallback は認めません。
- representative / secondary / long-tail の rollout tier は rollout tier contract に従います。

## Tooling Export

- matrix manifest: [export_backend_parity_matrix_manifest.py](/workspace/Pytra/tools/export_backend_parity_matrix_manifest.py)
- conformance summary manifest: [export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/export_backend_conformance_summary_handoff_manifest.py)
- parity review manifest: [export_backend_parity_review_manifest.py](/workspace/Pytra/tools/export_backend_parity_review_manifest.py)
- handoff manifest: [export_backend_parity_handoff_manifest.py](/workspace/Pytra/tools/export_backend_parity_handoff_manifest.py)

## Current Relative-Import Coverage

- relative import の current coverage baseline は [relative_import_backend_coverage.py](/workspace/Pytra/src/toolchain/compiler/relative_import_backend_coverage.py) と [check_relative_import_backend_coverage.py](/workspace/Pytra/tools/check_relative_import_backend_coverage.py) を正本にする。
- 現時点で `build_run_locked` なのは `cpp`、`transpile_smoke_locked` なのは `rs/cs/go/java/js/kotlin/lua/nim/php/scala/swift/ts` です。`go/nim/swift` は direct native emitter の function-body transpile smoke、`java/kotlin/scala` は JVM package bundle の `package_project_transpile`、`lua/php` は representative relative import alias rewrite の `native_emitter_function_body_transpile` を証跡 lane に固定しています。`ruby` は support claim としてはまだ未主張で、archived long-tail fail-closed bundle による `fail_closed_locked` と `backend_native_fail_closed` の baseline を維持しています。
- この欄は support claim ではなく verification coverage の handoff であり、non-C++ lane は representative smoke が lock されても full support 扱いにはしない。
- next rollout handoff は [p1-relative-import-longtail-support.md](../plans/p1-relative-import-longtail-support.md) を参照し、historical bundle order は `locked_js_ts_smoke_bundle -> native_path_bundle -> jvm_package_bundle` のまま固定する。`java/kotlin/scala` は archived JVM bundle として `transpile_smoke_locked` baseline に移り、active `longtail_relative_import_support_rollout` は current bundle を `mixed_rollout_locked + mixed_backend_evidence` として扱う。`lua/php` は `native_emitter_function_body_transpile` を current evidence lane にした `transpile_smoke_locked` representative lane、`ruby` は `backend_specific_fail_closed` / `backend_native_fail_closed` の residual fail-closed lane として残る。backend-local focused smoke lane は `lua_relative_import_support_rollout_smoke` / `php_relative_import_support_rollout_smoke` / `ruby_relative_import_support_rollout_smoke` に固定し、current bundle の smoke-locked backend は `lua/php`、remaining rollout backends は `ruby`、followup rollout bundle / followup verification lane はどちらも `none` とする。
