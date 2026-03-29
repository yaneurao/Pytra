<a href="../../../ja/plans/archive/20260312-p7-backend-parity-rollout-and-matrix.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P7 Backend Parity Rollout And Matrix

Last updated: 2026-03-12

Purpose:
- Make backend parity visible as feature × backend status so the project can continuously track which backends are `supported`, `fail_closed`, or `not_started`.
- Build parity requirements into new-feature merge policy so C++-only completion is no longer treated as feature completion.
- Institutionalize the support matrix and rollout order in docs, tooling, and review operations.

Background:
- Even with `P5` contract work and `P6` conformance groundwork, C++-first drift will return unless the workflow itself changes.
- If `P7` does not consume the `support_matrix_handoff` and `support_state_order` seed from `P5`, the matrix drifts into a separate feature/state vocabulary.
- Current support information is spread across backend-specific pages and notes, so feature-level cross-backend comparison is weak.
- There is not yet a formal parity check in review/merge flow, so it is easy to land changes where C++ works and other backends remain undefined.
- The final step is therefore to fix the matrix, rollout order, acceptance conditions, and documentation handoff as ongoing project policy.

Out of scope:
- Making every backend feature-complete at the same time.
- Backend-local optimization or performance tuning.
- A full rewrite of the current docs structure.

Acceptance criteria:
- The source of truth and publication path for a feature × backend support matrix are defined.
- Rollout tiers and order are fixed (for example: representative backends first, then secondary tiers, then long-tail backends).
- Review / merge checklist policy includes parity requirements and fail-closed expectations for unsupported lanes.
- Docs, support pages, and tooling have a defined handoff path from the matrix.
- The `docs/en/` mirror matches the Japanese source plan.

## Child tasks

- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S1-01] Decide the source of truth and publication path for the feature × backend support matrix.
- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-01] Fix rollout tiers and ordering from representative backends to secondary and long-tail backends.
- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-02] Define the parity review checklist and fail-closed requirement for new feature merges.
- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S3-01] Define how the support matrix flows into docs, release notes, and tooling.
- [x] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S4-01] Fix the archive / operations rules for maintaining rollout policy and the support matrix.

## Decision log

- 2026-03-12: The operationalization of parity is placed at `P7` because it should follow the contract and conformance layers instead of pretending to define them.
- 2026-03-12: Backend parity means “make support states visible and keep unsupported lanes fail-closed,” not “implement every backend simultaneously.”
- 2026-03-12: `P7` consumes `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()["support_matrix_handoff"]` and `support_state_order` as the canonical matrix seed.

## S1-01 Matrix Source Of Truth And Publish Path

- source of truth:
  - matrix contract: [backend_parity_matrix_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_matrix_contract.py)
  - row/state seed: [backend_feature_contract_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_feature_contract_inventory.py) via `iter_representative_support_matrix_handoff()` and `SUPPORT_STATE_ORDER`
  - conformance summary seed contract: [backend_conformance_summary_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_conformance_summary_handoff_contract.py)
  - CLI/export seam: [export_backend_parity_matrix_manifest.py](/workspace/Pytra/tools/gen/export_backend_parity_matrix_manifest.py), [export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/gen/export_backend_conformance_summary_handoff_manifest.py)
  - validation: [check_backend_parity_matrix_contract.py](/workspace/Pytra/tools/check/check_backend_parity_matrix_contract.py), [test_check_backend_parity_matrix_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_parity_matrix_contract.py), [check_backend_conformance_summary_handoff_contract.py](/workspace/Pytra/tools/check/check_backend_conformance_summary_handoff_contract.py), [test_check_backend_conformance_summary_handoff_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_conformance_summary_handoff_contract.py), [test_export_backend_conformance_summary_handoff_manifest.py](/workspace/Pytra/tools/unittest/tooling/test_export_backend_conformance_summary_handoff_manifest.py)
- source manifest rule:
  - `feature_contract_seed`: `backend_feature_contract_inventory.build_feature_contract_handoff_manifest`
  - `conformance_summary_seed`: `backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest`
  - the canonical matrix destination is fixed to `support_matrix`.
- row/source rule:
  - row seed comes directly from `iter_representative_support_matrix_handoff()` and keeps `feature_id/category/representative_fixture/backend_order/support_state_order` as the row keys.
  - summary seed is reused from the P6 representative conformance summary handoff, and the matrix only reads the allowlisted `representative_summary_entries` keys.
- publish path rule:
  - Japanese docs publish path: `docs/ja/language/backend-parity-matrix.md`
  - English docs publish path: `docs/en/language/backend-parity-matrix.md`
  - tooling publish seam: `tools/gen/export_backend_parity_matrix_manifest.py`
  - the conformance summary handoff itself keeps the fixed publish target order `support_matrix -> docs -> tooling`
- downstream rule:
  - downstream task / plan stay fixed to `P7-BACKEND-PARITY-ROLLOUT-MATRIX-01` and `docs/ja/plans/p7-backend-parity-rollout-and-matrix.md`.

- 2026-03-12: `S1-01` fixes `backend_parity_matrix_contract.py` as the canonical matrix contract, with row/state seed from `backend_feature_contract_inventory.iter_representative_support_matrix_handoff()` and summary seed from `backend_conformance_summary_handoff_contract.build_backend_conformance_summary_handoff_manifest()`.

## S2-01 Rollout Tier And Ordering

- source of truth:
  - rollout tier contract: [backend_parity_rollout_tier_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_rollout_tier_contract.py)
  - validation: [check_backend_parity_rollout_tier_contract.py](/workspace/Pytra/tools/check/check_backend_parity_rollout_tier_contract.py), [test_check_backend_parity_rollout_tier_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_parity_rollout_tier_contract.py)
  - export seam: [export_backend_parity_rollout_tier_manifest.py](/workspace/Pytra/tools/gen/export_backend_parity_rollout_tier_manifest.py), [test_export_backend_parity_rollout_tier_manifest.py](/workspace/Pytra/tools/unittest/tooling/test_export_backend_parity_rollout_tier_manifest.py)
- tier rule:
  - `representative`: `cpp -> rs -> cs`
  - `secondary`: `go -> java -> kt -> scala -> swift -> nim`
  - `long_tail`: `js -> ts -> lua -> rb -> php`
- ordering rule:
  - the concatenated tier order must match `backend_feature_contract_inventory.SUPPORT_MATRIX_BACKEND_ORDER`
  - backends must not overlap across tiers
- downstream rule:
  - downstream task / plan stay fixed to `P7-BACKEND-PARITY-ROLLOUT-MATRIX-01` and `docs/ja/plans/p7-backend-parity-rollout-and-matrix.md`

- 2026-03-12: `S2-01` fixes the rollout tiers to `representative -> secondary -> long_tail` and locks the concatenated order against the support matrix backend order via contract/tooling.

## S2-02 Parity Review Checklist And Fail-Closed Requirement

- source of truth:
  - review checklist contract: [backend_parity_review_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_review_contract.py)
  - validation: [check_backend_parity_review_contract.py](/workspace/Pytra/tools/check/check_backend_parity_review_contract.py), [test_check_backend_parity_review_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_parity_review_contract.py)
  - export seam: [export_backend_parity_review_manifest.py](/workspace/Pytra/tools/gen/export_backend_parity_review_manifest.py), [test_export_backend_parity_review_manifest.py](/workspace/Pytra/tools/unittest/tooling/test_export_backend_parity_review_manifest.py)
- checklist rule:
  - review checklist order is fixed to `feature_inventory -> matrix_state_recorded -> representative_tier_recorded -> later_tier_state_recorded -> unsupported_lanes_fail_closed -> docs_mirror`.
  - `feature_inventory` and `unsupported_lanes_fail_closed` reuse `backend_feature_contract_inventory.NEW_FEATURE_ACCEPTANCE_RULES`.
  - `representative_tier_recorded` and `later_tier_state_recorded` reuse the tier order from `backend_parity_rollout_tier_contract`.
- fail-closed rule:
  - any lane that is not `supported` must stay in `fail_closed / not_started / experimental`, and silent fallback labels `object_fallback / string_fallback / comment_stub_fallback / empty_output_fallback` remain forbidden.
  - phase rules stay aligned to `backend_feature_contract_inventory.FAIL_CLOSED_PHASE_RULES` for `parse_and_ir / emit_and_runtime / preview_rollout`.

- 2026-03-12: `S2-02` fixes the parity review checklist order and adds a contract that unsupported lanes must remain `fail_closed/not_started/experimental` with silent fallbacks forbidden.

## S3-01 Docs / Release Note / Tooling Handoff

- source of truth:
  - handoff contract: [backend_parity_handoff_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_handoff_contract.py)
  - validation: [check_backend_parity_handoff_contract.py](/workspace/Pytra/tools/check/check_backend_parity_handoff_contract.py), [test_check_backend_parity_handoff_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_parity_handoff_contract.py)
  - export seam: [export_backend_parity_handoff_manifest.py](/workspace/Pytra/tools/gen/export_backend_parity_handoff_manifest.py), [test_export_backend_parity_handoff_manifest.py](/workspace/Pytra/tools/unittest/tooling/test_export_backend_parity_handoff_manifest.py)
- docs handoff rule:
  - matrix publish target is `docs/ja|en/language/backend-parity-matrix.md`
  - docs entrypoints are `docs/ja|en/index.md` and `docs/ja|en/language/index.md`
  - docs are treated as publish targets for tooling manifests, not as an independently edited support-claim source
- release note rule:
  - release-note targets are `docs/ja/README.md`, `README.md`, `docs/ja/news/index.md`, and `docs/en/news/index.md`
  - release notes may summarize parity movement, but they link back to the matrix page instead of duplicating per-backend support tables
- tooling rule:
  - tooling publish targets are `export_backend_parity_matrix_manifest.py`, `export_backend_conformance_summary_handoff_manifest.py`, `export_backend_parity_review_manifest.py`, and `export_backend_parity_handoff_manifest.py`
  - the handoff manifest reuses the same matrix / conformance summary / review checklist / rollout-tier vocabulary

- 2026-03-12: `S3-01` fixes docs / release note / tooling handoff in `backend_parity_handoff_contract.py` and adds the matrix page plus docs entrypoints as canonical publish targets.

## S4-01 Archive / Operations Rule

- source of truth:
  - operations contract: [backend_parity_operations_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_operations_contract.py)
  - validation: [check_backend_parity_operations_contract.py](/workspace/Pytra/tools/check/check_backend_parity_operations_contract.py), [test_check_backend_parity_operations_contract.py](/workspace/Pytra/tools/unittest/tooling/test_check_backend_parity_operations_contract.py)
  - export seam: [export_backend_parity_operations_manifest.py](/workspace/Pytra/tools/gen/export_backend_parity_operations_manifest.py), [test_export_backend_parity_operations_manifest.py](/workspace/Pytra/tools/unittest/tooling/test_export_backend_parity_operations_manifest.py)
- operations rule:
  - maintenance order is `contract_seed -> docs_publish -> docs_entrypoints -> release_note_link -> tooling_export -> archive_handoff`
  - docs / README / news links to the parity matrix are checker-owned so publish-target drift fails closed
  - tooling export is anchored to `export_backend_parity_matrix_manifest.py` and `export_backend_parity_handoff_manifest.py`
- archive handoff rule:
  - when `P7` closes, hand off on the same day into `docs/ja|en/todo/archive/index.md` and `docs/ja|en/plans/archive/`
  - the live files that remain after archive handoff are the matrix page and the parity contract modules

- 2026-03-12: `S4-01` fixes the parity matrix maintenance order and archive handoff targets in `backend_parity_operations_contract.py`, and moves README / news / docs-index matrix links under checker control.
