# P1: relative import long-tail support rollout

Last updated: 2026-03-12

Related TODO:
- `ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01` in `docs/en/todo/index.md`

Background:
- The archived long-tail bundle now fixes the representative relative-import project for `lua/php/ruby` as a `fail_closed_locked + backend_native_fail_closed` baseline.
- The backend coverage inventory, second-wave handoff, and backend-parity docs already started pointing at `longtail_relative_import_support_rollout` as the next active rollout.
- However, the support rollout still lacks its own live plan / contract / checker, so the active handoff has no dedicated source of truth.

Goal:
- Keep the archived fail-closed baseline intact while fixing the active handoff for the `lua/php/ruby` relative-import support rollout.
- Align the representative scenarios, current baseline, and no-follow-up live rollout contract across docs, tooling, and contracts.

Scope:
- Add the live support rollout plan / TODO / contract / checker / unit tests
- Lock the handoff from the archived long-tail fail-closed bundle into the support rollout
- Sync the second-wave handoff, backend coverage inventory, and backend-parity docs to the active plan path

Out of scope:
- Implementing relative-import support for Lua / PHP / Ruby backends
- Changing relative-import semantics
- Adding full support claims

Acceptance criteria:
- The active handoff points to `docs/en/plans/p1-relative-import-longtail-support.md` and fixes `lua/php/ruby` on `longtail_relative_import_support_rollout`.
- The archived long-tail fail-closed bundle checker references the support rollout as its follow-up, and the support-rollout checker references the archived baseline as its prerequisite.
- Backend coverage / second-wave handoff / backend-parity docs no longer reference the deleted live long-tail bundle plan.
- `python3 tools/check_relative_import_*contract.py` and the matching unit tests pass.

Verification commands:
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/check_relative_import_secondwave_rollout_contract.py`
- `python3 tools/check_relative_import_longtail_bundle_contract.py`
- `python3 tools/check_relative_import_longtail_support_contract.py`
- `python3 tools/check_relative_import_lua_support_contract.py`
- `python3 tools/check_relative_import_php_support_contract.py`
- `python3 tools/check_relative_import_ruby_support_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_longtail_bundle_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_longtail_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_lua_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_php_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_ruby_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/backends/lua -p 'test_py2lua_smoke.py' -k relative_import_support_rollout`
- `PYTHONPATH=src:test/unit python3 test/unit/backends/php/test_py2php_smoke.py -k relative_import_support_rollout -v`
- `PYTHONPATH=src:test/unit:test/unit/backends python3 -m unittest discover -s test/unit/backends/rb -p 'test_py2rb_smoke.py' -k relative_import_support_rollout`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

Decision log:
- 2026-03-12: The archived long-tail bundle remains the `fail_closed_locked + backend_native_fail_closed` baseline, and only the active work moves into the support rollout.
- 2026-03-12: The support rollout canonically uses `bundle_state=active_rollout`, `verification_lane=longtail_relative_import_support_rollout`, and `followup_bundle_id=none`.
- 2026-03-12: `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S1-01` is the closeout-first bundle that aligns the live plan / TODO / support contract / checker and the archive handoff together.
- 2026-03-12: `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-01` fixes the Lua-focused verification lane as `lua_relative_import_support_rollout_smoke`, while the current diagnostic family stays `backend_specific_fail_closed` and the current evidence lane stays `backend_native_fail_closed`.
- 2026-03-12: `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-02` fixes the PHP-focused verification lane as `php_relative_import_support_rollout_smoke` and locks the smoke ids plus diagnostic markers in a backend-local contract/checker.
- 2026-03-12: `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-03` fixes the Ruby-focused verification lane as `ruby_relative_import_support_rollout_smoke` and locks the smoke ids plus diagnostic markers in a backend-local contract/checker.

## Breakdown

- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01] Fix the active handoff and representative contract for the `lua/php/ruby` relative-import support rollout while keeping the archived fail-closed baseline.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S1-01] Archive the long-tail fail-closed bundle and add the live support rollout plan / TODO / contract / checker / handoff.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-01] Fix the representative support-rollout contract and focused verification lane for the Lua backend.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-02] Lock the representative support-rollout contract and focused verification lane for the PHP backend with inventory / checker / smoke coverage.
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-03] Lock the representative support-rollout contract and focused verification lane for the Ruby backend with inventory / checker / smoke coverage.
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S3-01] Sync backend-parity docs / coverage inventory / active handoff wording to the current support-rollout state and close the task.
