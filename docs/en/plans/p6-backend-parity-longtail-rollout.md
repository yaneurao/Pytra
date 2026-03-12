# P6 Backend Parity Long-Tail Rollout

Last updated: 2026-03-12

Related TODO:
- `docs/ja/todo/index.md` entry `ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01`

Goal:
- Keep a live implementation queue for the long-tail tier (`js`, `ts`, `lua`, `rb`, `php`) so that unsupported support-matrix cells can actually be reduced after higher tiers move forward.

Background:
- The long-tail tier still exists in the matrix, but there is no active TODO that turns unsupported cells into implementation work.
- Without a live queue, parity rollout stops at matrix maintenance even when rollout policy is already defined.

In scope:
- Representative feature-cell implementation for long-tail backends.
- Preserving fail-closed behavior for unsupported lanes while upgrading supported lanes with evidence.
- Matrix/docs/support wording updates for the long-tail tier.

Out of scope:
- Representative or secondary-tier parity completion.
- Full feature parity across JS/TS/Lua/Ruby/PHP.
- Redesigning parity-matrix contracts.

Acceptance criteria:
- The long-tail backend order and rollout bundles are explicitly fixed.
- Unsupported lanes stay fail-closed, while supported lanes move only with concrete evidence.
- The plan is ready for direct handoff after secondary-tier work completes.

Verification:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_backend_parity_matrix_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_matrix_contract.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## Breakdown

- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S1-01] Lock the current residual cells and implementation bundles for the long-tail tier.
- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S2-01] Fill unsupported cells in the `js/ts` bundle with representative evidence.
- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S2-02] Fill unsupported cells in the `lua/rb/php` bundle with representative evidence.
- [ ] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S3-01] Sync long-tail matrix/docs/support wording to the current rollout state and close the task.

## Decision log

- 2026-03-12: The long-tail tier is split into `js/ts` and `lua/rb/php` bundles so the rollout can track real evidence batches instead of singleton tasks.
- 2026-03-12: Unsupported lanes remain fail-closed; only lanes with actual evidence move to a supported state.
