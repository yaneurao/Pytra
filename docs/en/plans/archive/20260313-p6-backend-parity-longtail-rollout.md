<a href="../../../ja/plans/archive/20260313-p6-backend-parity-longtail-rollout.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P6 Backend Parity Long-Tail Rollout

Last updated: 2026-03-13

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
- `python3 tools/check/check_todo_priority.py`
- `python3 tools/check/check_backend_parity_matrix_contract.py`
- `python3 tools/check/check_backend_parity_longtail_rollout_inventory.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_backend_parity_matrix_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_backend_parity_longtail_rollout_inventory.py'`
- `python3 tools/build_selfhost.py`
- `git diff --check`

## Breakdown

- [x] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S1-01] Lock the current residual cells and implementation bundles for the long-tail tier.
- [x] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S2-01] Fill unsupported cells in the `js/ts` bundle with representative evidence.
- [x] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S2-02] Fill unsupported cells in the `lua/rb/php` bundle with representative evidence.
- [x] [ID: P6-BACKEND-PARITY-LONGTAIL-ROLLOUT-01-S3-01] Sync long-tail matrix/docs/support wording to the current rollout state and close the task.

## Decision log

- 2026-03-12: The long-tail tier is split into `js/ts` and `lua/rb/php` bundles so the rollout can track real evidence batches instead of singleton tasks.
- 2026-03-12: Unsupported lanes remain fail-closed; only lanes with actual evidence move to a supported state.
- 2026-03-13: `S1-01` added `backend_parity_longtail_rollout_inventory.py`, its checker, and a unit test so the long-tail residual cells are now fixed directly against the matrix seed. The bundle order is now concretely handed off as `js/ts` first and `lua/rb/php` second; `js` keeps the tuple/lambda/comprehension/control/iterator/std gaps, `ts` adds `virtual_dispatch`, `lua/php` keep the lighter syntax + enumerate + std gaps, and `rb` additionally keeps `for_range/range/zip`.
- 2026-03-13: `S2-01` added `Swap` lowering to the `js` emitter and confirmed the full `js/ts` representative bundle, including `tuple_destructure`, via targeted smoke. The matrix now promotes the `js` tuple/lambda/comprehension/control/iterator/std bundle and the matching `ts` bundle plus `virtual_dispatch` to `supported/transpile_smoke`, and the long-tail handoff advances to `completed_backends = ("js", "ts")`, `next_backend = "lua"`, and `next_bundle = "lua_rb_php_bundle"`.
- 2026-03-13: `S2-02` closed the `lua/rb/php` bundle. `Swap` lowering now exists in the `lua/rb/php` emitters, and Lua also gained lambda rendering plus runtime alias shims for `enum/argparse/re` so the representative smoke bundle passes. The matrix promotes the remaining `lua/rb/php` residual cells to `supported/transpile_smoke`, and the long-tail residual inventory collapses to `completed_backends = ("js", "ts", "lua", "rb", "php")`, `next_backend = None`, and `next_bundle = None`.
- 2026-03-13: `S3-01` synced the long-tail matrix table, inventory wording, and TODO to the closed state. The end state is an empty long-tail residual inventory, reviewed representative cells for `js/ts/lua/rb/php` all at `supported/transpile_smoke`, and only archive migration remains before the active queue can drop the task.
