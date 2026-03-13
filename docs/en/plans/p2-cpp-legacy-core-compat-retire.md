# P2: retire residual references to the deleted `src/runtime/cpp/core/**` compatibility surface

Last updated: 2026-03-13

Related TODO:
- `docs/ja/todo/index.md` `ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01`

Background:
- The current C++ runtime ownership split is `src/runtime/cpp/native/core/` plus `src/runtime/cpp/generated/core/`, and `src/runtime/cpp/core/` itself no longer exists.
- Even so, the live tree still contains residual references that can mislead readers into thinking the deleted `src/runtime/cpp/core/**` surface is still active.
- A representative example is [docs/ja/plans/p0-runtime-root-reset-cpp-parity.md](../../ja/plans/p0-runtime-root-reset-cpp-parity.md), which is completed yet still describes `src/runtime/cpp/core` plus `src/runtime/cpp/gen` as the canonical layout.
- In contrast, negative guards such as `tools/check_runtime_cpp_layout.py` and `test_runtime_symbol_index.py` still need to mention legacy `src/runtime/cpp/core/**` so they can fail fast if it reappears.

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
- `python3 tools/check_todo_priority.py`
- `rg -n "src/runtime/cpp/core|runtime/cpp/core/" src tools test docs -g '!**/archive/**'`
- `python3 tools/check_runtime_cpp_layout.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_runtime_cpp_layout.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_runtime_symbol_index.py'`
- `git diff --check`

## Breakdown

- [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S1-01] Inventory live-tree references to `src/runtime/cpp/core/**` and classify them as positive references versus guard-only references.
- [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S2-01] Archive or clean up stale-complete plans and live docs that still describe the old layout as canonical.
- [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S2-02] Normalize tooling and test wording so remaining `src/runtime/cpp/core/**` mentions are clearly guard-only.
- [ ] [ID: P2-CPP-LEGACY-CORE-COMPAT-RETIRE-01-S3-01] Sync checkers, unit tests, and mirrored docs to the current ownership contract and close the task.

Decision log:
- 2026-03-13: Opened as a closeout task on the assumption that `src/runtime/cpp/core/` is already deleted and only residual references need cleanup.
