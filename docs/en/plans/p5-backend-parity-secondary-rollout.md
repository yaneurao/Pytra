# P5 Backend Parity Secondary Rollout

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` entry `ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01`

Goal:
- Reintroduce a live rollout track that fills remaining unsupported support-matrix cells for the secondary tier (`go`, `java`, `kt`, `scala`, `swift`, `nim`).

Background:
- The secondary tier already exists in the matrix and rollout-tier contracts, but there is no active implementation queue for reducing unsupported cells.
- Once the representative tier advances, secondary backends need a ready-to-run rollout queue rather than another contract-only task.

In scope:
- Representative feature-cell implementation for secondary-tier backends.
- Adding `transpile_smoke`, `build_run_smoke`, or explicit `fail_closed` evidence.
- Syncing matrix/docs for the secondary tier.

Out of scope:
- Remaining representative-tier work.
- Long-tail backend rollout.
- Changing matrix schema or support-state taxonomy.

Acceptance criteria:
- The backend order and bundle order for the secondary tier are fixed.
- Each bundle carries backend-specific smoke or fail-closed evidence.
- The plan is ready to receive handoff immediately after representative-tier work is done.

Verification:
- `python3 tools/check_todo_priority.py`
- `python3 tools/check_backend_parity_matrix_contract.py`
- `python3 tools/check_backend_parity_secondary_rollout_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_matrix_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_secondary_rollout_inventory.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## Breakdown

- [x] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01-S1-01] Lock the current residual cells and backend order of the secondary tier as live rollout bundles.
- [x] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01-S2-01] Fill unsupported cells in the `go/java/kt` bundle with representative evidence.
- [x] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01-S2-02] Fill unsupported cells in the `scala/swift/nim` bundle with representative evidence.
- [ ] [ID: P5-BACKEND-PARITY-SECONDARY-ROLLOUT-01-S3-01] Sync secondary-tier matrix/docs/support wording to the current rollout state and close the task.

## Decision log

- 2026-03-12: The secondary tier is handled as two bundles, `go/java/kt` then `scala/swift/nim`, to keep each implementation batch large enough to matter.
- 2026-03-12: This remains a waiting task while higher-priority representative-tier work is unfinished.
- 2026-03-13: `S1-01` added `backend_parity_secondary_rollout_inventory.py`, its checker, and a unit test so the secondary residual cells are now fixed directly against the matrix seed. The bundle order is now concretely handed off as `go/java/kt` first and `scala/swift/nim` second; the first bundle captures the tuple/lambda/comprehension/iterator/std gaps, while the second bundle records that Scala/Swift still add `for_range/range` gaps and Nim swaps those for a `virtual_dispatch` gap.
- 2026-03-13: `S2-01` closed the `go/java/kt` bundle. The `go/java/kotlin` emitters now lower the `Swap` stmt used by `tuple_assign.py`, the secondary representative fixture bundle smoke locks transpile evidence for `tuple/lambda/comprehension/for_range/try_raise/enumerate/zip/isinstance/json/pathlib/enum/argparse/math/re`, and the matrix promotes the `go/java/kt` residual cells to `supported/transpile_smoke`. The secondary residual inventory now shrinks the first bundle into an empty completed marker and advances the next active bundle to `scala/swift/nim`.
- 2026-03-13: `S2-02` closed the `scala/swift/nim` bundle. Scala/Swift now carry representative transpile smoke for `for_range/range`, Nim carries the same bundle plus `virtual_dispatch` smoke and `Swap` lowering, and the matrix promotes the full secondary tier to `supported/transpile_smoke`. The secondary residual inventory is now empty and the handoff collapses to `completed_backends = full secondary tier`, `next_backend = None`, and `remaining_backends = ()`.
