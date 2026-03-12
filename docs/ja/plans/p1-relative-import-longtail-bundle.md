# P1: relative import long-tail bundle rollout

最終更新: 2026-03-12

関連 TODO:
- `docs/ja/todo/index.md` の `ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01`

背景:
- `locked_js_ts_smoke_bundle -> native_path_bundle(go/nim/swift) -> jvm_package_bundle(java/kotlin/scala)` の second-wave rollout は archive 済み。
- current coverage baseline では `rs/cs/go/java/js/kotlin/nim/scala/swift/ts` が `transpile_smoke_locked` に固定され、残る未検証 backend は `lua/php/ruby` だけになった。
- backend coverage / second-wave handoff / backend parity docs は、次の live rollout を `lua/php/ruby` long-tail bundle として指す必要がある。

目的:
- `lua/php/ruby` を next live rollout bundle として固定する。
- long-tail representative scenario、verification lane、fail-closed lane を docs / tooling / contract に同期する。

対象:
- long-tail bundle の live plan / TODO / contract / checker / test 追加
- JVM package bundle contract の archive semantics 化
- backend coverage / second-wave handoff / backend parity docs の next rollout handoff 更新

非対象:
- Lua / PHP / Ruby backend の full support claim
- relative import semantics 自体の変更
- long-tail representative smoke 実装以外の backend 機能拡張

受け入れ基準:
- next live handoff はこの plan を参照し、`lua/php/ruby` を `longtail_relative_import_rollout` lane として固定する。
- `java/kotlin/scala` は archived JVM bundle として `transpile_smoke_locked` baseline に移る。
- backend coverage / second-wave contract / backend parity docs の active handoff が deleted JVM live plan を参照しない。
- `python3 tools/check_relative_import_*contract.py` と対応 unit test が通る。

確認コマンド:
- `python3 tools/check_relative_import_backend_coverage.py`
- `python3 tools/check_relative_import_secondwave_rollout_contract.py`
- `python3 tools/check_relative_import_jvm_package_bundle_contract.py`
- `python3 tools/check_relative_import_longtail_bundle_contract.py`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_backend_coverage.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_secondwave_rollout_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_jvm_package_bundle_contract.py'`
- `PYTHONPATH=src python3 -m unittest discover -s test/unit/tooling -p 'test_check_relative_import_longtail_bundle_contract.py'`
- `python3 tools/check_todo_priority.py`
- `git diff --check`

決定ログ:
- 2026-03-12: JVM package bundle は representative smoke を lock した archived bundle とみなし、follow-up live rollout は `lua/php/ruby` long-tail bundle へ移す。
- 2026-03-12: long-tail bundle の active lane は `longtail_relative_import_rollout`、fail-closed lane は `backend_specific_fail_closed` に固定する。
- 2026-03-12: second-wave bundle order は historical contract として残しつつ、next live rollout handoff は long-tail bundle に更新する。

## 分解

- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01] `lua/php/ruby` long-tail bundle の live handoff と representative rollout contract を固定する。
- [x] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S1-01] long-tail bundle の live plan / TODO / contract / checker / docs handoff を追加し、JVM bundle contract を archive semantics に切り替える。
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S2-01] `lua/php/ruby` の representative transpile smoke / fail-closed regression を追加する。
- [ ] [ID: P1-RELATIVE-IMPORT-LONGTAIL-BUNDLE-01-S2-02] backend parity docs / coverage inventory / handoff wording を long-tail current state に同期して close-ready にする。
