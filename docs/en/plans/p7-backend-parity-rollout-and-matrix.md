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
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-01] Fix rollout tiers and ordering from representative backends to secondary and long-tail backends.
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-02] Define the parity review checklist and fail-closed requirement for new feature merges.
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S3-01] Define how the support matrix flows into docs, release notes, and tooling.
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S4-01] Fix the archive / operations rules for maintaining rollout policy and the support matrix.

## Decision log

- 2026-03-12: The operationalization of parity is placed at `P7` because it should follow the contract and conformance layers instead of pretending to define them.
- 2026-03-12: Backend parity means “make support states visible and keep unsupported lanes fail-closed,” not “implement every backend simultaneously.”
- 2026-03-12: `P7` consumes `backend_feature_contract_inventory.build_feature_contract_handoff_manifest()["support_matrix_handoff"]` and `support_state_order` as the canonical matrix seed.

## S1-01 Matrix Source Of Truth And Publish Path

- source of truth:
  - matrix contract: [backend_parity_matrix_contract.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_matrix_contract.py)
  - CLI/export seam: [export_backend_parity_matrix_manifest.py](/workspace/Pytra/tools/export_backend_parity_matrix_manifest.py)
  - validation: [check_backend_parity_matrix_contract.py](/workspace/Pytra/tools/check_backend_parity_matrix_contract.py), [test_check_backend_parity_matrix_contract.py](/workspace/Pytra/test/unit/tooling/test_check_backend_parity_matrix_contract.py)
- source manifest rule:
  - `feature_contract_seed`: `backend_feature_contract_inventory.build_feature_contract_handoff_manifest`
  - `conformance_summary_seed`: `backend_conformance_summary_handoff.build_backend_conformance_summary_handoff_manifest`
  - the canonical matrix destination is fixed to `support_matrix`.
- row/source rule:
  - row seed comes directly from `iter_representative_support_matrix_handoff()` and keeps `feature_id/category/representative_fixture/backend_order/support_state_order` as the row keys.
  - summary seed is reused directly from the P6 `support_matrix` handoff (`feature_contract_handoff.support_matrix_handoff`), so the matrix does not invent a second vocabulary.
- publish path rule:
  - Japanese docs publish path: `docs/ja/language/backend-parity-matrix.md`
  - English docs publish path: `docs/en/language/backend-parity-matrix.md`
  - tooling publish seam: `tools/export_backend_parity_matrix_manifest.py`
- downstream rule:
  - downstream task / plan stay fixed to `P7-BACKEND-PARITY-ROLLOUT-MATRIX-01` and `docs/ja/plans/p7-backend-parity-rollout-and-matrix.md`.

- 2026-03-12: `S1-01` adds `backend_parity_matrix_contract.py`, fixes the support-matrix row seed to P5, the summary seed to P6, and the publish path to `docs/ja|en/language/backend-parity-matrix.md` plus the tooling manifest export.
