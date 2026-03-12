# P4 Backend Parity Representative Rollout

Last updated: 2026-03-12

Related TODO:
- `docs/ja/todo/index.md` entry `ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01`

Goal:
- Restore a live rollout track that fills the remaining unsupported support-matrix cells for the representative tier (`cpp`, `rs`, `cs`) by implementation work.
- Separate actual backend implementation work from the already-archived matrix/contract maintenance tasks.

Background:
- The parity matrix and rollout tiers are already fixed in archived tasks, but the active TODO no longer has a queue for reducing `not_started` cells by implementation.
- The matrix can stay canonical while rollout still stalls if no live implementation queue exists.
- The representative tier (`cpp -> rs -> cs`) is the first rollout wave and should be tracked independently.

In scope:
- Implementation work for representative-tier cells still marked `not_started` or `fail_closed`.
- Focused regressions, matrix updates, and support wording updates for those cells.

Out of scope:
- Secondary and long-tail backend implementation.
- Redesigning matrix schema or rollout-tier contracts.
- Forcing all representative backends to become feature-complete at once.

Acceptance criteria:
- The remaining unsupported representative-tier cells have an explicit live rollout order and evidence lane.
- Each slice is tracked as `feature -> backend -> evidence`.
- After each implementation slice, matrix/docs/tooling are synced to the current state.
- Progress is recorded in this live plan rather than only in archived parity plans.

Verification:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_backend_parity_matrix_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_matrix_contract.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## Breakdown

- [x] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S1-01] Inventory the current `not_started` / `fail_closed` representative-tier cells and lock the live rollout order.
- [x] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-01] Raise remaining `cpp` representative cells to `build_run_smoke` or `transpile_smoke`.
- [ ] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-02] Raise remaining `rs` representative cells to at least `transpile_smoke`.
- [ ] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S2-03] Raise remaining `cs` representative cells to at least `transpile_smoke`.
- [ ] [ID: P4-BACKEND-PARITY-REPRESENTATIVE-ROLLOUT-01-S3-01] Sync representative-tier matrix/docs/support wording to the final rollout state and close the task.

## Locked Inventory / Rollout Order

- Source of truth: [backend_parity_representative_rollout_inventory.py](/workspace/Pytra/src/toolchain/compiler/backend_parity_representative_rollout_inventory.py)
- Checker: [check_backend_parity_representative_rollout_inventory.py](/workspace/Pytra/tools/check_backend_parity_representative_rollout_inventory.py)
- The current residual backends are `rs` and `cs` only; the `cpp` residual set is empty
- Fixed bundle order:
  - `cpp_locked_baseline`
  - `rs_syntax_iter_bundle`
  - `rs_stdlib_bundle`
  - `cs_syntax_iter_bundle`
  - `cs_stdlib_bundle`
- The current next backend is `rs`

## Decision log

- 2026-03-12: Because matrix/tier contracts are already archived, this plan focuses only on live implementation work that fills unsupported cells.
- 2026-03-12: The representative tier remains ordered as `cpp -> rs -> cs`, and every implementation slice must update the matrix state as part of completion.
- 2026-03-12: `S1-01` fixed the representative residual inventory in tooling, established that the current `cpp` residual set is empty, and narrowed the live implementation order to `rs -> cs`. Bundles stay split between syntax/iterator rows and stdlib rows so shared fixtures can move multiple cells at once.
- 2026-03-12: `S2-01` closes as a no-op because the `cpp_locked_baseline` bundle and the empty residual inventory already prove that the representative cpp lane is baseline-locked. The next backend remains `rs`.
