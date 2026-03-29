<a href="../../../en/plans/archive/20260312-p1-relative-import-longtail-support.md">
  <img alt="Read in English" src="https://img.shields.io/badge/docs-English-2563EB?style=flat-square">
</a>

# P1: relative import long-tail support rollout

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01`

背景:
- archived long-tail bundle により、`lua/php/ruby` の representative relative import project は `fail_closed_locked + backend_native_fail_closed` baseline として固定された。
- backend coverage inventory / second-wave handoff / backend parity docs は、次の active rollout を `longtail_relative_import_support_rollout` として指し始めている。
- しかし support rollout 自体の live plan / contract / checker がまだ無く、active handoff の正本が欠けている。

目的:
- archived fail-closed baseline を維持したまま、`lua/php/ruby` relative import support rollout の active handoff を固定する。
- representative scenario / current baseline / follow-up なしの live rollout 契約を docs / tooling / contract に同期する。

対象:
- support rollout の live plan / TODO / contract / checker / unit test 追加
- archived long-tail fail-closed bundle から support rollout への handoff 固定
- second-wave handoff / backend coverage / backend parity docs の active plan path 同期

非対象:
- Lua / PHP / Ruby backend の relative import support 実装
- relative import semantics 自体の変更
- full support claim の追加

受け入れ基準:
- active handoff は `docs/ja/plans/archive/20260312-p1-relative-import-longtail-support-implementation.md` を参照し、`lua/php/ruby` を `longtail_relative_import_support_rollout` に固定する。
- archived long-tail fail-closed bundle checker は support rollout を follow-up として参照し、support contract checker は archived baseline を prereq として参照する。
- backend coverage / second-wave handoff / backend parity docs が deleted live long-tail bundle plan を参照しない。
- `python3 tools/check/check_relative_import_*contract.py` と対応 unit test が通る。

確認コマンド:
- `python3 tools/check/check_relative_import_backend_coverage.py`
- `python3 tools/check/check_relative_import_secondwave_rollout_contract.py`
- `python3 tools/check/check_relative_import_longtail_bundle_contract.py`
- `python3 tools/check/check_relative_import_longtail_support_contract.py`
- `python3 tools/check/check_relative_import_lua_support_contract.py`
- `python3 tools/check/check_relative_import_php_support_contract.py`
- `python3 tools/check/check_relative_import_ruby_support_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_longtail_bundle_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_longtail_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_lua_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_php_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/tooling -p 'test_check_relative_import_ruby_support_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s tools/unittest/emit/lua -p 'test_py2lua_smoke.py' -k relative_import_support_rollout`
- `PYTHONPATH=src:test/unit python3 tools/unittest/emit/php/test_py2php_smoke.py -k relative_import_support_rollout -v`
- `PYTHONPATH=src:test/unit:tools/unittest/backends python3 -m unittest discover -s tools/unittest/emit/rb -p 'test_py2rb_smoke.py' -k relative_import_support_rollout`
- `python3 tools/check/check_todo_priority.py`
- `git diff --check`

決定ログ:
- 2026-03-12: archived long-tail bundle は `fail_closed_locked + backend_native_fail_closed` baseline の履歴として固定し、active work は support rollout 側へ移す。
- 2026-03-12: support rollout は `bundle_state=active_rollout`、`verification_lane=longtail_relative_import_support_rollout`、`followup_bundle_id=none` を canonical とする。
- 2026-03-12: `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S1-01` は live plan / TODO / support contract / checker と archive handoff を一緒に揃える closeout-first bundle とする。
- 2026-03-12: `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-01` では Lua backend の focused verification lane を `lua_relative_import_support_rollout_smoke` とし、current diagnostic family は `backend_specific_fail_closed`、current evidence は `backend_native_fail_closed` のまま固定する。
- 2026-03-12: `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-02` では PHP backend の focused verification lane を `php_relative_import_support_rollout_smoke` とし、Lua と同じく backend-local contract/checker で smoke 名と diagnostic marker を固定する。
- 2026-03-12: `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-03` では Ruby backend の focused verification lane を `ruby_relative_import_support_rollout_smoke` とし、Lua/PHP と同じく backend-local contract/checker で smoke 名と diagnostic marker を固定する。
- 2026-03-12: `P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S3-01` では backend coverage / parity docs / active handoff wording に `lua/php/ruby` focused lane 名まで明記し、parent task を close する。

## 分解

- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01] archived fail-closed baseline を維持したまま、`lua/php/ruby` relative import support rollout の active handoff と representative contract を固定した。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S1-01] archived long-tail fail-closed bundle を archive へ移し、support rollout の live plan / TODO / contract / checker / handoff を追加した。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-01] Lua backend の representative support rollout contract と focused verification lane を固定する。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-02] PHP backend の representative support rollout contract と focused verification lane を fixed inventory / checker / smoke で固定した。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S2-03] Ruby backend の representative support rollout contract と focused verification lane を fixed inventory / checker / smoke で固定した。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-SUPPORT-01-S3-01] backend parity docs / coverage inventory / active handoff wording を current support rollout state に同期して task を閉じた。
