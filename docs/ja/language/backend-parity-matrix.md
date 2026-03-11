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
- 現時点で `build_run_locked` なのは `cpp`、`transpile_smoke_locked` なのは `rs/cs` で、`go/java/js/kotlin/lua/nim/php/ruby/scala/swift/ts` は `not_locked` として扱う。
- この欄は support claim ではなく verification coverage の handoff であり、non-C++ lane は representative smoke が lock されても full support 扱いにはしない。
- next rollout handoff は [p1-relative-import-firstwave-smoke.md](../plans/p1-relative-import-firstwave-smoke.md) を参照し、`rs/cs` を `transpile_smoke_locked` baseline に固定したうえで、残りの non-C++ lane は `backend_specific_fail_closed` を維持しながら `second_wave_rollout_planning` へ進む。
