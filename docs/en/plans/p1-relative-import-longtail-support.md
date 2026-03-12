# P1: relative import long-tail support implementation

Last updated: 2026-03-12

Related TODO:
- `docs/ja/todo/index.md` item `ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01`

Background:
- C++ already satisfies the relative-import baseline through multi-file build/run smoke.
- `rs/cs/go/java/js/kotlin/nim/scala/swift/ts` already own a transpile-smoke baseline, and `lua` has now moved its representative alias-rewrite lane to `transpile_smoke_locked + native_emitter_function_body_transpile`. `php/ruby` still remain on the archived long-tail `fail_closed_locked + backend_native_fail_closed` baseline.
- The archived support-rollout plan fixed only the handoff and closed, so there is no live plan for the actual support implementation.
- The Pytra-NES experiment needs package-structured Python to move through the transpiler, so the staged relative-import rollout should be pulled forward.

Goal:
- Support the representative relative-import project for `lua/php/ruby` through a staged rollout.
- Start by making the Lua backend transpile `from .. import helper as h` / `from ..helper import f as g`, while keeping wildcard relative imports fail-closed.
- Sync backend coverage, parity docs, and support contracts to the current rollout state.

In scope:
- Lua native-emitter relative-import alias rewriting
- Staged-state updates for the relative-import support contract, backend coverage inventory, and parity docs
- Lua smoke, tooling checker, and backend-local contract updates for the success lane

Out of scope:
- wildcard relative-import support
- PHP / Ruby support implementation
- redesigning the C++/Rust/C# relative-import path

Acceptance criteria:
- The Lua backend successfully transpiles the two representative scenarios and rewrites `h.f()` / `g()` into emitted `helper.f()`.
- The Lua backend still fail-closes `from ..helper import *` with `unsupported relative import form: wildcard import`.
- The backend coverage inventory moves `lua` to `transpile_smoke_locked + native_emitter_function_body_transpile` and keeps only `php/ruby` as the fail-closed residual.
- The long-tail support contract, Lua support contract, and backend parity docs all record the current rollout state and the focused smoke lane correctly.

Verification commands:
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/check_relative_import_longtail_support_contract.py`
- `python3 tools/check_relative_import_lua_support_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_longtail_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_lua_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/lua -p 'test_py2lua_smoke.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: Keep the archived support-rollout plan as handoff history, and reopen the live implementation plan at the same `p1-relative-import-longtail-support.md` path.
- 2026-03-12: Limit the first implementation bundle to the Lua backend; keep PHP/Ruby as fail-closed residuals in the contract.
- 2026-03-12: Implement Lua support with the same relative-import alias rewriting strategy already used by Go/Nim/Swift, and lock the representative smoke on the direct native-emitter transpile lane.
- 2026-03-12: After the Lua bundle lands, record the current long-tail rollout as `mixed_rollout_locked`, with `lua` as the smoke-locked backend and `php/ruby` as the remaining fail-closed residuals.

## Breakdown

- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01] Advance the staged rollout for `lua/php/ruby` and sync the current relative-import support state into docs, tooling, and backend coverage.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S1-01] Reopen the active plan, TODO, and support handoff for the live implementation work.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-01] Add relative-import alias rewriting to the Lua native emitter and switch the representative smoke and contracts to the success lane.
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-02] Extend the same representative scenarios to the PHP backend and update the contracts, smoke tests, and parity docs.
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-03] Extend the same representative scenarios to the Ruby backend and update the contracts, smoke tests, and parity docs.
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S3-01] Sync backend coverage, parity docs, and archived handoff wording to the final rollout state and close the task.
