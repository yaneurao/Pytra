# P2: Relative-Import Non-C++ Rollout Staging

Last updated: 2026-03-12

Related TODO:
- `ID: P2-RELATIVE-IMPORT-NONCPP-ROLLOUT-01` in `docs/ja/todo/index.md`

Background:
- The current relative-import coverage baseline is already locked as `cpp=build_run_locked` and `not_locked` everywhere else.
- However, the next rollout order for non-C++ backends is still not fixed as a live plan: the project has not yet stated which targets belong to the first wave, what counts as their representative verification lane, or how unsupported lanes stay fail-closed while rollout is still in progress.
- To expand support without widening support claims prematurely, the rollout order and verification shape need to be fixed first.

Goal:
- Fix the non-C++ relative-import rollout order as first wave / second wave / long-tail.
- Decide the representative smoke or fail-closed lane that should be added next for the first-wave backends.

Scope:
- Decide the non-C++ backend rollout order
- Decide the first-wave backends and their representative verification lanes
- Document the fail-closed handoff policy

Out of scope:
- Implementing relative imports for Rust / C# / other backends
- Expanding support claims in the support matrix
- Changing import graph / CLI semantics

Acceptance criteria:
- The first-wave / second-wave / long-tail backend groups are documented.
- The first-wave backends have an explicit next verification lane: `transpile smoke` and/or `backend-specific fail_closed`.
- The next rollout task can attach without disturbing the current `cpp=build_run_locked` baseline.

Verification commands:
- `python3 tools/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: After the current coverage baseline was closed, the next step was defined as a staged non-C++ rollout plan rather than an immediate implementation push.
- 2026-03-12: The rollout order was fixed as `first wave=rs/cs`, `second wave=go/java/js/kotlin/scala/swift/nim/ts`, and `long-tail=lua/php/ruby`.
- 2026-03-12: The first wave was fixed to `rs/cs` with `transpile_smoke` as the next verification lane, while every non-C++ backend keeps `backend_specific_fail_closed` until support claims widen.

## Breakdown

- [x] [ID: P2-RELATIVE-IMPORT-NONCPP-ROLLOUT-01-S1-01] Create the live plan / TODO and fix the first-wave / second-wave / long-tail rollout order.
- [x] [ID: P2-RELATIVE-IMPORT-NONCPP-ROLLOUT-01-S2-01] Fix the representative verification lane for first-wave backends across `transpile smoke` and `fail_closed`.
- [ ] [ID: P2-RELATIVE-IMPORT-NONCPP-ROLLOUT-01-S2-02] Sync links from the current coverage inventory / backend-parity docs into the next rollout handoff.
