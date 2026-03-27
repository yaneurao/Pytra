<a href="../../../ja/plans/archive/20260312-p6-backend-parity-matrix-cell-fill.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P6: backend parity matrix cell fill

Last updated: 2026-03-12

Related TODO:
- `ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01` in `docs/en/todo/index.md`

Background:
- The current backend parity matrix already has a canonical publish target and a tooling contract.
- However, the matrix still only carries the row seed (`feature_id / category / representative_fixture / backend_order / support_state_order`) and does not yet populate each `feature × backend` cell with a support state.
- Meanwhile, C++ already has a detailed table in [spec-support.md](/workspace/Pytra/docs/en/language/cpp/spec-support.md), which makes the overall backend story look uneven.
- As a multi-backend compiler, Pytra needs the cross-backend 2D matrix to become the canonical source before any per-backend detailed table can be treated as sufficient.

Goal:
- Turn `docs/ja/language/backend-parity-matrix.md` and its English mirror into a real canonical matrix that carries `feature × backend` support states.
- Populate every cell with one of `supported / fail_closed / not_started / experimental` and export the evidence for that state from tooling manifests.
- Keep the C++ detailed matrix as a drill-down document, while moving the canonical truth to the cross-backend matrix.

In scope:
- adding a per-cell schema to the parity matrix contract
- preparing backend state seeds for every representative feature row
- exporting state evidence / fixture / diagnostic handoff data
- turning the docs publish target into a real table
- fixing the rollout order for filling the matrix from representative lanes first

Out of scope:
- achieving full feature parity across all backends at once
- removing per-backend detailed documentation
- redesigning the representative feature inventory from scratch
- redefining the support-state taxonomy

Acceptance criteria:
- the parity matrix contract has a per-cell state schema
- the docs publish target can emit a real `feature × backend` state table instead of just the row seed
- each cell can export at least `support_state` and `evidence_kind`
- the cross-backend matrix is explicitly documented as the canonical source, while the C++ matrix is treated as a drill-down
- `python3 tools/check_todo_priority.py` and parity-matrix tooling tests pass

Verification commands:
- `python3 tools/check_todo_priority.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_backend_parity_matrix*.py'`
- `python3 tools/export_backend_parity_matrix_manifest.py`
- `git diff --check`

Decision log:
- 2026-03-12: Lock the current matrix as a scaffold baseline rather than a fully populated per-cell support table.
- 2026-03-12: Treat the cross-backend matrix as the canonical source and per-language support tables as drill-down documentation.
- 2026-03-12: The initial cell schema requires `support_state` and `evidence_kind`, while richer details remain optional handoff data.
- 2026-03-12: `S1-01` fixed the `row_seed_scaffold` baseline in the matrix contract / manifest / docs publish target and fail-closed the current per-cell gap summary.
- 2026-03-12: `S2-01` fixed the per-cell schema as `backend/support_state/evidence_kind` required with `details/evidence_ref/diagnostic_kind` optional, and exported it at the top level of the manifest.
- 2026-03-12: `S2-02` added `backend_cells` seeds to representative rows and fixed the initial bundle as `cpp=supported/build_run_smoke` with the remaining backends on the conservative `not_started/not_started_placeholder` seed.
- 2026-03-12: `S3-01` published the seeded 2D table in the docs page and fixed the table block through contract-generated markdown plus begin/end markers.
- 2026-03-12: `S3-02` fixed the role split between the cross-backend matrix and the cpp-only support table, and locked the matrix-first maintenance order in docs/tooling contract form.
- 2026-03-12: `S4-01` added the rollout-tier fill order (`representative -> secondary -> long_tail`) to the matrix manifest and fixed the same order in the docs pages.
- 2026-03-12: `S4-02` promoted only the direct fixture-backed representative `rs/cs` cells from conservative seeds to `supported/transpile_smoke`, while secondary and long-tail lanes stay on placeholder seeds.
- 2026-03-12: `S4-03` promoted the direct-evidence secondary-tier cells and only raised the `go/java/kt/scala/swift/nim` lanes that already have representative fixture-backed smoke to `supported/transpile_smoke`.
- 2026-03-12: `S4-04` promoted only the long-tail `js/ts/lua/rb/php` cells that already have representative fixture-backed smoke, limiting the updates to `bitwise_invert_basic`, `inheritance_virtual_dispatch_multilang`, `for_range`, and `is_instance`.

## Breakdown

- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S1-01] Lock the current scaffold baseline and the gap in docs / contract / tooling.
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S2-01] Add a per-cell schema to the parity matrix contract and update manifest export.
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S2-02] Add backend cell seeds to representative feature rows so `support_state` / `evidence_kind` can be filled.
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S3-01] Materialize the docs publish target as a 2D table and explicitly document the cross-backend matrix as canonical.
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S3-02] Fix the role split with the C++ detailed table, drill-down links, and maintenance order in docs / tooling contracts.
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S4-01] Fix the rollout-tier fill order in the matrix manifest and docs.
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S4-02] Replace conservative seeds with reviewed representative-tier (`cpp/rs/cs`) cell states.
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S4-03] Promote direct-evidence secondary-tier (`go/java/kt/scala/swift/nim`) cells to reviewed states.
- [x] [ID: P6-BACKEND-PARITY-MATRIX-CELL-FILL-01-S4-04] Reflect reviewed / fail-closed long-tail (`js/ts/lua/rb/php`) cells in the matrix.
