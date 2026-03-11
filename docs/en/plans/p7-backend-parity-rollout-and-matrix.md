# P7 Backend Parity Rollout And Matrix

Last updated: 2026-03-12

Purpose:
- Make backend parity visible as feature × backend status so the project can continuously track which backends are `supported`, `fail_closed`, or `not_started`.
- Build parity requirements into new-feature merge policy so C++-only completion is no longer treated as feature completion.
- Institutionalize the support matrix and rollout order in docs, tooling, and review operations.

Background:
- Even with `P5` contract work and `P6` conformance groundwork, C++-first drift will return unless the workflow itself changes.
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

- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S1-01] Decide the source of truth and publication path for the feature × backend support matrix.
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-01] Fix rollout tiers and ordering from representative backends to secondary and long-tail backends.
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S2-02] Define the parity review checklist and fail-closed requirement for new feature merges.
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S3-01] Define how the support matrix flows into docs, release notes, and tooling.
- [ ] [ID: P7-BACKEND-PARITY-ROLLOUT-MATRIX-01-S4-01] Fix the archive / operations rules for maintaining rollout policy and the support matrix.

## Decision log

- 2026-03-12: The operationalization of parity is placed at `P7` because it should follow the contract and conformance layers instead of pretending to define them.
- 2026-03-12: Backend parity means “make support states visible and keep unsupported lanes fail-closed,” not “implement every backend simultaneously.”
