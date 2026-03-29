<a href="../../../ja/plans/archive/20260314-p2-cpp-legacy-core-compat-retire.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P2: retire residual references to the deleted `src/runtime/cpp/core/**` compatibility surface

Last updated: 2026-03-14

Related TODO:
- `docs/ja/todo/index.md` `ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01`

Background:
- The current C++ runtime ownership split is `src/runtime/cpp/native/core/` plus `src/runtime/cpp/generated/core/`, and `src/runtime/cpp/core/` itself no longer exists.
- Even so, the live tree still contains residual references that can mislead readers into thinking the deleted `src/runtime/cpp/core/**` surface is still active.
- A representative stale example is [docs/ja/plans/archive/20260306-p0-runtime-root-reset-cpp-parity.md](../../ja/plans/archive/20260306-p0-runtime-root-reset-cpp-parity.md), which stayed under live `plans/` even though it was complete and still described `src/runtime/cpp/core` plus `src/runtime/cpp/gen` as the canonical layout.
- In contrast, negative guards such as `tools/check/check_runtime_cpp_layout.py` and `test_runtime_symbol_index.py` still need to mention legacy `src/runtime/cpp/core/**` so they can fail fast if it reappears.

Objective:
- Remove the deleted `src/runtime/cpp/core/**` surface from all live docs, tooling, and tests that still treat it as an active layout.
- Limit legacy-path mentions to guard-only references that clearly mean "this must not reappear."

In scope:
- Inventorying positive references to `src/runtime/cpp/core/**` in live plans, specs, tooling, and tests
- Archiving or cleaning up stale-complete live plans
- Classifying which `src/runtime/cpp/core/**` references must remain as guard-only wording and normalizing that wording
- Syncing TODO, plan, and the English mirror

Out of scope:
- Redesigning ownership for `src/runtime/cpp/native/core/**` or `generated/core/**`
- Full cleanup of the `runtime2` parked tree
- Functional changes to the C++ runtime implementation itself

Acceptance criteria:
- No live-tree text still describes `src/runtime/cpp/core/**` as a canonical or present surface.
- Remaining references to legacy `src/runtime/cpp/core/**` are limited to necessary guards and negative assertions.
- Stale-complete plans are no longer easy to mistake for active live plans.
- Related checker behavior, unit tests, and docs wording are synchronized to the current ownership contract.

Validation commands (planned):
- `python3 tools/check/check_todo_priority.py`
- `rg -n "src/runtime/cpp/core|runtime/cpp/core/" src tools test docs -g '!**/archive/**'`
- `python3 tools/check/check_runtime_cpp_layout.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_runtime_cpp_layout.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_runtime_symbol_index.py'`
- `git diff --check`

## Breakdown

- [x] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S1-01] Inventoried live-tree references to `src/runtime/cpp/core/**` and classified them as positive references versus guard-only references.
- [x] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S2-01] Archived the stale-complete plan and cleaned up live docs that still described the old layout as canonical.
- [x] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S2-02] Revalidated tooling and test wording so the remaining `src/runtime/cpp/core/**` mentions are clearly guard-only.
- [x] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S3-01] Synced checkers, unit tests, and mirrored docs to the current ownership contract and closed the task.

Decision log:
- 2026-03-13: Opened as a closeout task on the assumption that `src/runtime/cpp/core/` is already deleted and only residual references need cleanup.
- 2026-03-14: Confirmed that the only positive live-tree reference was the stale-complete `p0-runtime-root-reset-cpp-parity.md`, then moved it to `docs/ja/plans/archive/20260306-p0-runtime-root-reset-cpp-parity.md` and rewired the historical links in `todo/archive/20260306.md` and the archive indexes to the archived path.
- 2026-03-14: Normalized the checked-in `test/transpile/cpp/**` snapshots from legacy `runtime/cpp/core/**` include/source paths to `runtime/cpp/native/core/**`, removing the remaining positive fixture references to the deleted layout.
- 2026-03-14: Confirmed that the remaining hits from `rg -n "src/runtime/cpp/core|runtime/cpp/core/" src tools test docs -g '!**/archive/**'` are limited to guard-only wording in `check_runtime_cpp_layout.py`, `check_runtime_core_gen_markers.py`, the runtime specs, and negative-assertion tests.
