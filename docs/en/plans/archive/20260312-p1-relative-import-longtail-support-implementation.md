<a href="../../../ja/plans/archive/20260312-p1-relative-import-longtail-support-implementation.md">
  <img alt="Read in Japanese" src="https://img.shields.io/badge/docs-日本語-DC2626?style=flat-square">
</a>

# P1: relative import long-tail support implementation

Last updated: 2026-03-12

Related TODO:
- `docs/ja/todo/index.md` item `ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01`

Background:
- C++ already satisfies the relative-import baseline through multi-file build/run smoke.
- `rs/cs/go/java/js/kotlin/nim/scala/swift/ts` already own a transpile-smoke baseline, and the final bundle moves `lua/php/ruby` onto the representative alias-rewrite lane at `transpile_smoke_locked + native_emitter_function_body_transpile`.
- The archived support-rollout plan fixed only the handoff and closed, so there is no live plan for the actual support implementation.
- The Pytra-NES experiment needs package-structured Python to move through the transpiler, so the staged relative-import rollout should be pulled forward.

Goal:
- Support the representative relative-import project for `lua/php/ruby` through a staged rollout.
- After Lua, make the PHP backend transpile `from .. import helper as h` / `from ..helper import f as g`, while keeping wildcard relative imports fail-closed.
- Sync backend coverage, parity docs, and support contracts to the current rollout state.

In scope:
- PHP native-emitter relative-import alias rewriting
- Staged-state updates for the relative-import support contract, backend coverage inventory, and parity docs
- PHP smoke, tooling checker, and backend-local contract updates for the success lane

Out of scope:
- wildcard relative-import support
- Ruby support implementation
- redesigning the C++/Rust/C# relative-import path

Acceptance criteria:
- The PHP backend successfully transpiles the two representative scenarios and rewrites `h.f()` / `g()` into emitted `helper_f()` PHP.
- The PHP backend still fail-closes `from ..helper import *` with `unsupported relative import form: wildcard import`.
- Sync the backend coverage inventory, parity docs, and long-tail handoff wording to the final state where `lua/php/ruby` all own representative `transpile_smoke_locked` coverage.
- The long-tail support contract, PHP support contract, and backend parity docs all record the current rollout state and the focused smoke lane correctly.

Verification commands:
- `python3 tools/check/check_relative_import_backend_coverage.py`
- `python3 tools/check/check_relative_import_longtail_support_contract.py`
- `python3 tools/check/check_relative_import_php_support_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_longtail_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_php_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/php -p 'test_py2php_smoke.py' -k relative_import`
- `python3 tools/build_selfhost.py`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: Keep the archived support-rollout plan as handoff history, and reopen the live implementation plan at the same `p1-relative-import-longtail-support.md` path.
- 2026-03-12: Limit the first implementation bundle to the Lua backend; keep PHP/Ruby as fail-closed residuals in the contract.
- 2026-03-12: Implement Lua support with the same relative-import alias rewriting strategy already used by Go/Nim/Swift, and lock the representative smoke on the direct native-emitter transpile lane.
- 2026-03-12: After the Lua bundle lands, record the current long-tail rollout as `mixed_rollout_locked`, with `lua` as the smoke-locked backend and `php/ruby` as the remaining fail-closed residuals.
- 2026-03-12: The first Pytra-NES blocker was parenthesized `from ... import (...)`, so land the frontend parser fix before the PHP/Ruby rollout bundles.
- 2026-03-12: Lock PHP support with the direct native-emitter rewrite strategy (`helper_f()`), while leaving wildcard relative imports fail-closed.
- 2026-03-12: After the PHP bundle lands, record the current long-tail rollout with `lua/php` as smoke-locked backends and `ruby` as the remaining fail-closed residual.
- 2026-03-12: Lock Ruby support with the same direct native-emitter rewrite strategy (`helper_f()`), still leaving wildcard relative imports fail-closed. The final state is `bundle_state=locked_representative_smoke`, `current_contract_state=transpile_smoke_locked`, `current_evidence_lane=native_emitter_function_body_transpile`, and `remaining_rollout_backends=none`.

## Breakdown

- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01] Advance the staged rollout for `lua/php/ruby` and sync the current relative-import support state into docs, tooling, and backend coverage.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S1-01] Reopen the active plan, TODO, and support handoff for the live implementation work.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S1-02] Let the frontend accept parenthesized `from ... import (...)` in relative-import projects.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-01] Add relative-import alias rewriting to the Lua native emitter and switch the representative smoke and contracts to the success lane.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-02] Extend the same representative scenarios to the PHP backend and update the contracts, smoke tests, and parity docs.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S2-03] Extend the same representative scenarios to the Ruby backend and update the contracts, smoke tests, and parity docs.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-IMPLEMENTATION-01-S3-01] Sync backend coverage, parity docs, and archived handoff wording to the final rollout state and close the task.
